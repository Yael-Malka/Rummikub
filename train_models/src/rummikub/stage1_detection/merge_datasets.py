"""Flatten reviewed stage-1 sources into before-preparation/ (single tile class)."""

import io
import json
import shutil
from pathlib import Path
from PIL import Image

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
REVIEW_DIR = DATA_DIR / "stage1_detection/for-review"
OUTPUT_DIR = DATA_DIR / "stage1_detection/before-preparation"
IMG_EXTS   = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}

def ensure_clean(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)

def save_label(dest: Path, lines: list[str]):
    dest.write_text("\n".join(lines), encoding="utf-8")

def copy_image_as_jpg(src: Path, dest: Path):
    if src.suffix.lower() in (".jpg", ".jpeg"):
        shutil.copy2(src, dest)
    else:
        Image.open(src).convert("RGB").save(dest, "JPEG", quality=95)

def merge_kaggle(img_out: Path, lbl_out: Path) -> tuple[int, int]:
    base  = REVIEW_DIR / "kaggle-rummikub"
    imgs  = base / "images"
    json_path = base / "rummikub.json"

    if not json_path.exists():
        print("  [kaggle] rummikub.json not found, skipping")
        return 0, 0

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    written = skipped = 0

    for entry in data.values():
        filename = entry["filename"]
        src_img  = imgs / filename
        if not src_img.exists():
            skipped += 1
            continue

        img   = Image.open(src_img).convert("RGB")
        iw, ih = img.size

        stem    = Path(filename).stem
        out_img = img_out / f"kaggle__{stem}.jpg"
        out_lbl = lbl_out / f"kaggle__{stem}.txt"

        img.save(out_img, "JPEG", quality=95)

        lines = []
        for region in entry.get("regions", []):
            sa = region.get("shape_attributes", {})
            if sa.get("name") != "rect":
                continue
            x, y, w, h = sa["x"], sa["y"], sa["width"], sa["height"]
            cx = (x + w / 2) / iw
            cy = (y + h / 2) / ih
            nw = w / iw
            nh = h / ih
            cx = max(0.0, min(1.0, cx))
            cy = max(0.0, min(1.0, cy))
            nw = max(0.0, min(1.0, nw))
            nh = max(0.0, min(1.0, nh))
            lines.append(f"0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        save_label(out_lbl, lines)
        written += 1

    return written, skipped

def merge_roboflow(name: str, slug: str, img_out: Path, lbl_out: Path) -> tuple[int, int]:
    base = REVIEW_DIR / name

    if not base.exists():
        print(f"  [{slug}] directory not found, skipping")
        return 0, 0

    written = skipped = 0

    # Collect all image files across all splits (train / valid / test)
    for img_path in base.rglob("*"):
        if img_path.suffix.lower() not in IMG_EXTS:
            continue
        if img_path.stat().st_size == 0:
            skipped += 1
            continue

        # Find matching label: same stem, sibling labels/ dir
        lbl_path = img_path.parent.parent / "labels" / (img_path.stem + ".txt")

        stem    = img_path.stem
        out_img = img_out / f"{slug}__{stem}.jpg"
        out_lbl = lbl_out / f"{slug}__{stem}.txt"

        copy_image_as_jpg(img_path, out_img)

        if lbl_path.exists():
            # Remap every class id to 0
            lines = []
            for raw in lbl_path.read_text(encoding="utf-8").splitlines():
                parts = raw.strip().split()
                if len(parts) == 5:
                    lines.append(f"0 {parts[1]} {parts[2]} {parts[3]} {parts[4]}")
            save_label(out_lbl, lines)
        else:
            # No label file means no annotations -> write empty label
            save_label(out_lbl, [])

        written += 1

    return written, skipped

def main():
    img_out = OUTPUT_DIR / "images"
    lbl_out = OUTPUT_DIR / "labels"

    ensure_clean(img_out)
    ensure_clean(lbl_out)

    print("Merging datasets into datasets/stage1_detection/before-preparation/")
    print()

    total_written = total_skipped = 0

    print("[1/3] kaggle-rummikub  (VIA JSON -> YOLO)")
    w, s = merge_kaggle(img_out, lbl_out)
    print(f"      {w} written, {s} skipped")
    total_written += w; total_skipped += s

    print("[2/3] rf-rummikub-solver  (YOLO 16-class -> class 0)")
    w, s = merge_roboflow("rf-rummikub-solver", "solver", img_out, lbl_out)
    print(f"      {w} written, {s} skipped")
    total_written += w; total_skipped += s

    print("[3/3] rf-rummy-konstantin  (YOLO 54-class -> class 0)")
    w, s = merge_roboflow("rf-rummy-konstantin", "konst", img_out, lbl_out)
    print(f"      {w} written, {s} skipped")
    total_written += w; total_skipped += s

    print()
    print(f"Total images : {total_written}")
    print(f"Total skipped: {total_skipped}")
    print(f"Output       : {OUTPUT_DIR.resolve()}")

    # Sanity check: every image has a label
    imgs  = set(p.stem for p in img_out.glob("*"))
    lbls  = set(p.stem for p in lbl_out.glob("*.txt"))
    unmatched = imgs.symmetric_difference(lbls)
    if unmatched:
        print(f"WARNING: {len(unmatched)} unmatched image/label pairs: {list(unmatched)[:5]}")
    else:
        print("Sanity check passed: every image has a matching label file.")

if __name__ == "__main__":
    main()
