
import pandas as pd

SEASON = 2025
TEAM = "LAD"
WAR_DOLLARS = 8_000_000

hitters = pd.read_csv("mlb_hitters_2025_LAD.csv")
pitchers = pd.read_csv("mlb_pitchers_2025_LAD.csv")

bat_war = pd.read_csv("bwar_hitters_test.csv")
pitch_war = pd.read_csv("bwar_pitchers_test.csv")

def prepare_war(df, output_column):
    df = df[
        (df["year_ID"] == SEASON) &
        (df["team_ID"] == TEAM)
    ].copy()

    df = df.dropna(subset=["mlb_ID"])
    df["MLBAM_ID"] = df["mlb_ID"].astype(int)

    if df.duplicated(["MLBAM_ID"]).any():
        raise ValueError(
            f"Duplicate WAR records in {output_column}"
        )

    return df[["MLBAM_ID", "WAR"]].rename(
        columns={"WAR": output_column}
    )

bat_war = prepare_war(bat_war, "Batting_bWAR")
pitch_war = prepare_war(pitch_war, "Pitching_bWAR")

# Create one row per player across both datasets
players = pd.concat([
    hitters[["MLBAM_ID", "Name", "Team", "Season"]],
    pitchers[["MLBAM_ID", "Name", "Team", "Season"]]
]).drop_duplicates(subset=["MLBAM_ID"])

players = players.merge(
    bat_war, on="MLBAM_ID", how="left"
)

players = players.merge(
    pitch_war, on="MLBAM_ID", how="left"
)

# Missing WAR components are not automatically zero.
# Keep them missing until source coverage is checked.
players["Total_bWAR"] = players[
    ["Batting_bWAR", "Pitching_bWAR"]
].sum(axis=1, min_count=1)

players["Base_Market_Value"] = (
    players["Total_bWAR"] * WAR_DOLLARS
)

players.to_csv(
    "dvm_2025_LAD_valuations_test.csv",
    index=False
)

print("Unique players:", len(players))
print(players.to_string(index=False))
print("Saved: dvm_2025_LAD_valuations_test.csv")
