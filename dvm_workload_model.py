
import pandas as pd
import numpy as np

# ==========================================
# DIAMOND VALUE MODEL
# v0.5 - Improved Workload Classification
# ==========================================

INPUT_FILE = "dvm_2025_LAD_availability.csv"
OUTPUT_FILE = "dvm_2025_LAD_workload.csv"


def classify_player(row):
    hitting_gp = row["Hitting_GP"]
    pitching_gp = row["Pitching_GP"]
    pitching_gs = row["Pitching_GS"]

    batting_war = row["Batting_bWAR"]
    pitching_war = row["Pitching_bWAR"]

    has_hitting = pd.notna(hitting_gp) and hitting_gp > 0
    has_pitching = pd.notna(pitching_gp) and pitching_gp > 0

    if (
        has_hitting
        and has_pitching
        and abs(batting_war) >= 0.5
        and abs(pitching_war) >= 0.5
    ):
        return "Two-Way Player"

    if has_pitching and (
        not has_hitting
        or abs(pitching_war) > abs(batting_war)
    ):
        if pd.isna(pitching_gs):
            return "Unclassified Pitcher"

        start_rate = pitching_gs / pitching_gp

        if start_rate >= 0.60:
            return "Starting Pitcher"

        if start_rate <= 0.20:
            return "Relief Pitcher"

        return "Hybrid Pitcher"

    if has_hitting:
        return "Position Player"

    return "No MLB Appearance Data"


def main():
    print("=" * 55)
    print("DIAMOND VALUE MODEL")
    print("Improved 2025 Workload Classification")
    print("=" * 55)

    df = pd.read_csv(INPUT_FILE)

    required = [
        "MLBAM_ID",
        "Name",
        "Batting_bWAR",
        "Pitching_bWAR",
        "Hitting_GP",
        "Pitching_GP",
        "Pitching_GS",
        "Innings_Pitched"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    for col in [
        "Batting_bWAR",
        "Pitching_bWAR",
        "Hitting_GP",
        "Pitching_GP",
        "Pitching_GS"
    ]:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    df["Start_Percentage"] = np.where(
        df["Pitching_GP"] > 0,
        df["Pitching_GS"] / df["Pitching_GP"],
        np.nan
    )

    df["Workload_Role"] = df.apply(
        classify_player, axis=1
    )

    # Descriptive workload indicators.
    # These are not injury probabilities.
    df["Hitting_Game_Share"] = (
        df["Hitting_GP"] / 162
    ).clip(0, 1)

    df["Pitching_Start_Share"] = (
        df["Pitching_GS"] / 32
    ).clip(0, 1)

    df["Relief_Appearance_Share"] = (
        df["Pitching_GP"] / 65
    ).clip(0, 1)

    df["Workload_Reference"] = np.select(
        [
            df["Workload_Role"] == "Position Player",
            df["Workload_Role"] == "Starting Pitcher",
            df["Workload_Role"] == "Relief Pitcher",
            df["Workload_Role"] == "Hybrid Pitcher",
            df["Workload_Role"] == "Two-Way Player"
        ],
        [
            "162 games",
            "32 starts",
            "65 appearances",
            "Mixed pitching workload",
            "Separate hitting and pitching workloads"
        ],
        default="Insufficient role data"
    )

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nUPDATED CLASSIFICATIONS")
    print("-" * 55)

    print(df["Workload_Role"].value_counts().to_string())

    print("\nHYBRID PITCHERS")
    print("-" * 55)

    hybrids = df[
        df["Workload_Role"] == "Hybrid Pitcher"
    ]

    if hybrids.empty:
        print("None")
    else:
        print(
            hybrids[
                [
                    "Name",
                    "Pitching_GP",
                    "Pitching_GS",
                    "Start_Percentage"
                ]
            ].to_string(index=False)
        )

    print("\nSaved:", OUTPUT_FILE)
    print("Classification update complete!")


if __name__ == "__main__":
    main()
