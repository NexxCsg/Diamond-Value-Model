
import pandas as pd

# ==========================================
# DIAMOND VALUE MODEL (DVM)
# Financial Integration - v0.2
# ==========================================

VALUATIONS_FILE = "dvm_2025_LAD_contract_valuations.csv"
SALARIES_FILE = "dvm_2025_LAD_reported_salaries.csv"
OUTPUT_FILE = "dvm_2025_LAD_financial_model.csv"

KEYS = ["MLBAM_ID", "Season"]


def main():
    print("=" * 50)
    print("DIAMOND VALUE MODEL")
    print("Financial Integration - v0.2")
    print("=" * 50)

    valuations = pd.read_csv(VALUATIONS_FILE)
    salaries = pd.read_csv(SALARIES_FILE)

    # Prevent duplicate player-season records.
    for name, data in [
        ("Valuations", valuations),
        ("Salaries", salaries)
    ]:
        if data.duplicated(KEYS).any():
            raise ValueError(
                f"{name} contains duplicate player-season records"
            )

    # Preserve every player in the DVM roster.
    salary_columns = [
        "MLBAM_ID",
        "Season",
        "Reported_Salary",
        "Reported_Salary_Source"
    ]

    merged = valuations.merge(
        salaries[salary_columns],
        on=KEYS,
        how="left",
        validate="one_to_one"
    )

    if len(merged) != len(valuations):
        raise ValueError("Player count changed during merge")

    # Reported salary is a separate source-defined metric.
    # Do not substitute it for contractual AAV or Base_Salary.
    # Missing values remain missing.

    merged["Reported_Salary_Difference_From_AAV"] = (
        merged["Reported_Salary"] - merged["AAV"]
    )

    # Historical economic surplus is calculated only when
    # contractual AAV or Base_Salary is available.
    # Existing valuation formulas are preserved.

    merged.to_csv(OUTPUT_FILE, index=False)

    print("\nFINANCIAL MODEL RESULTS")
    print("-" * 50)
    print("Total players:", len(merged))
    print("Players with AAV:", merged["AAV"].notna().sum())
    print(
        "Players with reported salary:",
        merged["Reported_Salary"].notna().sum()
    )
    print(
        "Players with both:",
        (
            merged["AAV"].notna()
            & merged["Reported_Salary"].notna()
        ).sum()
    )

    print("\nSaved:", OUTPUT_FILE)
    print("Financial integration completed successfully!")


if __name__ == "__main__":
    main()
