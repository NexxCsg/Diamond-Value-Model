
import pandas as pd
from pybaseball import bwar_bat, bwar_pitch

# ==========================================
# DIAMOND VALUE MODEL (DVM)
# Automated Salary Importer - v0.2
# ==========================================

SEASON = 2025
TEAM = "LAD"

ROSTER_FILE = "dvm_2025_LAD_valuations_test.csv"
OUTPUT_FILE = "dvm_2025_LAD_reported_salaries.csv"


def prepare_salaries(data, source):
    """Extract salary records for the selected team and season."""

    required = [
        "mlb_ID",
        "name_common",
        "year_ID",
        "team_ID",
        "salary"
    ]

    missing = [col for col in required if col not in data.columns]

    if missing:
        raise ValueError(
            f"{source}: Missing required columns: {missing}"
        )

    result = data[
        (data["year_ID"] == SEASON)
        & (data["team_ID"] == TEAM)
    ][required].copy()

    result = result.rename(columns={
        "mlb_ID": "MLBAM_ID",
        "name_common": "Player",
        "year_ID": "Season",
        "team_ID": "Team",
        "salary": "Reported_Salary"
    })

    result["MLBAM_ID"] = pd.to_numeric(
        result["MLBAM_ID"],
        errors="coerce"
    )

    result["Reported_Salary"] = pd.to_numeric(
        result["Reported_Salary"],
        errors="coerce"
    )

    # Keep only records with a valid ID and salary.
    result = result.dropna(
        subset=["MLBAM_ID", "Reported_Salary"]
    )

    result["MLBAM_ID"] = result["MLBAM_ID"].astype(int)

    result["Source_Dataset"] = source

    return result


def main():

    print("=" * 50)
    print("DIAMOND VALUE MODEL")
    print("Automated Salary Importer - v0.2")
    print("=" * 50)

    print("\nDownloading batting salary data...")

    batting = prepare_salaries(
        bwar_bat(),
        "Batting"
    )

    print("Downloading pitching salary data...")

    pitching = prepare_salaries(
        bwar_pitch(),
        "Pitching"
    )

    # Combine both sources.
    combined = pd.concat(
        [batting, pitching],
        ignore_index=True
    )

    # A player can appear in both batting and pitching.
    # Verify that salary values agree before deduplicating.
    conflicts = combined.groupby(
        ["MLBAM_ID", "Season"]
    )["Reported_Salary"].nunique()

    if (conflicts > 1).any():
        raise ValueError(
            "Conflicting salary values detected for player-season"
        )

    # Keep one salary record per player-season.
    combined = combined.sort_values(
        ["MLBAM_ID", "Source_Dataset"]
    )

    combined = combined.drop_duplicates(
        subset=["MLBAM_ID", "Season"],
        keep="first"
    )

    # Load existing DVM roster.
    roster = pd.read_csv(ROSTER_FILE)

    roster = roster[
        ["MLBAM_ID", "Name", "Season"]
    ].copy()

    if roster.duplicated(
        ["MLBAM_ID", "Season"]
    ).any():
        raise ValueError(
            "Duplicate player-season records in DVM roster"
        )

    # Match salaries to existing DVM player IDs.
    merged = roster.merge(
        combined[
            [
                "MLBAM_ID",
                "Season",
                "Reported_Salary",
                "Source_Dataset"
            ]
        ],
        on=["MLBAM_ID", "Season"],
        how="left",
        validate="one_to_one"
    )

    merged = merged.rename(
        columns={"Name": "Player"}
    )

    # Preserve the source for each salary.
    merged["Reported_Salary_Source"] = pd.NA

    has_salary = merged["Reported_Salary"].notna()

    merged.loc[
        has_salary,
        "Reported_Salary_Source"
    ] = "Baseball-Reference via pybaseball"

    # Missing salaries remain NaN, never zero.
    merged.to_csv(
        OUTPUT_FILE,
        index=False
    )

    total = len(merged)

    with_salary = merged[
        "Reported_Salary"
    ].notna().sum()

    without_salary = total - with_salary

    print("\n" + "=" * 50)
    print("IMPORT RESULTS")
    print("=" * 50)

    print(f"Total DVM players: {total}")
    print(f"Players with reported salary: {with_salary}")
    print(f"Players without reported salary: {without_salary}")

    print(f"\nSaved: {OUTPUT_FILE}")

    print("\nSalary importer completed successfully!")


if __name__ == "__main__":
    main()
