
import pandas as pd

df = pd.read_csv("dvm_2025_LAD_valuations_test.csv")

# Test 1: Correct number of players
assert len(df) == 62, "Incorrect player count"

# Test 2: No duplicate player IDs
assert not df["MLBAM_ID"].duplicated().any(), \
    "Duplicate player IDs"

# Test 3: No missing total WAR
assert df["Total_bWAR"].notna().all(), \
    "Missing WAR values"

# Test 4: Verify valuation calculations
expected = df["Total_bWAR"] * 8_000_000

assert (
    (df["Base_Market_Value"] - expected).abs() < 0.01
).all(), "Incorrect valuation calculations"

# Test 5: Verify Ohtani's combined WAR
ohtani = df.loc[df["MLBAM_ID"] == 660271]

assert len(ohtani) == 1, "Ohtani record missing"

assert abs(
    ohtani.iloc[0]["Total_bWAR"] - 7.71
) < 0.001, "Incorrect Ohtani WAR"

print("All 5 DVM tests passed!")
