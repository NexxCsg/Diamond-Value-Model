
import pandas as pd

# ==========================================
# DIAMOND VALUE MODEL
# v0.5 - Injury Risk Features
# ==========================================

INPUT_FILE = "dvm_2025_LAD_injury_exposure.csv"
OUTPUT_FILE = "dvm_2025_LAD_injury_risk.csv"

def main():
    print("=" * 55)
    print("DIAMOND VALUE MODEL")
    print("2025 Injury Risk Features")
    print("=" * 55)

    df = pd.read_csv(INPUT_FILE)

    df["Injury_History_Status"] = (
        df["IL_Exposure_Status"]
        .map({
            "Observed": "No_Unresolved_Stints",
            "Right-Censored": "Incomplete",
            "Ambiguous": "Incomplete"
        })
        .fillna("Incomplete")
    )

    df["Confirmed_IL_Days"] = pd.to_numeric(
        df["Closed_IL_Days"],
        errors="coerce"
    )

    df["IL_History_Usable"] = (
        df["Injury_History_Status"]
        == "No_Unresolved_Stints"
    )

    # Do not interpret missing transactions
    # as proof that a player was injury-free.
    df["IL_Transaction_Evidence"] = (
        df["IL_Transaction_Count"]
        .apply(
            lambda x: (
                "Recorded"
                if pd.notna(x) and x > 0
                else "None_Found"
            )
        )
    )

    # Descriptive exposure only.
    # Calendar-day denominator, not MLB games.
    season_days = (
        pd.Timestamp("2025-09-29")
        - pd.Timestamp("2025-03-18")
    ).days

    df["IL_Exposure_Share"] = (
        df["Confirmed_IL_Days"] / season_days
    ).clip(0, 1)

    # Exclude unresolved histories from
    # the initial predictive feature.
    df.loc[
        ~df["IL_History_Usable"],
        "IL_Exposure_Share"
    ] = float("nan")

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nDATA QUALITY")
    print("-" * 55)

    print("Total players:", len(df))

    print(
        "Usable histories:",
        int(df["IL_History_Usable"].sum())
    )

    print(
        "Incomplete histories:",
        int((~df["IL_History_Usable"]).sum())
    )

    print(
        "Players with IL transactions:",
        int(
            (df["IL_Transaction_Count"] > 0).sum()
        )
    )

    print("\nHIGHEST CONFIRMED IL EXPOSURE")
    print("-" * 55)

    usable = df[
        df["IL_History_Usable"]
    ]

    print(
        usable.nlargest(
            10, "Confirmed_IL_Days"
        )[
            [
                "Name",
                "Confirmed_IL_Days",
                "IL_Exposure_Share",
                "IL_Transaction_Evidence"
            ]
        ].to_string(index=False)
    )

    print("\nSaved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
