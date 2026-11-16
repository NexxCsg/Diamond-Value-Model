
import pandas as pd
import numpy as np
from pybaseball import bwar_bat, bwar_pitch

# ==========================================
# DIAMOND VALUE MODEL (DVM)
# 2026 Projection Backtest - v0.4
# ==========================================

PROJECTIONS_FILE = "dvm_2025_LAD_age_projections.csv"
OUTPUT_FILE = "dvm_2026_backtest.csv"

SEASON = 2026
VALUE_PER_WAR = 8_000_000


def prepare_war(data, war_type):
    required = ["mlb_ID", "year_ID", "WAR"]

    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(
            f"Missing {war_type} columns: {missing}"
        )

    data = data[data["year_ID"] == SEASON].copy()

    data["MLBAM_ID"] = pd.to_numeric(
        data["mlb_ID"], errors="coerce"
    )

    data["WAR"] = pd.to_numeric(
        data["WAR"], errors="coerce"
    )

    data = data.dropna(subset=["MLBAM_ID", "WAR"])

    # Sum across teams/stints for traded players.
    result = data.groupby(
        "MLBAM_ID", as_index=False
    )["WAR"].sum()

    result["MLBAM_ID"] = result["MLBAM_ID"].astype(int)

    return result.rename(
        columns={"WAR": war_type}
    )


def main():
    print("=" * 50)
    print("DIAMOND VALUE MODEL")
    print("2026 Projection Backtest")
    print("=" * 50)

    predictions = pd.read_csv(PROJECTIONS_FILE)

    predictions = predictions[
        predictions["Projection_Year"] == SEASON
    ].copy()

    if predictions.duplicated(["MLBAM_ID"]).any():
        raise ValueError("Duplicate player projections")

    print("\nDownloading 2026 batting bWAR...")
    batting = prepare_war(
        bwar_bat(), "Actual_Batting_bWAR"
    )

    print("Downloading 2026 pitching bWAR...")
    pitching = prepare_war(
        bwar_pitch(), "Actual_Pitching_bWAR"
    )

    actual = batting.merge(
        pitching,
        on="MLBAM_ID",
        how="outer",
        validate="one_to_one"
    )

    # Players appearing in either dataset have
    # zero contribution from an absent component.
    actual["Actual_Batting_bWAR"] = (
        actual["Actual_Batting_bWAR"].fillna(0)
    )

    actual["Actual_Pitching_bWAR"] = (
        actual["Actual_Pitching_bWAR"].fillna(0)
    )

    actual["Actual_2026_bWAR"] = (
        actual["Actual_Batting_bWAR"]
        + actual["Actual_Pitching_bWAR"]
    )

    result = predictions.merge(
        actual,
        on="MLBAM_ID",
        how="left",
        validate="one_to_one"
    )

    # No 2026 MLB WAR record is not automatically
    # the same as an observed zero-WAR season.
    result["Has_2026_Record"] = (
        result["Actual_2026_bWAR"].notna()
    )

    evaluated = result["Has_2026_Record"]

    result["Error_WAR"] = (
        result["Actual_2026_bWAR"]
        - result["Projected_bWAR"]
    )

    result["Absolute_Error_WAR"] = (
        result["Error_WAR"].abs()
    )

    result["Squared_Error_WAR"] = (
        result["Error_WAR"] ** 2
    )

    result["Actual_Market_Value"] = (
        result["Actual_2026_bWAR"] * VALUE_PER_WAR
    )

    result["Market_Value_Error"] = (
        result["Actual_Market_Value"]
        - result["Projected_Market_Value"]
    )

    result.to_csv(OUTPUT_FILE, index=False)

    print("\nBACKTEST RESULTS")
    print("-" * 50)
    print("Players projected:", len(result))
    print("Players with 2026 WAR:", int(evaluated.sum()))
    print("Players without 2026 WAR:", int((~evaluated).sum()))

    if evaluated.any():
        valid = result.loc[evaluated]

        mae = valid["Absolute_Error_WAR"].mean()
        bias = valid["Error_WAR"].mean()
        rmse = np.sqrt(
            valid["Squared_Error_WAR"].mean()
        )

        print(f"\nMean Absolute Error: {mae:.3f} WAR")
        print(f"Mean Error (Bias): {bias:.3f} WAR")
        print(f"RMSE: {rmse:.3f} WAR")

        print("\nLargest prediction misses:")

        print(
            valid.nlargest(
                10, "Absolute_Error_WAR"
            )[
                [
                    "Name",
                    "Projected_bWAR",
                    "Actual_2026_bWAR",
                    "Error_WAR"
                ]
            ].to_string(index=False)
        )

    print("\nSaved:", OUTPUT_FILE)
    print("Backtest completed successfully!")


if __name__ == "__main__":
    main()
