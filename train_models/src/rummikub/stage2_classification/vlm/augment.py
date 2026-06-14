"""Augment + split the step3 VLM dataset (80/10/10)."""

import csv
import importlib.util
import os
import random
import re
import shutil
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import yaml
from tqdm import tqdm

os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
from rummikub.stage2_classification.augment import build_compose
STEP3_DIR = DATA_DIR / "stage2_vlm/step3"
AUG_CFG   = Path(__file__).parent.parent / "configs/augmentations.yaml"
OUT_DIR   = DATA_DIR / "stage2_vlm/crops_aug"
OUT_MAN   = DATA_DIR / "stage2_vlm/manifest_aug.csv"
SEED      = 42
NUM_WORKERS = 8
SKIP_DIRS = {"review"}

def scan_step3():
    """Walk step3/<number>/<color>/ and return list of row dicts."""
    rows = []
    valid_nums = {str(i) for i in range(1, 14)} | {"joker"}
    valid_cols = {"black", "blue", "orange", "red", "joker"}

    for num_dir in sorted(STEP3_DIR.iterdir()):
        if not num_dir.is_dir() or num_dir.name in SKIP_DIRS:
            continue
        num = num_dir.name
        if num not in valid_nums:
            continue
        for col_dir in sorted(num_dir.iterdir()):
            if not col_dir.is_dir() or col_dir.name in SKIP_DIRS:
                continue
            col = col_dir.name
            if col not in valid_cols:
                continue          # skip "unknown" dirs
            for f in sorted(col_dir.glob("*.jpg")):
                rows.append({
                    "filepath": f.relative_to(ROOT).as_posix(),
                    "number": num, "color": col,
                    "source": "vlm",
                    "stem": f.stem,
                })
    return rows

def assign_splits(rows, seed=SEED):
    """Group-stratified 80/10/10 split by stem (no leakage)."""
    rng = random.Random(seed)

    # Group stems per (number, color) stratum
    strata: dict[tuple, list] = defaultdict(list)
    seen = set()
    for r in rows:
        key = (r["number"], r["color"])
        if r["stem"] not in seen:
            strata[key].append(r["stem"])
            seen.add(r["stem"])

    stem_split: dict[str, str] = {}
    for stems in strata.values():
        unique = list(dict.fromkeys(stems))
        rng.shuffle(unique)
        n = len(unique)
        n_val  = max(1, round(n * 0.10))
        n_test = max(1, round(n * 0.10))
        if n_val + n_test >= n:
            n_val  = min(n_val,  max(0, n - 1))
            n_test = min(n_test, max(0, n - n_val))
        for i, s in enumerate(unique):
            if s not in stem_split:   # first-assignment wins on multi-stratum stems
                if i < n - n_val - n_test:
                    stem_split[s] = "train"
                elif i < n - n_test:
                    stem_split[s] = "val"
                else:
                    stem_split[s] = "test"

    return [{**r, "split": stem_split.get(r["stem"], "train")} for r in rows]

def augment_one(src_path, number, color, stem, n_variants, compose, rng_seed):
    img = cv2.imread(src_path)
    if img is None:
        return []

    out_sub = OUT_DIR / number / color
    out_sub.mkdir(parents=True, exist_ok=True)

    rng = random.Random(rng_seed)
    rows = []

    # Copy original
    orig_dst = out_sub / f"{stem}.jpg"
    cv2.imwrite(str(orig_dst), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    rows.append({
        "filepath": orig_dst.relative_to(ROOT).as_posix(),
        "number": number, "color": color, "source": "vlm", "split": "train",
    })

    # N augmented variants
    for i in range(n_variants):
        seed_i = rng.randint(0, 2**31)
        random.seed(seed_i); np.random.seed(seed_i)
        aug = compose(image=img)["image"]
        dst = out_sub / f"{stem}__aug{i+1}.jpg"
        cv2.imwrite(str(dst), aug, [cv2.IMWRITE_JPEG_QUALITY, 95])
        rows.append({
            "filepath": dst.relative_to(ROOT).as_posix(),
            "number": number, "color": color, "source": "vlm", "split": "train",
        })
    return rows

def copy_one(src_path, number, color, stem, split):
    dst = OUT_DIR / number / color / Path(src_path).name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / src_path, dst)
    return {
        "filepath": dst.relative_to(ROOT).as_posix(),
        "number": number, "color": color, "source": "vlm", "split": split,
    }

def main():
    with open(AUG_CFG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    n_variants = cfg.get("n_variants", 8)
    compose    = build_compose(cfg.get("augmentations", []))

    rows = scan_step3()
    rows = assign_splits(rows)

    train = [r for r in rows if r["split"] == "train"]
    other = [r for r in rows if r["split"] != "train"]

    print(f"Dataset: {len(rows)} tiles  "
          f"(train {len(train)} / val {sum(1 for r in other if r['split']=='val')} "
          f"/ test {sum(1 for r in other if r['split']=='test')})")
    print(f"n_variants: {n_variants}  "
          f"-> ~{len(train)*(n_variants+1)} train images after aug")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    manifest_rows: list[dict] = []
    rng = random.Random(SEED)

    print(f"\nAugmenting train split ({NUM_WORKERS} threads) ...")
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as pool:
        futures = {
            pool.submit(
                augment_one,
                str(ROOT / r["filepath"]), r["number"], r["color"], r["stem"],
                n_variants, compose, rng.randint(0, 2**31),
            ): r for r in train
        }
        with tqdm(total=len(futures), desc="train") as bar:
            for fut in as_completed(futures):
                manifest_rows.extend(fut.result())
                bar.update(1)

    print("Copying val/test ...")
    for r in tqdm(other, desc="val/test"):
        manifest_rows.append(copy_one(r["filepath"], r["number"], r["color"],
                                       r["stem"], r["split"]))

    with open(OUT_MAN, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filepath","number","color","source","split"])
        w.writeheader(); w.writerows(manifest_rows)

    # Summary
    from collections import Counter
    tr = [r for r in manifest_rows if r["split"] == "train"]
    vl = [r for r in manifest_rows if r["split"] == "val"]
    te = [r for r in manifest_rows if r["split"] == "test"]
    nums = Counter(r["number"] for r in tr)
    cols = Counter(r["color"]  for r in tr)

    print(f"\n{'='*55}")
    print(f"AUGMENTATION COMPLETE")
    print(f"{'='*55}")
    print(f"Train : {len(tr)}  (orig {len(train)} x {n_variants+1} variants)")
    print(f"Val   : {len(vl)}")
    print(f"Test  : {len(te)}")
    print(f"Per number (train): {dict(sorted(nums.items(), key=lambda x:(len(x[0]),x[0])))}")
    print(f"Per color  (train): {dict(cols)}")
    print(f"\nManifest -> {OUT_MAN}")
    print(f"{'='*55}")

if __name__ == "__main__":
    main()
