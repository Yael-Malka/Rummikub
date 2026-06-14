"""Offline aug for stage-2 train crops (--preview shows a sample grid first)."""

import argparse
import csv
import os
import random
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import albumentations as A
import cv2
import numpy as np
import yaml
from tqdm import tqdm

os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from rummikub.paths import DATA_DIR

STAGE2_DIR = DATA_DIR / "stage2_classification"
MANIFEST   = STAGE2_DIR / "manifest.csv"
CONFIG     = Path(__file__).parent / "configs/augmentations.yaml"
OUT_DIR    = STAGE2_DIR / "crops_aug"
OUT_MAN    = STAGE2_DIR / "manifest_aug.csv"
SEED       = 42
NUM_WORKERS = 8

def _p(params, key, default):
    """Return a list value as tuple, other values as-is, with a fallback."""
    v = params.get(key, default)
    return tuple(v) if isinstance(v, list) else v

def build_compose(aug_configs: list) -> A.Compose:
    """Build a single A.Compose from the YAML augmentation list."""
    transforms = []
    for cfg in aug_configs:
        fn = cfg["function"]
        p  = cfg.get("params") or {}

        if fn == "rotate":
            transforms.append(A.Rotate(
                limit=_p(p, "limit", 20),
                border_mode=p.get("border_mode", 0),
                value=_p(p, "value", [114, 114, 114]),
                p=p.get("p", 0.7),
            ))
        elif fn == "shift_scale":
            transforms.append(A.ShiftScaleRotate(
                shift_limit=p.get("shift_limit", 0.10),
                scale_limit=p.get("scale_limit", 0.15),
                rotate_limit=p.get("rotate_limit", 0),
                border_mode=p.get("border_mode", 0),
                value=_p(p, "value", [114, 114, 114]),
                p=p.get("p", 0.6),
            ))
        elif fn == "perspective":
            transforms.append(A.Perspective(
                scale=_p(p, "scale", (0.02, 0.05)),
                p=p.get("p", 0.4),
            ))
        elif fn == "shear":
            transforms.append(A.Affine(
                shear=_p(p, "shear", (-5, 5)),
                p=p.get("p", 0.3),
            ))
        elif fn == "brightness_contrast":
            transforms.append(A.RandomBrightnessContrast(
                brightness_limit=p.get("brightness_limit", 0.25),
                contrast_limit=p.get("contrast_limit", 0.20),
                p=p.get("p", 0.7),
            ))
        elif fn == "saturation_only":
            # HueSaturationValue with hue=0 and val=0 -> saturation shift only
            transforms.append(A.HueSaturationValue(
                hue_shift_limit=0,
                sat_shift_limit=p.get("sat_shift_limit", 20),
                val_shift_limit=0,
                p=p.get("p", 0.5),
            ))
        elif fn == "downscale":
            sr = _p(p, "scale_range", (0.30, 0.70))
            transforms.append(A.Downscale(
                scale_range=sr,
                p=p.get("p", 0.5),
            ))
        elif fn == "blur":
            transforms.append(A.GaussianBlur(
                blur_limit=_p(p, "blur_limit", (3, 5)),
                p=p.get("p", 0.4),
            ))
        elif fn == "noise":
            transforms.append(A.GaussNoise(
                var_limit=_p(p, "var_limit", (5.0, 25.0)),
                p=p.get("p", 0.4),
            ))
        elif fn == "jpeg_compression":
            ql = p.get("quality_lower", 50)
            qu = p.get("quality_upper", 90)
            transforms.append(A.ImageCompression(
                quality_range=(ql, qu),
                p=p.get("p", 0.4),
            ))
        elif fn == "coarse_dropout":
            transforms.append(A.CoarseDropout(
                max_holes=p.get("max_holes", 3),
                max_height=p.get("max_height", 16),
                max_width=p.get("max_width", 16),
                min_holes=p.get("min_holes", 1),
                min_height=p.get("min_height", 6),
                min_width=p.get("min_width", 6),
                fill_value=p.get("fill_value", 114),
                p=p.get("p", 0.3),
            ))
        elif fn == "grid_distortion":
            transforms.append(A.GridDistortion(
                num_steps=p.get("num_steps", 5),
                distort_limit=p.get("distort_limit", 0.2),
                p=p.get("p", 0.3),
            ))
        elif fn == "shadow":
            transforms.append(A.RandomShadow(
                shadow_roi=_p(p, "shadow_roi", (0.0, 0.0, 1.0, 1.0)),
                num_shadows_lower=p.get("num_shadows_lower", 1),
                num_shadows_upper=p.get("num_shadows_upper", 2),
                shadow_dimension=p.get("shadow_dimension", 4),
                p=p.get("p", 0.25),
            ))
        elif fn == "sharpen":
            # Unsharp masking (doc §4.6): sharpen digit edges. As a random aug
            # (not a deterministic bake) the model sees both sharp and soft views.
            transforms.append(A.Sharpen(
                alpha=_p(p, "alpha", (0.2, 0.5)),
                lightness=_p(p, "lightness", (0.5, 1.0)),
                p=p.get("p", 0.3),
            ))
        elif fn == "clahe":
            # CLAHE as a RANDOM augmentation (doc §4.5.1 recommendation) rather than
            # a deterministic bake -> contrast robustness with no inference cost.
            # A.CLAHE applies on the luminance only, so colour is preserved.
            transforms.append(A.CLAHE(
                clip_limit=_p(p, "clip_limit", (1.0, 3.0)),
                tile_grid_size=tuple(_p(p, "tile_grid_size", (8, 8))),
                p=p.get("p", 0.3),
            ))
        else:
            raise ValueError(f"Unknown augmentation function: '{fn}'")

    return A.Compose(transforms)

def augment_crop(
    src_path: str,
    number: str,
    color: str,
    source: str,
    n_variants: int,
    compose: A.Compose,
    rng_seed: int,
) -> list[dict]:
    """Augment one crop N times + copy the original. Returns manifest rows."""
    img = cv2.imread(src_path)
    if img is None:
        return []

    stem   = Path(src_path).stem
    out_sub = OUT_DIR / number / color
    out_sub.mkdir(parents=True, exist_ok=True)

    rows = []

    # Copy the original.
    orig_dst = out_sub / f"{stem}.jpg"
    cv2.imwrite(str(orig_dst), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    rows.append({
        "filepath": str(orig_dst.relative_to(ROOT)).replace("\\", "/"),
        "number": number, "color": color, "source": source, "split": "train",
    })

    # Generate N augmented variants.
    rng = random.Random(rng_seed)
    for i in range(n_variants):
        seed_i = rng.randint(0, 2**31)
        random.seed(seed_i)
        np.random.seed(seed_i)
        aug = compose(image=img)["image"]
        dst = out_sub / f"{stem}__aug{i + 1}.jpg"
        cv2.imwrite(str(dst), aug, [cv2.IMWRITE_JPEG_QUALITY, 95])
        rows.append({
            "filepath": str(dst.relative_to(ROOT)).replace("\\", "/"),
            "number": number, "color": color, "source": source, "split": "train",
        })

    return rows

def run_preview(rows: list[dict], compose: A.Compose, n_samples: int = 6, n_cols: int = 8):
    """Save a grid of n_samples crops × (original + n_cols-1 variants) to disk."""
    train_rows = [r for r in rows if r["split"] == "train"]
    random.seed(SEED)
    samples = random.sample(train_rows, min(n_samples, len(train_rows)))

    cell = 128
    grid_w = n_cols * cell
    grid_h = n_samples * cell
    grid   = np.full((grid_h, grid_w, 3), 200, dtype=np.uint8)

    for row_idx, r in enumerate(samples):
        img = cv2.imread(r["filepath"])
        if img is None:
            continue
        # Column 0: original
        grid[row_idx*cell:(row_idx+1)*cell, 0:cell] = img
        # Columns 1..n_cols-1: augmented variants
        for col_idx in range(1, n_cols):
            aug = compose(image=img)["image"]
            grid[row_idx*cell:(row_idx+1)*cell, col_idx*cell:(col_idx+1)*cell] = aug

    out = STAGE2_DIR / "augmentation_preview.jpg"
    cv2.imwrite(str(out), grid, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"Preview saved -> {out}")
    print(f"  {n_samples} rows (one crop each) × {n_cols} columns "
          f"(col 0 = original, cols 1-{n_cols-1} = augmented variants)")
    print("  Check: 6 vs 9 distinguishable; no color crossings; "
          "downscaled samples look like real detector crops.")

def main(preview_only: bool = False):
    with open(CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    n_variants  = cfg.get("n_variants", 8)
    aug_configs = cfg.get("augmentations", [])
    compose     = build_compose(aug_configs)

    rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8")))
    train_rows = [r for r in rows if r["split"] == "train"]
    other_rows = [r for r in rows if r["split"] != "train"]

    print(f"Manifest      : {len(rows)} total  "
          f"(train {len(train_rows)} / other {len(other_rows)})")
    print(f"n_variants    : {n_variants}  "
          f"-> ~{len(train_rows) * (n_variants + 1)} train images after aug")

    if preview_only:
        print("\nRunning preview mode...")
        run_preview(rows, compose)
        return

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    print(f"\nAugmenting train split with {NUM_WORKERS} threads...")
    manifest_rows: list[dict] = []
    rng = random.Random(SEED)

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as pool:
        futures = {
            pool.submit(
                augment_crop,
                r["filepath"], r["number"], r["color"], r["source"],
                n_variants, compose, rng.randint(0, 2**31),
            ): r
            for r in train_rows
        }
        with tqdm(total=len(futures), desc="train crops") as bar:
            for fut in as_completed(futures):
                manifest_rows.extend(fut.result())
                bar.update(1)

    # Pass val/test through (copy originals, no augmentation).
    print("Copying val/test crops through untouched...")
    for r in tqdm(other_rows, desc="val/test"):
        src = Path(r["filepath"])
        dst = OUT_DIR / r["number"] / r["color"] / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        manifest_rows.append({
            "filepath": str(dst.relative_to(ROOT)).replace("\\", "/"),
            "number": r["number"], "color": r["color"],
            "source": r["source"], "split": r["split"],
        })

    # Write manifest_aug.csv
    with open(OUT_MAN, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filepath","number","color","source","split"])
        w.writeheader()
        w.writerows(manifest_rows)

    # Summary
    from collections import Counter
    tr = [r for r in manifest_rows if r["split"] == "train"]
    vl = [r for r in manifest_rows if r["split"] == "val"]
    te = [r for r in manifest_rows if r["split"] == "test"]
    nums = Counter(r["number"] for r in tr)
    cols = Counter(r["color"] for r in tr)

    print(f"\n{'='*55}")
    print(f"AUGMENTATION COMPLETE")
    print(f"{'='*55}")
    print(f"Output dir    : {OUT_DIR}")
    print(f"manifest_aug  : {OUT_MAN}")
    print(f"\nTrain images  : {len(tr)}  "
          f"(orig {len(train_rows)} × {n_variants + 1} variants incl. original)")
    print(f"Val images    : {len(vl)}  (unchanged)")
    print(f"Test images   : {len(te)}  (unchanged)")
    print(f"\nTrain per-number : {dict(sorted(nums.items(), key=lambda x:(len(x[0]),x[0])))}")
    print(f"Train per-color  : {dict(cols)}")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--preview", action="store_true",
        help="Save a sample grid to augmentation_preview.jpg and exit (no full aug).",
    )
    args = parser.parse_args()
    main(preview_only=args.preview)
