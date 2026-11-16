
from pybaseball import bwar_pitch

try:
    data = bwar_pitch(return_all=True)

    print("Rows retrieved:", len(data))
    print("Columns:", list(data.columns))
    print("Latest year:", data["year_ID"].max())

    dodgers = data[
        (data["year_ID"] == 2025) &
        (data["team_ID"] == "LAD")
    ].copy()

    print("2025 Dodgers pitching WAR records:", len(dodgers))

    columns = [
        "name_common",
        "mlb_ID",
        "team_ID",
        "year_ID",
        "WAR"
    ]

    print(dodgers[columns].to_string(index=False))

    data.to_csv("bwar_pitchers_test.csv", index=False)
    print("Saved: bwar_pitchers_test.csv")

except Exception as error:
    print("Error:", type(error).__name__, error)
