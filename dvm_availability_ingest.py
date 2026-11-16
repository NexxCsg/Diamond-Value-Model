
import pandas as pd
import requests
import time

# ==========================================
# DIAMOND VALUE MODEL
# v0.5 - Player Availability Data Ingestion
# ==========================================

INPUT_FILE = "dvm_2025_LAD_with_ages.csv"
OUTPUT_FILE = "dvm_2025_LAD_availability.csv"

SEASON = 2025

API_URL = (
    "https://statsapi.mlb.com/api/v1/people/"
    "{player_id}/stats"
)


def fetch_player_stats(player_id, session):
    url = API_URL.format(player_id=int(player_id))

    params = {
        "stats": "season",
        "group": "hitting,pitching",
        "season": SEASON,
        "sportIds": 1
    }

    response = session.get(
        url, params=params, timeout=20
    )

    response.raise_for_status()

    data = response.json()

    result = {
        "Hitting_GP": None,
        "Pitching_GP": None,
        "Pitching_GS": None,
        "Innings_Pitched": None
    }

    for group in data.get("stats", []):
        group_name = (
            group.get("group", {}).get("displayName", "")
        ).lower()

        for split in group.get("splits", []):
            stat = split.get("stat", {})

            if group_name == "hitting":
                result["Hitting_GP"] = stat.get(
                    "gamesPlayed"
                )

            elif group_name == "pitching":
                result["Pitching_GP"] = stat.get(
                    "gamesPlayed"
                )

                result["Pitching_GS"] = stat.get(
                    "gamesStarted"
                )

                result["Innings_Pitched"] = stat.get(
                    "inningsPitched"
                )

    return result


def main():
    print("=" * 55)
    print("DIAMOND VALUE MODEL")
    print("2025 Player Availability Importer")
    print("=" * 55)

    df = pd.read_csv(INPUT_FILE)

    required = [
        "MLBAM_ID",
        "Name",
        "Total_bWAR"
    ]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if df["MLBAM_ID"].duplicated().any():
        raise ValueError(
            "Duplicate MLB player IDs detected"
        )

    records = []

    session = requests.Session()

    total = len(df)

    for index, row in df.iterrows():
        player_id = int(row["MLBAM_ID"])
        name = row["Name"]

        print(
            f"[{len(records) + 1}/{total}] "
            f"Fetching {name}..."
        )

        try:
            stats = fetch_player_stats(
                player_id, session
            )

            status = "Success"

        except requests.RequestException as exc:
            print(f"  API error: {exc}")

            stats = {
                "Hitting_GP": None,
                "Pitching_GP": None,
                "Pitching_GS": None,
                "Innings_Pitched": None
            }

            status = "API_Error"

        records.append({
            "MLBAM_ID": player_id,
            "Name": name,
            **stats,
            "Availability_Data_Status": status
        })

        time.sleep(0.15)

    availability = pd.DataFrame(records)

    result = df.merge(
        availability.drop(columns=["Name"]),
        on="MLBAM_ID",
        how="left",
        validate="one_to_one"
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 55)
    print("IMPORT SUMMARY")
    print("=" * 55)

    print("Total players:", len(result))

    for col in [
        "Hitting_GP",
        "Pitching_GP",
        "Pitching_GS",
        "Innings_Pitched"
    ]:
        print(
            f"{col}: "
            f"{result[col].notna().sum()} populated"
        )

    print("\nAPI errors:", (
        result["Availability_Data_Status"]
        == "API_Error"
    ).sum())

    print("\nSaved:", OUTPUT_FILE)
    print("Availability ingestion complete!")


if __name__ == "__main__":
    main()
