
import pandas as pd
import numpy as np

# ==========================================
# DIAMOND VALUE MODEL
# 2026 Backtest Baseline Comparison - v0.4
# ==========================================

INPUT_FILE = "dvm_2026_backtest.csv"
OUTPUT_FILE = "dvm_2026_baseline_comparison.csv"


def evaluate(actual, predicted):
    error = actual - predicted

    return {
        "MAE": np.abs(error).mean(),
        "RMSE": np.sqrt(np.mean(error ** 2)),
        "Bias": error.mean()
    }


def main():
    print("=" * 55)
    print("DIAMOND VALUE MODEL")
    print("2026 Baseline Comparison")
    print("=" * 55)

    df = pd.read_csv(INPUT_FILE)

    required = [
        "MLBAM_ID",
        "Name",
        "Historical_bWAR",
        "Projected_bWAR",
        "Actual_2026_bWAR"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if df["MLBAM_ID"].duplicated().any():
        raise ValueError("Duplicate player IDs")

    for col in [
        "Historical_bWAR",
        "Projected_bWAR",
        "Actual_2026_bWAR"
    ]:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    # Evaluate all models on exactly the same players.
    valid = df.dropna(
        subset=[
            "Historical_bWAR",
            "Projected_bWAR",
            "Actual_2026_bWAR"
        ]
    ).copy()

    if valid.empty:
        raise ValueError("No complete player records")

    # Baseline 1: Repeat actual 2025 WAR.
    valid["Repeat_2025_WAR"] = (
        valid["Historical_bWAR"]
    )

    # Baseline 2: Repeat 2025 WAR, floored at zero.
    valid["Zero_Floor_WAR"] = (
        valid["Historical_bWAR"].clip(lower=0)
    )

    models = {
        "Repeat 2025 WAR": "Repeat_2025_WAR",
        "Zero-floor 2025 WAR": "Zero_Floor_WAR",
        "DVM Age Curve": "Projected_bWAR"
    }

    results = []

    for name, column in models.items():
        metrics = evaluate(
            valid["Actual_2026_bWAR"],
            valid[column]
        )

        results.append({
            "Model": name,
            "Players": len(valid),
            **metrics
        })

    summary = pd.DataFrame(results)
    summary = summary.sort_values("MAE")

    print("\nMODEL COMPARISON")
    print("-" * 55)
    print(
        summary.to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}"
        )
    )

    winner = summary.iloc[0]["Model"]

    print("\nLowest MAE:", winner)

    age_mae = summary.loc[
        summary["Model"] == "DVM Age Curve",
        "MAE"
    ].iloc[0]

    repeat_mae = summary.loc[
        summary["Model"] == "Repeat 2025 WAR",
        "MAE"
    ].iloc[0]

    improvement = repeat_mae - age_mae

    print(
        "DVM MAE improvement vs repeat-2025:",
        f"{improvement:+.3f} WAR"
    )

    summary.to_csv(OUTPUT_FILE, index=False)

    print("\nSaved:", OUTPUT_FILE)
    print("Baseline comparison complete!")


if __name__ == "__main__":
    main()
