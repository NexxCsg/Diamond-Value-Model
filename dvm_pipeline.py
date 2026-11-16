

import pandas as pd

# DVM Pipeline v0.1
# 2025 Los Angeles Dodgers

SEASON = 2025
TEAM = "LAD"

hitters = pd.read_csv("mlb_hitters_2025_LAD.csv")
pitchers = pd.read_csv("mlb_pitchers_2025_LAD.csv")
valuations = pd.read_csv("dvm_2025_LAD_valuations_test.csv")

for name, df in [
    ("Hitters", hitters),
    ("Pitchers", pitchers),
    ("Valuations", valuations)
]:
    if df["MLBAM_ID"].isna().any():
        raise ValueError(f"{name}: Missing player IDs")

    if df.duplicated(["MLBAM_ID", "Team", "Season"]).any():
        raise ValueError(f"{name}: Duplicate player records")

    if not (
        (df["Team"] == TEAM) &
        (df["Season"] == SEASON)
    ).all():
        raise ValueError(f"{name}: Unexpected team or season")

if valuations["Total_bWAR"].isna().any():
    raise ValueError("Missing total bWAR")

# Verify that all hitter and pitcher records
# appear in the valuation table.
expected_ids = set(hitters["MLBAM_ID"]) | set(pitchers["MLBAM_ID"])
actual_ids = set(valuations["MLBAM_ID"])

if expected_ids != actual_ids:
    raise ValueError("Player IDs do not match valuation records")

output_file = "DVM_Pipeline_2025_LAD.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    hitters.to_excel(writer, sheet_name="Hitters", index=False)
    pitchers.to_excel(writer, sheet_name="Pitchers", index=False)
    valuations.to_excel(writer, sheet_name="Valuations", index=False)

print("Hitters:", len(hitters))
print("Pitchers:", len(pitchers))
print("Unique players:", len(valuations))
print("Saved:", output_file)
