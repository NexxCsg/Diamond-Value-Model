
import requests
import pandas as pd

BASE_URL = "https://statsapi.mlb.com/api/v1"
SEASON = 2025
TEAM_ID = 119

session = requests.Session()

response = session.get(
    f"{BASE_URL}/teams/{TEAM_ID}/roster",
    params={"rosterType": "fullSeason", "season": SEASON},
    timeout=30
)
response.raise_for_status()

roster = response.json().get("roster", [])
rows = []

for player in roster:
    player_id = player["person"]["id"]
    name = player["person"]["fullName"]

    response = session.get(
        f"{BASE_URL}/people/{player_id}/stats",
        params={
            "stats": "yearByYear",
            "group": "pitching",
            "season": SEASON
        },
        timeout=30
    )
    response.raise_for_status()

    groups = response.json().get("stats", [])

    for group in groups:
        for split in group.get("splits", []):
            if str(split.get("season")) != str(SEASON):
                continue

            team = split.get("team") or {}

            if team.get("id") != TEAM_ID:
                continue

            stats = split.get("stat", {})

            if int(stats.get("gamesPlayed") or 0) == 0:
                continue

            rows.append({
                "MLBAM_ID": player_id,
                "Name": name,
                "Team": "LAD",
                "Season": SEASON,
                "G": stats.get("gamesPlayed"),
                "GS": stats.get("gamesStarted"),
                "IP": stats.get("inningsPitched"),
                "ERA": stats.get("era"),
                "WHIP": stats.get("whip"),
                "SO": stats.get("strikeOuts")
            })

df = pd.DataFrame(rows)

if df.empty:
    raise ValueError("No Dodgers pitcher records retrieved")

if df.duplicated(["MLBAM_ID", "Team", "Season"]).any():
    raise ValueError("Duplicate player-team-season records detected")

df.to_csv("mlb_pitchers_2025_LAD.csv", index=False)

print("Dodgers pitchers retrieved:", len(df))
print(df.to_string(index=False))
print("Saved: mlb_pitchers_2025_LAD.csv")
