"""Run the whole pipeline: fetch -> analyze -> drivers.

This is what the scheduled task calls each trading day after the close.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
PY = sys.executable  # the venv's python when invoked as ./venv/bin/python run_all.py

STEPS = ["fetch.py", "analyze.py", "drivers.py"]


def main():
    for step in STEPS:
        print(f"\n=== {step} ===", flush=True)
        r = subprocess.run([PY, str(HERE / step)], cwd=HERE)
        if r.returncode != 0:
            print(f"FAILED at {step}", file=sys.stderr)
            sys.exit(r.returncode)
    print("\nPipeline complete. data/nasdaq.json is up to date.")


if __name__ == "__main__":
    main()
