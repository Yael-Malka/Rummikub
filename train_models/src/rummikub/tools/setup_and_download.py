"""Ask for a Roboflow key, then download all four stage-1 datasets at once."""

import getpass
import subprocess
import sys
import time
from pathlib import Path

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as PROJECT_DIR
RF_DIR      = PROJECT_DIR / "scripts" / "stage1_detection"
LOG_DIR     = PROJECT_DIR / "datasets" / "stage1_detection" / "for-review"

RF_SCRIPTS = [
    RF_DIR / "download_rf_rummikub_solver.py",
    RF_DIR / "download_rf_rummy_tiles_detector.py",
    RF_DIR / "download_rf_rummy_konstantin.py",
    RF_DIR / "download_rf_rummy_mahesha.py",
]

def launch_all(rf_key: str) -> list:
    processes = []

    for script in RF_SCRIPTS:
        name     = Path(script).stem
        log_path = LOG_DIR / f"{name}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log_path, "w")

        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdin=subprocess.PIPE,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=str(PROJECT_DIR),
        )
        # Send key once via stdin, then close so the script's input() returns
        proc.stdin.write((rf_key + "\n").encode())
        proc.stdin.close()

        processes.append((name, proc, log_file, log_path))
        print(f"  Started : {name}  (PID {proc.pid})")

    return processes

def wait_all(processes: list):
    print()
    print("Waiting for all downloads to finish...")
    print("(logs in datasets/stage1_detection/for-review/*.log)")
    print()

    while processes:
        finished = [(n, p, lf, lp) for n, p, lf, lp in processes if p.poll() is not None]

        for entry in finished:
            name, proc, log_file, log_path = entry
            status = "OK" if proc.returncode == 0 else f"FAILED (exit {proc.returncode})"
            print(f"  [{status}] {name}  ->  {log_path}")
            log_file.close()
            processes.remove(entry)

        if processes:
            time.sleep(3)

    print()
    print("All downloads complete. Check datasets/stage1_detection/for-review/ for results.")

def main():
    print("=" * 50)
    print("  Roboflow Dataset Downloader")
    print("=" * 50)
    print()
    print("Get your free key at: app.roboflow.com > Settings > API")
    rf_key = getpass.getpass("Roboflow API key: ").strip()
    print()

    print("Launching downloads in parallel...")
    processes = launch_all(rf_key)
    print()

    wait_all(processes)

if __name__ == "__main__":
    main()
