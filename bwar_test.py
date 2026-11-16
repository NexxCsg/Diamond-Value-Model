
from pybaseball import bwar_bat

try:
    data = bwar_bat(return_all=True)

    print("Rows retrieved:", len(data))
    print("Columns:", list(data.columns))

    print(data.head())

    data.to_csv("bwar_hitters_test.csv", index=False)
    print("Saved: bwar_hitters_test.csv")

except Exception as error:
    print("Error:", type(error).__name__, error)
