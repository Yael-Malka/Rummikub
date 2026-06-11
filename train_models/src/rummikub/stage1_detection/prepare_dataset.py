"""Letterbox to 640², split 80/10/10 by source image, emit ready/ + data.yaml."""

import random
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import yaml
from tqdm import tqdm

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
SOURCE_DIR  = DATA_DIR / "stage1_detection/augmented"
OUTPUT_DIR  = DATA_DIR / "stage1_detection/ready"
TARGET_SIZE = 640
TRAIN_RATIO = 0.80
VAL_RATIO   = 0.10
SEED        = 42
NUM_WORKERS = 8
IMG_EXTS    = {".jpg", ".jpeg", ".png"}

# Strips  __aug{N}_{function}  suffix added by augment_dataset.py
_AUG_RE = re.compile(r"__aug\d+_\w+$")

def original_stem(stem: str) -> str:
    return _AUG_RE.sub("", stem)

def letterbox_and_adjust(
    img_path: Path,
    lbl_path: Path,
    out_img: Path,
    out_lbl: Path,
) -> bool:
    img = cv2.imread(str(img_path))
    if img is None:
        return False

    h, w  = img.shape[:2]
    scale = min(TARGET_SIZE / w, TARGET_SIZE / h)
    nw    = int(w * scale)
    nh    = int(h * scale)
    pad_l = (TARGET_SIZE - nw) // 2
    pad_t = (TARGET_SIZE - nh) // 2

    canvas = np.full((TARGET_SIZE, TARGET_SIZE, 3), 114, dtype=np.uint8)
    canvas[pad_t:pad_t + nh, pad_l:pad_l + nw] = cv2.resize(
        img, (nw, nh), interpolation=cv2.INTER_LINEAR
    )
    cv2.imwrite(str(out_img), canvas, [cv2.IMWRITE_JPEG_QUALITY, 95])

    lines = []
    if lbl_path.exists():
        for raw in lbl_path.read_text(encoding="utf-8").splitlines():
            parts = raw.strip().split()
            if len(parts) != 5:
                continue
            cls = parts[0]
            cx_n, cy_n, bw_n, bh_n = map(float, parts[1:])
            new_cx = (cx_n * nw + pad_l) / TARGET_SIZE
            new_cy = (cy_n * nh + pad_t) / TARGET_SIZE
            new_bw = bw_n * nw / TARGET_SIZE
            new_bh = bh_n * nh / TARGET_SIZE
            if new_bw < 0.001 or new_bh < 0.001:
                continue
            lines.append(
                f"{cls} "
                f"{max(0.0, min(1.0, new_cx)):.6f} "
                f"{max(0.0, min(1.0, new_cy)):.6f} "
                f"{max(0.0, min(1.0, new_bw)):.6f} "
                f"{max(0.0, min(1.0, new_bh)):.6f}"
            )

    out_lbl.write_text("\n".join(lines), encoding="utf-8")
    return True

def main():
    src_img_dir = SOURCE_DIR / "images"
    src_lbl_dir = SOURCE_DIR / "labels"

    all_imgs = sorted(
        p for p in src_img_dir.glob("*") if p.suffix.lower() in IMG_EXTS
    )
    print(f"Source images : {len(all_imgs)}")

    by_orig: dict[str, list[Path]] = {}
    for p in all_imgs:
        by_orig.setdefault(original_stem(p.stem), []).append(p)

    orig_keys = sorted(by_orig)
    random.seed(SEED)
    random.shuffle(orig_keys)

    n       = len(orig_keys)
    n_train = int(n * TRAIN_RATIO)
    n_val   = int(n * VAL_RATIO)

    split_for: dict[str, str] = {}
    for k in orig_keys[:n_train]:
        split_for[k] = "train"
    for k in orig_keys[n_train:n_train + n_val]:
        split_for[k] = "val"
    for k in orig_keys[n_train + n_val:]:
        split_for[k] = "test"

    img_counts = {"train": 0, "val": 0, "test": 0}
    for orig, imgs in by_orig.items():
        img_counts[split_for[orig]] += len(imgs)

    orig_counts = {s: sum(1 for v in split_for.values() if v == s) for s in ("train", "val", "test")}
    print(
        f"Original stems: {n}  "
        f"(train {orig_counts['train']} / val {orig_counts['val']} / test {orig_counts['test']})"
    )
    print(
        f"Total files   : {len(all_imgs)}  "
        f"(train {img_counts['train']} / val {img_counts['val']} / test {img_counts['test']})"
    )
    print(f"Output        : {OUTPUT_DIR.resolve()}")
    print()

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    for split in ("train", "val", "test"):
        (OUTPUT_DIR / "images" / split).mkdir(parents=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True)

    jobs = [
        (
            img_path,
            src_lbl_dir / f"{img_path.stem}.txt",
            OUTPUT_DIR / "images" / split_for[original_stem(img_path.stem)] / f"{img_path.stem}.jpg",
            OUTPUT_DIR / "labels" / split_for[original_stem(img_path.stem)] / f"{img_path.stem}.txt",
        )
        for img_path in all_imgs
    ]

    print(f"Letterboxing to {TARGET_SIZE}×{TARGET_SIZE} using {NUM_WORKERS} workers...")
    ok = err = 0
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as pool:
        futures = {pool.submit(letterbox_and_adjust, *job): job[0] for job in jobs}
        with tqdm(total=len(futures)) as bar:
            for fut in as_completed(futures):
                if fut.result():
                    ok += 1
                else:
                    err += 1
                    print(f"  ERROR: {futures[fut]}")
                bar.update(1)

    print(f"\n{ok} written, {err} errors.")

    data_yaml = {
        "path":  str(OUTPUT_DIR.resolve()).replace("\\", "/"),
        "train": "images/train",
        "val":   "images/val",
        "test":  "images/test",
        "nc":    1,
        "names": ["tile"],
    }
    yaml_path = OUTPUT_DIR / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data_yaml, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"data.yaml      : {yaml_path.resolve()}")
    print(f"\nComplete. {ok} images ready for YOLO training.")

if __name__ == "__main__":
    main()
