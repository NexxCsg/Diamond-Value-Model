
import re
import requests
import pandas as pd

# ==========================================
# DIAMOND VALUE MODEL
# v0.5 - Corrected Injury History Importer
# ==========================================

INPUT_FILE = "dvm_2025_LAD_workload.csv"
OUTPUT_FILE = "dvm_2025_LAD_injury_history.csv"
STINTS_FILE = "dvm_2025_LAD_il_stints.csv"

TEAM_ID = 119

SEASON_START = pd.Timestamp("2025-03-18")
SEASON_END = pd.Timestamp("2025-09-28")


def fetch_transactions():
    url = "https://statsapi.mlb.com/api/v1/transactions"

    params = {
        "teamId": TEAM_ID,
        "startDate": "01/01/2025",
        "endDate": "12/31/2025"
    }

    response = requests.get(
        url, params=params, timeout=45
    )
    response.raise_for_status()

    return response.json().get("transactions", [])


def event_type(description):
    text = description.lower()

    if "injured list" not in text:
        return None

    if "transferred" in text:
        return "Transfer"

    if "activated" in text:
        return "Activation"

    if "placed" in text:
        return "Placement"

    return "Other"


def get_start_date(transaction):
    description = transaction.get("description", "")

    match = re.search(
        r"retroactive to ([A-Za-z]+ \d{1,2}, \d{4})",
        description,
        re.IGNORECASE
    )

    if match:
        parsed = pd.to_datetime(
            match.group(1), errors="coerce"
        )

        if pd.notna(parsed):
            return parsed

    # IMPORTANT:
    # Do not use effectiveDate here.
    # Some MLB records have an effectiveDate
    # unrelated to the original placement date.
    return pd.to_datetime(
        transaction.get("date"),
        errors="coerce"
    )


def create_stint(player_id, event):
    return {
        "MLBAM_ID": player_id,
        "IL_Start": event["Start"],
        "IL_End": pd.NaT,
        "Status": "Open",
        "Placement_Description": event["Description"]
    }


def build_stints(player_id, transactions):
    events = []

    for transaction in transactions:
        person = transaction.get("person") or {}

        if person.get("id") != player_id:
            continue

        description = transaction.get("description", "")
        kind = event_type(description)

        if kind is None:
            continue

        events.append({
            "Date": pd.to_datetime(
                transaction.get("date"),
                errors="coerce"
            ),
            "Start": get_start_date(transaction),
            "Type": kind,
            "Description": description
        })

    events.sort(
        key=lambda x: (
            x["Date"]
            if pd.notna(x["Date"])
            else pd.Timestamp.max
        )
    )

    stints = []
    flags = set()
    current = None

    for event in events:
        kind = event["Type"]

        if kind == "Placement":
            if current is None:
                current = create_stint(
                    player_id, event
                )
                continue

            gap = None

            if (
                pd.notna(current["IL_Start"])
                and pd.notna(event["Start"])
            ):
                gap = abs(
                    (
                        event["Start"]
                        - current["IL_Start"]
                    ).days
                )

            if gap is not None and gap <= 7:
                flags.add("Possible_Duplicate_Placement")

                current["IL_Start"] = min(
                    current["IL_Start"],
                    event["Start"]
                )
            else:
                # A second placement without an
                # activation creates ambiguity.
                current["Status"] = (
                    "Missing_Activation"
                )
                stints.append(current)

                flags.add(
                    "Missing_Activation_Between_Placements"
                )

                current = create_stint(
                    player_id, event
                )

        elif kind == "Transfer":
            if current is None:
                flags.add(
                    "Transfer_Without_Placement"
                )

        elif kind == "Activation":
            if current is None:
                flags.add(
                    "Activation_Without_Placement"
                )
            else:
                current["IL_End"] = event["Date"]
                current["Status"] = "Closed"
                stints.append(current)
                current = None

    if current is not None:
        current["Status"] = "Unresolved"
        stints.append(current)

    return stints, flags, len(events)


def days_within_season(start, end):
    if pd.isna(start) or pd.isna(end):
        return None

    first = max(start, SEASON_START)
    last = min(
        end,
        SEASON_END + pd.Timedelta(days=1)
    )

    return max((last - first).days, 0)


def main():
    print("=" * 55)
    print("DIAMOND VALUE MODEL")
    print("Corrected 2025 Injury History Importer")
    print("=" * 55)

    df = pd.read_csv(INPUT_FILE)

    if df["MLBAM_ID"].duplicated().any():
        raise ValueError("Duplicate MLBAM IDs")

    print("\nDownloading MLB transactions...")
    transactions = fetch_transactions()

    print("Transactions retrieved:", len(transactions))

    all_stints = []
    summaries = []

    for _, player in df.iterrows():
        player_id = int(player["MLBAM_ID"])

        stints, flags, count = build_stints(
            player_id, transactions
        )

        confirmed_days = 0
        incomplete = False

        for stint in stints:
            stint["Name"] = player["Name"]

            days = days_within_season(
                stint["IL_Start"],
                stint["IL_End"]
            )

            stint["2025_IL_Days"] = days

            if days is None:
                incomplete = True
            else:
                confirmed_days += days

            all_stints.append(stint)

        unresolved_count = sum(
            s["Status"] != "Closed"
            for s in stints
        )

        if flags.intersection({
            "Missing_Activation_Between_Placements",
            "Transfer_Without_Placement",
            "Activation_Without_Placement"
        }):
            incomplete = True

        summaries.append({
            "MLBAM_ID": player_id,
            "IL_Transaction_Count": count,
            "IL_Stint_Count": len(stints),
            "Confirmed_Closed_IL_Days":
                confirmed_days,
            "Documented_2025_IL_Days": (
                None if incomplete
                else confirmed_days
            ),
            "IL_Stints_Unresolved":
                unresolved_count,
            "IL_Data_Flags": (
                "; ".join(sorted(flags))
                if flags else ""
            ),
            "IL_Data_Complete": not incomplete
        })

    summary = pd.DataFrame(summaries)

    result = df.merge(
        summary,
        on="MLBAM_ID",
        how="left",
        validate="one_to_one"
    )

    stints_df = pd.DataFrame(all_stints)

    result.to_csv(
        OUTPUT_FILE, index=False
    )

    stints_df.to_csv(
        STINTS_FILE, index=False
    )

    print("\nINJURY DATA SUMMARY")
    print("-" * 55)

    print("Players:", len(result))

    print(
        "Players with IL transactions:",
        (result["IL_Transaction_Count"] > 0).sum()
    )

    print("Total IL stints:", len(stints_df))

    print(
        "Players with unresolved stints:",
        (result["IL_Stints_Unresolved"] > 0).sum()
    )

    print(
        "Players with data flags:",
        result["IL_Data_Flags"].fillna("").ne("").sum()
    )

    print("\nFLAGGED OR UNRESOLVED PLAYERS")
    print("-" * 55)

    flagged = result[
        result["IL_Data_Flags"].fillna("").ne("")
        | (result["IL_Stints_Unresolved"] > 0)
    ]

    if flagged.empty:
        print("None")
    else:
        print(
            flagged[
                [
                    "Name",
                    "Confirmed_Closed_IL_Days",
                    "Documented_2025_IL_Days",
                    "IL_Stints_Unresolved",
                    "IL_Data_Flags"
                ]
            ].to_string(index=False)
        )

    print("\nSaved:", OUTPUT_FILE)
    print("Saved:", STINTS_FILE)

    print("\nReview unresolved records before modeling.")


if __name__ == "__main__":
    main()
