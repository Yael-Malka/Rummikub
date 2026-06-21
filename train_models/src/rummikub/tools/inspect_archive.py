"""List files in archive.zip and print a summary of rummikub.json."""

import zipfile
import json
import collections
from pathlib import Path

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
def main():
    """Peek at archive.zip contents and rummikub.json shape."""
    archive_path = ROOT / "archive.zip"

    with zipfile.ZipFile(archive_path) as z:
        names = z.namelist()
        print(f"Total files: {len(names)}")

        tops = set()
        for n in names:
            tops.add(n.split("/")[0])
        print("Top-level entries:", sorted(tops))

        exts = collections.Counter()
        for n in names:
            filename = n.split("/")[-1]
            if "." in filename:
                exts[filename.rsplit(".", 1)[-1].lower()] += 1
            else:
                exts["(dir)"] += 1
        print("Extensions:", dict(exts))

        print()
        print("First 10 image entries:")
        for n in names[:10]:
            print(" ", n)

        print()
        print("=== rummikub.json structure ===")
        with z.open("rummikub.json") as f:
            data = json.load(f)

        print("Top-level keys:", list(data.keys()))
        print()

        if "annotations" in data:
            print("Format: COCO")
            print(f"  images:      {len(data['images'])}")
            print(f"  annotations: {len(data['annotations'])}")
            print(f"  categories:  {data['categories']}")
            print()
            print("Sample image entry:")
            print(json.dumps(data["images"][0], indent=2))
            print()
            print("Sample annotation entry:")
            print(json.dumps(data["annotations"][0], indent=2))
        elif isinstance(data, list):
            print(f"Format: list of {len(data)} items")
            print("First item:")
            print(json.dumps(data[0], indent=2))
        else:
            print("Format: dict with keys:", list(data.keys()))
            for k, v in list(data.items())[:3]:
                print(f"\n  {k}:")
                print("   ", str(v)[:300])

if __name__ == "__main__":
    main()
