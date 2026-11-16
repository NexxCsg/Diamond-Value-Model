
import numpy as np
import pandas as pd

# ==========================================
# DIAMOND VALUE MODEL
# v0.5 - Injury-Adjusted WAR Backtest
# ==========================================

BACKTEST_FILE = "dvm_2026_backtest.csv"
INJURY_FILE = "dvm_2025_LAD_injury_risk.csv"

OUTPUT_FILE = "dvm_2026_injury_backtest.csv"
SUMMARY_FILE = "dvm_2026_injury_comparison.csv"

# Experimental adjustment strengths.
# These are not medically calibrated.
STRENGTHS = [0.00, 0.05, 0.10, 0.15, 0.20]


def calculate_metrics(actual, predicted):
    error = actual - predicted

    return {
        "MAE": np.mean(np.abs(error)),
        "RMSE": np.sqrt(np.mean(error ** 2)),
        "Bias": np.mean(error)
    }


def main():
    print("=" * 60)
    print("DIAMOND VALUE MODEL")
    print("v0.5 - Injury-Adjusted 2026 Backtest")
    print("=" * 60)

    backtest = pd.read_csv(BACKTEST_FILE)
    injuries = pd.read_csv(INJURY_FILE)

    # Require unique player identifiers.
    for name, frame in [
        ("Backtest", backtest),
        ("Injury", injuries)
    ]:
        if frame["MLBAM_ID"].duplicated().any():
            raise ValueError(
                f"Duplicate MLBAM IDs in {name}"
            )

    injury_columns = [
        "MLBAM_ID",
        "IL_History_Usable",
        "IL_Exposure_Share",
        "Confirmed_IL_Days",
        "IL_Transaction_Evidence"
    ]

    df = backtest.merge(
        injuries[injury_columns],
        on="MLBAM_ID",
        how="left",
        validate="one_to_one",
        indicator=True
    )

    print("\nJOIN VALIDATION")
    print("-" * 60)

    print("Backtest players:", len(backtest))
    print("Merged players:", len(df))

    print(
        "Matched injury records:",
        int((df["_merge"] == "both").sum())
    )

    print(
        "Unmatched injury records:",
        int((df["_merge"] != "both").sum())
    )

    if (df["_merge"] != "both").any():
        raise ValueError(
            "Some players have no injury records."
        )

    # Only players with a recorded 2026
    # performance and usable injury features.
    eligible = df[
        (df["Has_2026_Record"] == True)
        & (df["IL_History_Usable"] == True)
        & df["IL_Exposure_Share"].notna()
        & df["Actual_2026_bWAR"].notna()
        & df["Projected_bWAR"].notna()
    ].copy()

    if eligible.empty:
        raise ValueError(
            "No eligible players for comparison."
        )

    print("\nBACKTEST SAMPLE")
    print("-" * 60)

    print(
        "Players with 2026 records:",
        int(df["Has_2026_Record"].sum())
    )

    print(
        "Eligible injury-model players:",
        len(eligible)
    )

    print(
        "Excluded from matched comparison:",
        len(df) - len(eligible)
    )

    actual = eligible[
        "Actual_2026_bWAR"
    ].to_numpy(dtype=float)

    baseline = eligible[
        "Projected_bWAR"
    ].to_numpy(dtype=float)

    exposure = eligible[
        "IL_Exposure_Share"
    ].to_numpy(dtype=float)

    results = []

    for strength in STRENGTHS:
        # A small illustrative penalty applied
        # to the age-only projected WAR.
        #
        # We clip the multiplier, not the
        # projected WAR itself.
        multiplier = np.clip(
            1 - strength * exposure,
            0,
            1
        )

        prediction = baseline * multiplier

        metrics = calculate_metrics(
            actual, prediction
        )

        results.append({
            "Injury_Strength": strength,
            "Players": len(eligible),
            **metrics
        })

        column_name = (
            f"Predicted_WAR_Injury_"
            f"{int(strength * 100):02d}"
        )

        eligible[column_name] = prediction

    comparison = pd.DataFrame(results)

    baseline_mae = comparison.loc[
        comparison["Injury_Strength"] == 0,
        "MAE"
    ].iloc[0]

    comparison["MAE_Improvement"] = (
        baseline_mae - comparison["MAE"]
    )

    comparison["MAE_Improvement_Pct"] = (
        100
        * comparison["MAE_Improvement"]
        / baseline_mae
        if baseline_mae != 0
        else np.nan
    )

    comparison.to_csv(
        SUMMARY_FILE, index=False
    )

    eligible.to_csv(
        OUTPUT_FILE, index=False
    )

    print("\nMODEL COMPARISON")
    print("-" * 60)

    print(
        comparison.round(4).to_string(
            index=False
        )
    )

    best = comparison.loc[
        comparison["MAE"].idxmin()
    ]

    print("\nLOWEST RETROSPECTIVE MAE")
    print("-" * 60)

    print(
        "Adjustment strength:",
        best["Injury_Strength"]
    )

    print(
        "MAE:",
        round(best["MAE"], 4)
    )

    print(
        "Baseline MAE:",
        round(baseline_mae, 4)
    )

    print(
        "MAE improvement:",
        round(best["MAE_Improvement"], 4)
    )

    print("\nSaved:", OUTPUT_FILE)
    print("Saved:", SUMMARY_FILE)

    print(
        "\nNOTE: This is retrospective testing."
    )
    print(
        "Selecting the best strength on 2026"
        " outcomes is not independent validation."
    )


if __name__ == "__main__":
    main()
