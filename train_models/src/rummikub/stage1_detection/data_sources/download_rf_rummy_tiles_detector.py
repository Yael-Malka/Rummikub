"""Download ahmet-aksnger/rummy-tiles-detector v3 from Roboflow -> data/stage1_detection/for-review/."""

import sys
import zipfile
import requests
from pathlib import Path

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
WORKSPACE = "ahmet-aksnger"
PROJECT   = "rummy-tiles-detector"
VERSION   = 3
FORMAT    = "yolov8"
DEST      = DATA_DIR / "stage1_detection/for-review/rf-rummy-tiles-detector"

def download(api_key: str):
    """Fetch dataset zip from Roboflow and extract to DEST."""
    DEST.mkdir(parents=True, exist_ok=True)

    print(f"Requesting export URL for {WORKSPACE}/{PROJECT} v{VERSION}...")
    url = f"https://api.roboflow.com/{WORKSPACE}/{PROJECT}/{VERSION}/{FORMAT}?api_key={api_key}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json()

    if "export" not in data or "link" not in data["export"]:
        print(f"ERROR: unexpected response: {data}")
        return

    download_url = data["export"]["link"]
    print(f"Downloading zip...")
    zip_resp = requests.get(download_url, timeout=120, stream=True)
    zip_resp.raise_for_status()

    zip_path = DEST / "dataset.zip"
    with open(zip_path, "wb") as f:
        for chunk in zip_resp.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Extracting...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(DEST)
    zip_path.unlink()

    print(f"Done -> {DEST.resolve()}")

def main():
    """Read API key from stdin and run download."""
    api_key = sys.stdin.readline().strip()
    if not api_key:
        print("ERROR: no API key received on stdin")
        return
    download(api_key)

if __name__ == "__main__":
    main()
