"""Pull labeled crops out of Kaggle + Konstantin into stage2 manifest.csv."""

import cv2
import numpy as np
import json
import csv
import yaml
import random
import re
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from rummikub.common.geometry import (
    CROP_SIZE,
    letterbox_square,
    normalize_color,
    normalize_number,
    padded_crop,
    save_crop,
)
from rummikub.paths import DATA_DIR, PROJECT_ROOT

_STAGE1 = DATA_DIR / "stage1_detection" / "for-review"

KAGGLE_IMAGES_DIR = _STAGE1 / "kaggle-rummikub/images"
KAGGLE_JSON       = _STAGE1 / "kaggle-rummikub/rummikub.json"

KONST_TRAIN_IMAGES = _STAGE1 / "rf-rummy-konstantin/train/images"
KONST_TRAIN_LABELS = _STAGE1 / "rf-rummy-konstantin/train/labels"
KONST_TEST_IMAGES  = _STAGE1 / "rf-rummy-konstantin/test/images"
KONST_TEST_LABELS  = _STAGE1 / "rf-rummy-konstantin/test/labels"
KONST_YAML         = _STAGE1 / "rf-rummy-konstantin/data.yaml"

OUT_CROPS_DIR = DATA_DIR / "stage2/crops"
OUT_MANIFEST  = DATA_DIR / "stage2/manifest.csv"

NUM_WORKERS = 8
SEED        = 42

def collect_kaggle_annotations():
    """
    Returns list of dicts:
      { image_path, x, y, w, h, number, color, source, stem, region_idx }
    """
    with open(KAGGLE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    annotations = []
    for key, entry in data.items():
        filename = entry.get("filename", "")
        img_path = KAGGLE_IMAGES_DIR / filename
        stem = Path(filename).stem
        regions = entry.get("regions", [])
        for idx, region in enumerate(regions):
            sa = region.get("shape_attributes", {})
            ra = region.get("region_attributes", {})
            if sa.get("name") != "rect":
                continue
            number = normalize_number(str(ra.get("number", "")))
            color  = normalize_color(str(ra.get("color", "")))
            if not number or not color:
                continue
            # joker override
            if number == "joker":
                color = "joker"
            annotations.append({
                "image_path": img_path,
                "x": int(sa["x"]),
                "y": int(sa["y"]),
                "w": int(sa["width"]),
                "h": int(sa["height"]),
                "number": number,
                "color":  color,
                "source": "kaggle",
                "stem":   stem,
                "region_idx": idx,
            })
    return annotations

def collect_konst_annotations():
    """
    Parse YOLO-format labels from train + test splits (skip valid — it is empty).
    Returns same dict structure as collect_kaggle_annotations().
    """
    with open(KONST_YAML, "r") as f:
        ydata = yaml.safe_load(f)
    class_names = ydata["names"]  # list[str], e.g. ['10_black', ...]

    def parse_class(class_name: str):
        # e.g. '10_black' -> ('10','black'), 'j_black' -> ('joker','joker')
        parts = class_name.rsplit("_", 1)
        if len(parts) != 2:
            return None, None
        num_raw, col_raw = parts
        if num_raw.lower() == "j":
            return "joker", "joker"
        return num_raw, col_raw.lower()

    splits = [
        (KONST_TRAIN_IMAGES, KONST_TRAIN_LABELS),
        (KONST_TEST_IMAGES,  KONST_TEST_LABELS),
    ]

    annotations = []
    for img_dir, lbl_dir in splits:
        for lbl_file in sorted(lbl_dir.glob("*.txt")):
            stem = lbl_file.stem
            # find matching image (jpg/jpeg/png)
            img_path = None
            for ext in (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"):
                candidate = img_dir / (stem + ext)
                if candidate.exists():
                    img_path = candidate
                    break
            if img_path is None:
                continue

            with open(lbl_file, "r") as f:
                lines = f.read().splitlines()

            for idx, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 5:
                    continue
                class_id = int(parts[0])
                cx = float(parts[1])
                cy = float(parts[2])
                bw = float(parts[3])
                bh = float(parts[4])

                if class_id >= len(class_names):
                    continue
                number, color = parse_class(class_names[class_id])
                if number is None:
                    continue

                annotations.append({
                    "image_path": img_path,
                    "cx": cx, "cy": cy, "bw": bw, "bh": bh,
                    "number": number,
                    "color":  color,
                    "source": "konst",
                    "stem":   stem,
                    "region_idx": idx,
                })
    return annotations

_image_cache: dict = {}
_image_cache_lock = None  # will use ThreadPoolExecutor thread-safety via per-key locking
import threading
_image_cache_lock = threading.Lock()

def load_image(path: Path):
    key = str(path)
    with _image_cache_lock:
        if key in _image_cache:
            return _image_cache[key]
    img = cv2.imread(str(path))
    with _image_cache_lock:
        _image_cache[key] = img
    return img

def process_annotation(ann: dict):
    """
    Extract, letterbox, save one crop.
    Returns (record_dict, skip_reason_or_None).
    record_dict has keys: filepath, number, color, source, stem
    """
    img_path = ann["image_path"]
    if not img_path.exists():
        return None, f"missing_file:{img_path.name}"

    img = load_image(img_path)
    if img is None:
        return None, f"unreadable:{img_path.name}"

    img_h, img_w = img.shape[:2]
    source = ann["source"]

    if source == "kaggle":
        x, y, w, h = ann["x"], ann["y"], ann["w"], ann["h"]
    else:
        # YOLO normalized -> pixel
        cx, cy = ann["cx"] * img_w, ann["cy"] * img_h
        bw, bh = ann["bw"] * img_w, ann["bh"] * img_h
        x = int(round(cx - bw / 2))
        y = int(round(cy - bh / 2))
        w = int(round(bw))
        h = int(round(bh))

    crop = padded_crop(img, x, y, w, h)
    if crop is None:
        return None, f"degenerate_bbox:{img_path.name}@{ann['region_idx']}"

    squared = letterbox_square(crop, CROP_SIZE)

    number = ann["number"]
    color  = ann["color"]
    stem   = ann["stem"]
    idx    = ann["region_idx"]

    # sanitize stem for filesystem
    safe_stem = re.sub(r"[^\w\-]", "_", stem)
    filename  = f"{source}_{safe_stem}_{idx}.jpg"
    out_path  = OUT_CROPS_DIR / number / color / filename

    ok = save_crop(squared, out_path)
    if not ok:
        return None, f"save_failed:{out_path}"

    rel_path = out_path.relative_to(PROJECT_ROOT).as_posix()
    return {
        "filepath": rel_path,
        "number":   number,
        "color":    color,
        "source":   source,
        "stem":     stem,
    }, None

def make_splits(records: list[dict]) -> list[dict]:
    """
    Assign split='train'/'val'/'test' to each record.
    Strategy:
      1. Group image stems within each source.
      2. For each (number, color) stratum, collect the image stems that
         contribute at least one crop of that label.
      3. Shuffle stems per stratum (seeded), then assign 80/10/10.
      4. Any stem not assigned via stratification (because it only appears in
         already-assigned strata) inherits from those assignments; otherwise
         default to 'train'.

    Since one stem can appear in multiple strata, we use majority-vote across
    strata to decide its split, then re-assign deterministically.
    """
    rng = random.Random(SEED)

    # stem -> set of (number,color) pairs
    stem_labels: dict[tuple, set] = defaultdict(set)  # (source,stem) -> strata
    # strata -> list of (source,stem)
    strata_stems: dict[tuple, list] = defaultdict(list)

    seen_stems: set = set()
    for rec in records:
        key = (rec["source"], rec["stem"])
        label = (rec["number"], rec["color"])
        stem_labels[key].add(label)
        if key not in seen_stems:
            seen_stems.add(key)
            strata_stems[label].append(key)  # NOTE: a stem appears once per stratum it contributes to

    # We need: for each unique (source,stem) key, decide its split.
    # Approach: for each stratum shuffle stems, split 80/10/10, record votes.
    stem_votes: dict[tuple, list] = defaultdict(list)

    for label, stems_list in strata_stems.items():
        unique_stems = list(dict.fromkeys(stems_list))  # preserve order, dedup
        rng.shuffle(unique_stems)
        n = len(unique_stems)
        n_val  = max(1, int(round(n * 0.10)))
        n_test = max(1, int(round(n * 0.10)))
        # ensure we don't over-allocate
        if n_val + n_test >= n:
            n_val  = min(n_val,  max(0, n - 1))
            n_test = min(n_test, max(0, n - n_val))
        n_train = n - n_val - n_test

        for i, stem_key in enumerate(unique_stems):
            if i < n_train:
                stem_votes[stem_key].append("train")
            elif i < n_train + n_val:
                stem_votes[stem_key].append("val")
            else:
                stem_votes[stem_key].append("test")

    # Resolve votes by majority; ties -> train
    stem_split: dict[tuple, str] = {}
    for stem_key, votes in stem_votes.items():
        counts = {"train": 0, "val": 0, "test": 0}
        for v in votes:
            counts[v] += 1
        stem_split[stem_key] = max(counts, key=lambda k: (counts[k], k == "train"))

    # Default for any stems that somehow escaped voting
    for rec in records:
        key = (rec["source"], rec["stem"])
        if key not in stem_split:
            stem_split[key] = "train"

    # Assign
    result = []
    for rec in records:
        key = (rec["source"], rec["stem"])
        result.append({**rec, "split": stem_split[key]})
    return result

def main():
    print("=" * 60)
    print("Stage 2 Dataset Builder")
    print("=" * 60)

    # Collect all annotations
    print("\n[1/4] Collecting annotations ...")
    kaggle_anns = collect_kaggle_annotations()
    konst_anns  = collect_konst_annotations()
    print(f"  Kaggle annotations : {len(kaggle_anns)}")
    print(f"  Konst  annotations : {len(konst_anns)}")
    all_anns = kaggle_anns + konst_anns
    print(f"  Total  annotations : {len(all_anns)}")

    # Extract crops in parallel
    print(f"\n[2/4] Extracting crops with {NUM_WORKERS} threads ...")
    records   = []
    skipped   = []

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(process_annotation, ann): ann for ann in all_anns}
        done = 0
        for future in as_completed(futures):
            rec, skip_reason = future.result()
            done += 1
            if done % 500 == 0:
                print(f"    ... {done}/{len(all_anns)} processed")
            if rec is not None:
                records.append(rec)
            else:
                skipped.append(skip_reason)

    print(f"  Crops saved   : {len(records)}")
    print(f"  Crops skipped : {len(skipped)}")

    # Assign splits
    print("\n[3/4] Assigning train/val/test splits ...")
    records = make_splits(records)

    # Write manifest
    print(f"\n[4/4] Writing manifest to {OUT_MANIFEST} ...")
    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["filepath", "number", "color", "source", "split"]
    with open(OUT_MANIFEST, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    print(f"  Manifest rows : {len(records)}")

    # Summary

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total = len(records)
    print(f"\nTotal crops extracted : {total}")

    # Per-source
    src_counts: dict = defaultdict(int)
    for r in records:
        src_counts[r["source"]] += 1
    print("\nPer-source counts:")
    for src in sorted(src_counts):
        print(f"  {src:10s}: {src_counts[src]}")

    # Per-split
    split_counts: dict = defaultdict(int)
    for r in records:
        split_counts[r["split"]] += 1
    print("\nPer-split counts:")
    for sp in ["train", "val", "test"]:
        print(f"  {sp:6s}: {split_counts[sp]}")

    # Per-number
    num_counts: dict = defaultdict(int)
    for r in records:
        num_counts[r["number"]] += 1
    print("\nPer-number counts:")
    num_order = [str(i) for i in range(1, 14)] + ["joker"]
    for n in num_order:
        print(f"  {n:6s}: {num_counts.get(n, 0)}")

    # Per-color
    col_counts: dict = defaultdict(int)
    for r in records:
        col_counts[r["color"]] += 1
    print("\nPer-color counts:")
    for c in ["black", "blue", "orange", "red", "joker"]:
        print(f"  {c:8s}: {col_counts.get(c, 0)}")

    # Skipped
    if skipped:
        skip_groups: dict = defaultdict(int)
        for s in skipped:
            reason = s.split(":")[0]
            skip_groups[reason] += 1
        print("\nSkipped breakdown:")
        for reason, cnt in sorted(skip_groups.items()):
            print(f"  {reason}: {cnt}")
        # Show unique filenames skipped
        skip_files = list(dict.fromkeys(s for s in skipped))[:20]
        print(f"  (first {len(skip_files)} skip messages: {skip_files})")
    else:
        print("\nNo crops skipped.")

    print("\nDone.")

if __name__ == "__main__":
    main()
