
import pandas as pd

# ==========================================
# DIAMOND VALUE MODEL
# v0.5 - Injury Exposure Model
# ==========================================

INPUT_FILE = "dvm_2025_LAD_injury_history.csv"
STINTS_FILE = "dvm_2025_LAD_il_stints.csv"
OUTPUT_FILE = "dvm_2025_LAD_injury_exposure.csv"

SEASON_START = pd.Timestamp("2025-03-18")
SEASON_END = pd.Timestamp("2025-09-28")
SEASON_END_EXCLUSIVE = SEASON_END + pd.Timedelta(days=1)


def clipped_days(start, end):
    if pd.isna(start) or pd.isna(end):
        return 0

    first = max(start, SEASON_START)
    last = min(end, SEASON_END_EXCLUSIVE)

    return max((last - first).days, 0)


def main():
    print("=" * 55)
    print("DIAMOND VALUE MODEL")
    print("2025 Injury Exposure Model")
    print("=" * 55)

    players = pd.read_csv(INPUT_FILE)

    stints = pd.read_csv(STINTS_FILE)

    stints["IL_Start"] = pd.to_datetime(
        stints["IL_Start"], errors="coerce"
    )

    stints["IL_End"] = pd.to_datetime(
        stints["IL_End"], errors="coerce"
    )

    records = []

    for _, player in players.iterrows():
        player_id = int(player["MLBAM_ID"])

        player_stints = stints[
            stints["MLBAM_ID"] == player_id
        ].sort_values("IL_Start")

        closed_days = 0
        censored_days = 0
        uncertain = False

        for _, stint in player_stints.iterrows():
            start = stint["IL_Start"]
            end = stint["IL_End"]
            status = stint["Status"]

            if status == "Closed":
                closed_days += clipped_days(
                    start, end
                )

            elif status == "Unresolved":
                # Observed through the season cutoff,
                # not a confirmed activation date.
                censored_days += clipped_days(
                    start, SEASON_END_EXCLUSIVE
                )

            else:
                # Missing activation between separate
                # placements cannot be reconstructed.
                uncertain = True

        flags = str(
            player.get("IL_Data_Flags", "")
        )

        if "Missing_Activation" in flags:
            uncertain = True

        records.append({
            "MLBAM_ID": player_id,
            "Closed_IL_Days": closed_days,
            "Censored_IL_Days": censored_days,
            "Known_IL_Exposure_Days": (
                closed_days + censored_days
            ),
            "IL_Exposure_Uncertain": uncertain,
            "IL_Exposure_Status": (
                "Ambiguous" if uncertain
                else "Right-Censored"
                if censored_days > 0
                else "Observed"
            )
        })

    exposure = pd.DataFrame(records)

    result = players.merge(
        exposure,
        on="MLBAM_ID",
        how="left",
        validate="one_to_one"
    )

    result.to_csv(
        OUTPUT_FILE, index=False
    )

    print("\nEXPOSURE SUMMARY")
    print("-" * 55)

    print("Players:", len(result))

    print(
        result["IL_Exposure_Status"]
        .value_counts().to_string()
    )

    print("\nTOP KNOWN IL EXPOSURE")
    print("-" * 55)

    print(
        result.nlargest(
            12, "Known_IL_Exposure_Days"
        )[
            [
                "Name",
                "Closed_IL_Days",
                "Censored_IL_Days",
                "Known_IL_Exposure_Days",
                "IL_Exposure_Status"
            ]
        ].to_string(index=False)
    )

    print("\nSaved:", OUTPUT_FILE)
    print("Injury exposure model complete!")


if __name__ == "__main__":
    main()
