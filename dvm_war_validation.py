
import pandas as pd

players = pd.read_csv("dvm_2025_LAD_valuations_test.csv")
hitters = pd.read_csv("mlb_hitters_2025_LAD.csv")
pitchers = pd.read_csv("mlb_pitchers_2025_LAD.csv")

hitter_ids = set(hitters["MLBAM_ID"])
pitcher_ids = set(pitchers["MLBAM_ID"])

print("Unique players:", len(players))
print("Duplicate IDs:", players["MLBAM_ID"].duplicated().sum())

missing = []

for _, player in players.iterrows():
    player_id = player["MLBAM_ID"]
    name = player["Name"]

    if player_id in hitter_ids and pd.isna(player["Batting_bWAR"]):
        missing.append((name, "Batting"))

    if player_id in pitcher_ids and pd.isna(player["Pitching_bWAR"]):
        missing.append((name, "Pitching"))

print("Missing required WAR components:", len(missing))

for name, component in missing:
    print(name, "|", component)

print("Missing total bWAR:", players["Total_bWAR"].isna().sum())
