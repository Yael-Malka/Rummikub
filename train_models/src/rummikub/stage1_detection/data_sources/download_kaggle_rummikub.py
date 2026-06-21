"""Download sverrela/rummikub from Kaggle. Needs ~/.kaggle/kaggle.json."""

import os
import zipfile
from pathlib import Path

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
DEST = DATA_DIR / "stage1_detection/for-review/kaggle-rummikub"

def main():
    """Download sverrela/rummikub from Kaggle into DEST."""
    DEST.mkdir(parents=True, exist_ok=True)

    try:
        import kaggle
    except ImportError:
        print("ERROR: run  pip install kaggle")
        return

    cred = Path.home() / ".kaggle" / "kaggle.json"
    if not cred.exists():
        print("ERROR: Kaggle credentials not found.")
        print("  1. Go to kaggle.com > Account > API > Create New Token")
        print(f"  2. Save the downloaded kaggle.json to: {cred}")
        return

    print("Downloading sverrela/rummikub from Kaggle...")
    os.system(f'kaggle datasets download -d sverrela/rummikub -p "{DEST}" --unzip')
    print(f"Done -> {DEST.resolve()}")

if __name__ == "__main__":
    main()
