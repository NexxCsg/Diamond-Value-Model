
import subprocess
import sys

scripts = [
    "mlb_hitters_ingest.py",
    "mlb_pitchers_ingest.py",
    "bwar_test.py",
    "bwar_pitching_test.py",
    "dvm_war_merge.py",
    "dvm_war_validation.py",
    "dvm_pipeline.py",
    "test_dvm.py"
]

for script in scripts:
    print(f"\nRunning {script}...", flush=True)

    subprocess.run(
        [sys.executable, script],
        check=True
    )

print("\nDVM PIPELINE COMPLETED SUCCESSFULLY!")
