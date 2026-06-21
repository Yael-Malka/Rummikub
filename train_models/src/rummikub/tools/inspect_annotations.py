"""Print stats from rummikub.json — counts, numbers, colors, missing fields."""

import zipfile
import json
import collections
from pathlib import Path

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
def main():
    """Print annotation stats from archive.zip / rummikub.json."""
    with zipfile.ZipFile(ROOT / "archive.zip") as z:
        with z.open("rummikub.json") as f:
            data = json.load(f)

    total_images = len(data)
    total_annotations = 0
    numbers = collections.Counter()
    colors = collections.Counter()
    annotations_per_image = []
    missing_attrs = 0
    images_no_regions = 0

    for key, entry in data.items():
        regions = entry.get("regions", [])
        if not regions:
            images_no_regions += 1
        annotations_per_image.append(len(regions))
        total_annotations += len(regions)

        for region in regions:
            attrs = region.get("region_attributes", {})
            num = attrs.get("number", "").strip()
            col = attrs.get("color", "").strip()
            if not num or not col:
                missing_attrs += 1
            numbers[num] += 1
            colors[col] += 1

    print(f"Total images:      {total_images}")
    print(f"Total annotations: {total_annotations}")
    print(f"Images no regions: {images_no_regions}")
    print(f"Missing attrs:     {missing_attrs}")
    print(f"Avg tiles/image:   {total_annotations / total_images:.1f}")
    print(f"Min tiles/image:   {min(annotations_per_image)}")
    print(f"Max tiles/image:   {max(annotations_per_image)}")

    print()
    print("Unique numbers:", sorted(numbers.keys()))
    print("Number counts:")
    for k in sorted(numbers.keys()):
        print(f"  {k!r:10s}: {numbers[k]}")

    print()
    print("Unique colors:", sorted(colors.keys()))
    print("Color counts:")
    for k in sorted(colors.keys()):
        print(f"  {k!r:12s}: {colors[k]}")

    print()
    sample_key = next(iter(data))
    entry = data[sample_key]
    print("Sample entry key:", sample_key)
    print("  filename:", entry["filename"])
    print("  regions count:", len(entry["regions"]))
    if entry["regions"]:
        r = entry["regions"][0]
        print("  first region shape_attributes:", r["shape_attributes"])
        print("  first region region_attributes:", r["region_attributes"])

if __name__ == "__main__":
    main()
