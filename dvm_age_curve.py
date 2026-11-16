
import pandas as pd

# ==========================================
# DIAMOND VALUE MODEL (DVM)
# Age-Adjusted WAR Projection - v0.4
# ==========================================

INPUT_FILE = "dvm_2025_LAD_with_ages.csv"
OUTPUT_FILE = "dvm_2025_LAD_age_projections.csv"

BASE_SEASON = 2025
PEAK_AGE = 27
VALUE_PER_WAR = 8_000_000

# Prototype assumptions, not trained estimates.
ANNUAL_GROWTH = 0.03
ANNUAL_DECLINE = 0.04
PROJECTION_YEARS = 3


def age_multiplier(age):
    """Illustrative annual change based on projected age."""

    if age < PEAK_AGE:
        return 1 + ANNUAL_GROWTH

    if age == PEAK_AGE:
        return 1.0

    return 1 - ANNUAL_DECLINE


def main():

    print("=" * 50)
    print("DIAMOND VALUE MODEL")
    print("Age-Adjusted WAR Projection - v0.4")
    print("=" * 50)

    df = pd.read_csv(INPUT_FILE)

    required = [
        "MLBAM_ID",
        "Name",
        "Age",
        "Total_bWAR"
    ]

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if df.duplicated(["MLBAM_ID"]).any():
        raise ValueError("Duplicate player IDs found")

    df["Age"] = pd.to_numeric(
        df["Age"], errors="coerce"
    )

    df["Total_bWAR"] = pd.to_numeric(
        df["Total_bWAR"], errors="coerce"
    )

    projections = []

    for _, player in df.iterrows():

        if pd.isna(player["Age"]) or pd.isna(
            player["Total_bWAR"]
        ):
            continue

        player_id = int(player["MLBAM_ID"])
        name = player["Name"]

        starting_age = int(player["Age"])
        historical_war = float(player["Total_bWAR"])

        # Prototype baseline:
        # Negative historical WAR becomes zero.
        # This is not a statistically calibrated forecast.
        projected_war = max(historical_war, 0.0)

        for year_ahead in range(
            1, PROJECTION_YEARS + 1
        ):

            projection_year = BASE_SEASON + year_ahead
            projected_age = starting_age + year_ahead

            multiplier = age_multiplier(
                projected_age
            )

            projected_war *= multiplier

            market_value = (
                projected_war * VALUE_PER_WAR
            )

            projections.append({
                "MLBAM_ID": player_id,
                "Name": name,
                "Base_Season": BASE_SEASON,
                "Historical_bWAR": historical_war,
                "Age_2025": starting_age,
                "Projection_Year": projection_year,
                "Projected_Age": projected_age,
                "Age_Multiplier": multiplier,
                "Projected_bWAR": round(
                    projected_war, 3
                ),
                "Projected_Market_Value": round(
                    market_value, 2
                ),
                "Model_Type": "Illustrative Age Curve"
            })

    result = pd.DataFrame(projections)

    if result.empty:
        raise ValueError(
            "No projections generated. "
            "Check player age and WAR data."
        )

    result = result.sort_values(
        ["Name", "Projection_Year"]
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nPROJECTION RESULTS")
    print("-" * 50)

    print(
        "Players projected:",
        result["MLBAM_ID"].nunique()
    )

    print(
        "Projection years:",
        f"{BASE_SEASON + 1}-{BASE_SEASON + PROJECTION_YEARS}"
    )

    print(
        "Total projection records:",
        len(result)
    )

    print("\nTop 10 projected players for 2026:")

    top = result[
        result["Projection_Year"] == 2026
    ].nlargest(
        10, "Projected_bWAR"
    )

    print(
        top[
            [
                "Name",
                "Projected_Age",
                "Projected_bWAR"
            ]
        ].to_string(index=False)
    )

    print("\nSaved:", OUTPUT_FILE)
    print("Age projection completed successfully!")


if __name__ == "__main__":
    main()
