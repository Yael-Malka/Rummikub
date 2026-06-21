"""Build stage2_v4: merge archived sources, aug train only, write manifest."""

import argparse
import csv
import json
import os
import random
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import yaml
from tqdm import tqdm

os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from rummikub.stage2_classification import augment as aug   # build_compose
from rummikub.common import preprocess_bgr                  # none | clahe_on_l
from rummikub.paths import ARCHIVE_DIR, DATA_DIR, PROJECT_ROOT

# old manifests live under _archive/data/ after the v4 move
_ARCHIVE_DATA = ARCHIVE_DIR / "data"
SOURCES  = [
    _ARCHIVE_DATA / "stage2_classification/manifest.csv",
    _ARCHIVE_DATA / "stage2_vlm/step3/manifest.csv",
]
CONFIG   = Path(__file__).parent / "configs/augmentations_v4.yaml"
OUT_DIR  = DATA_DIR / "stage2_v4"
CROPS    = OUT_DIR / "crops_aug"
OUT_MAN  = OUT_DIR / "manifest_aug.csv"
INFO     = OUT_DIR / "dataset_info.json"
PREPROCESS = "none"
SEED       = 42
NUM_WORKERS = 8

def _resolve_source(filepath: str) -> str:
    """Absolute path to a crop file under _archive/data/."""
    p = Path(str(filepath).replace("\\", "/"))
    parts = p.parts
    if parts and parts[0] in ("datasets", "data"):
        return str((_ARCHIVE_DATA.joinpath(*parts[1:])).resolve())
    return str((PROJECT_ROOT / p).resolve())

def _read_sources() -> list[dict]:
    """Load and merge both source manifests."""
    rows = []
    for man in SOURCES:
        for r in csv.DictReader(open(man, encoding="utf-8")):
            r["_abs"] = _resolve_source(r["filepath"])
            rows.append(r)
    return rows

# 6 and 9 get full rotation so underline matters, not orientation
FULL_ROT_CLASSES = {"6", "9"}

def process_crop(r: dict, n_variants: int, compose, compose_fullrot, rng_seed: int) -> list[dict]:
    """Save original + train aug variants for one crop."""
    img = cv2.imread(r["_abs"])
    if img is None:
        return []

    number, color, source, split = r["number"], r["color"], r["source"], r["split"]
    comp    = compose_fullrot if number in FULL_ROT_CLASSES else compose
    stem    = Path(r["_abs"]).stem
    out_sub = CROPS / number / color
    out_sub.mkdir(parents=True, exist_ok=True)
    out_rows = []

    def _save(im, name):
        dst = out_sub / name
        # optional baked preprocess before save
        cv2.imwrite(str(dst), preprocess_bgr(im, PREPROCESS), [cv2.IMWRITE_JPEG_QUALITY, 95])
        out_rows.append({
            "filepath": str(dst.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "number": number, "color": color, "source": source, "split": split,
        })

    # original (all splits)
    _save(img, f"{stem}.jpg")

    # aug variants: train only
    if split == "train":
        rng = random.Random(rng_seed)
        for i in range(n_variants):
            s = rng.randint(0, 2**31)
            random.seed(s); np.random.seed(s)
            _save(comp(image=img)["image"], f"{stem}__aug{i + 1}.jpg")

    return out_rows

def run_preview(rows, compose, compose_full, n_samples=8, n_cols=8):
    """Sample grid for eyeballing aug + 6/9 full-rotation."""
    train = [r for r in rows if r["split"] == "train"]
    random.seed(SEED)
    # bias sample toward 6/9
    sixnine = [r for r in train if r["number"] in FULL_ROT_CLASSES]
    rest    = [r for r in train if r["number"] not in FULL_ROT_CLASSES]
    samples = (random.sample(sixnine, min(4, len(sixnine))) +
               random.sample(rest, min(n_samples - 4, len(rest))))
    cell = 128
    grid = np.full((len(samples) * cell, n_cols * cell, 3), 200, dtype=np.uint8)
    for ri, r in enumerate(samples):
        img = cv2.imread(r["_abs"])
        if img is None:
            continue
        comp = compose_full if r["number"] in FULL_ROT_CLASSES else compose
        # col 0 original, rest augmented
        grid[ri*cell:(ri+1)*cell, 0:cell] = cv2.resize(preprocess_bgr(img, PREPROCESS), (cell, cell))
        for ci in range(1, n_cols):
            v = preprocess_bgr(comp(image=img)["image"], PREPROCESS)
            grid[ri*cell:(ri+1)*cell, ci*cell:(ci+1)*cell] = cv2.resize(v, (cell, cell))
    out = OUT_DIR / "augmentation_preview.jpg"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), grid, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"Preview -> {out}  (col 0 = original, cols 1+ = augmented; preprocess={PREPROCESS})")

def main(preview_only=False):
    """Build crops_aug/ + manifest_aug.csv + dataset_info.json."""
    import copy
    with open(CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    n_variants = cfg.get("n_variants", 9)
    aug_cfgs   = cfg.get("augmentations", [])
    compose    = aug.build_compose(aug_cfgs)

    # wider rotation pipeline for 6/9
    cfgs_full = copy.deepcopy(aug_cfgs)
    for c in cfgs_full:
        if c.get("function") == "rotate":
            c.setdefault("params", {})
            c["params"]["limit"] = 180
            c["params"]["p"] = 1.0   # always rotate for 6/9
    compose_full = aug.build_compose(cfgs_full)

    rows  = _read_sources()
    train = [r for r in rows if r["split"] == "train"]
    other = [r for r in rows if r["split"] != "train"]
    print(f"Sources: {len(rows)} crops  (train {len(train)} / val+test {len(other)})")
    print(f"n_variants: {n_variants}  -> ~{len(train) * (n_variants + 1)} train images")
    print(f"preprocess (baked): {PREPROCESS}")

    if preview_only:
        run_preview(rows, compose, compose_full)
        return

    if CROPS.exists():
        shutil.rmtree(CROPS)
    CROPS.mkdir(parents=True)

    manifest_rows: list[dict] = []
    rng = random.Random(SEED)
    print(f"\nProcessing with {NUM_WORKERS} threads...")
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as pool:
        futs = {pool.submit(process_crop, r, n_variants, compose, compose_full, rng.randint(0, 2**31)): r
                for r in rows}
        with tqdm(total=len(futs)) as bar:
            for fut in as_completed(futs):
                manifest_rows.extend(fut.result())
                bar.update(1)

    with open(OUT_MAN, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filepath", "number", "color", "source", "split"])
        w.writeheader(); w.writerows(manifest_rows)

    from collections import Counter
    tr = [r for r in manifest_rows if r["split"] == "train"]
    vl = [r for r in manifest_rows if r["split"] == "val"]
    te = [r for r in manifest_rows if r["split"] == "test"]
    nums = Counter(r["number"] for r in tr)
    cols = Counter(r["color"] for r in tr)

    INFO.write_text(json.dumps({
        "preprocess": PREPROCESS,
        "n_variants": n_variants,
        "sources": [str(s.relative_to(PROJECT_ROOT)) for s in SOURCES],
        "counts": {"train": len(tr), "val": len(vl), "test": len(te), "total": len(manifest_rows)},
    }, indent=2), encoding="utf-8")

    print(f"\n{'='*55}\nDATASET v3 BUILT\n{'='*55}")
    print(f"Out dir : {OUT_DIR}")
    print(f"Train   : {len(tr)}   Val: {len(vl)}   Test: {len(te)}   Total: {len(manifest_rows)}")
    print(f"Per-number (train): {dict(sorted(nums.items(), key=lambda x:(len(x[0]),x[0])))}")
    print(f"Per-color  (train): {dict(cols)}")
    print(f"manifest -> {OUT_MAN}")
    print(f"info     -> {INFO}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--config", help="augmentations yaml (default: v4)")
    ap.add_argument("--out", help="output dataset dir name under data/ (default: stage2_v4)")
    ap.add_argument("--preprocess", choices=["none", "clahe_on_l"],
                    help="deterministic bake; 'none' = CLAHE only as a random aug (v4)")
    args = ap.parse_args()

    # CLI overrides for v3 vs v4 builds
    if args.config:
        CONFIG = Path(args.config) if Path(args.config).is_absolute() else Path(__file__).parent / "configs" / args.config
    if args.out:
        OUT_DIR = DATA_DIR / args.out
        CROPS   = OUT_DIR / "crops_aug"
        OUT_MAN = OUT_DIR / "manifest_aug.csv"
        INFO    = OUT_DIR / "dataset_info.json"
    if args.preprocess:
        PREPROCESS = args.preprocess

    main(preview_only=args.preview)
