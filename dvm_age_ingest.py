
import pandas as pd
import requests
from datetime import date, datetime

# ==========================================
# DIAMOND VALUE MODEL (DVM)
# Automated Player Age Importer - v0.4
# ==========================================

INPUT_FILE = "dvm_2025_LAD_financial_model.csv"
OUTPUT_FILE = "dvm_2025_LAD_with_ages.csv"

REFERENCE_DATE = date(2025, 6, 30)

API_URL = "https://statsapi.mlb.com/api/v1/people/{}"


def calculate_age(birth_date):
    birthday = datetime.strptime(
        birth_date, "%Y-%m-%d"
    ).date()

    age = REFERENCE_DATE.year - birthday.year

    if (
        REFERENCE_DATE.month,
        REFERENCE_DATE.day
    ) < (
        birthday.month,
        birthday.day
    ):
        age -= 1

    return age


def get_player_age(player_id, session):
    url = API_URL.format(int(player_id))

    try:
        response = session.get(
            url,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()
        people = data.get("people", [])

        if not people:
            return None

        birth_date = people[0].get("birthDate")

        if not birth_date:
            return None

        return calculate_age(birth_date)

    except (
        requests.RequestException,
        ValueError,
        KeyError
    ) as error:
        print(
            f"Could not retrieve age for "
            f"player {player_id}: {error}"
        )
        return None


def main():
    print("=" * 50)
    print("DIAMOND VALUE MODEL")
    print("Player Age Importer - v0.4")
    print("=" * 50)

    df = pd.read_csv(INPUT_FILE)

    required = ["MLBAM_ID", "Name"]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if df["MLBAM_ID"].isna().any():
        raise ValueError(
            "Missing MLBAM player IDs in dataset"
        )

    if df["MLBAM_ID"].duplicated().any():
        raise ValueError(
            "Duplicate MLBAM player IDs detected"
        )

    session = requests.Session()

    ages = {}

    unique_players = df[
        ["MLBAM_ID", "Name"]
    ].drop_duplicates()

    print(
        f"\nRetrieving ages for "
        f"{len(unique_players)} players...\n"
    )

    for _, player in unique_players.iterrows():

        player_id = int(player["MLBAM_ID"])
        player_name = player["Name"]

        age = get_player_age(
            player_id,
            session
        )

        ages[player_id] = age

        if age is None:
            print(
                f"{player_name}: Age unavailable"
            )
        else:
            print(
                f"{player_name}: {age}"
            )

    df["Age"] = df["MLBAM_ID"].map(ages)

    df["Age_Reference_Date"] = (
        REFERENCE_DATE.isoformat()
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 50)
    print("AGE IMPORT RESULTS")
    print("=" * 50)

    print("Total players:", len(df))

    print(
        "Players with ages:",
        df["Age"].notna().sum()
    )

    print(
        "Players missing ages:",
        df["Age"].isna().sum()
    )

    print(
        "Reference date:",
        REFERENCE_DATE
    )

    print("\nSaved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
