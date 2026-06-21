"""Offline aug for stage-1 images from a YAML config → augmented/."""

import sys
import shutil
from pathlib import Path

import cv2
import numpy as np
import yaml
from tqdm import tqdm
import albumentations as A

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
SOURCE_DIR  = DATA_DIR / "stage1_detection/before-preparation"
OUTPUT_DIR  = DATA_DIR / "stage1_detection/augmented"
IMG_EXTS    = {".jpg", ".jpeg", ".png"}
MOSAIC_SIZE = 640

def load_labels(path: Path) -> tuple[list[int], list[tuple]]:
    """YOLO labels → class ids + normalized (cx,cy,w,h) boxes."""
    class_ids, bboxes = [], []
    if not path.exists():
        return class_ids, bboxes
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) == 5:
            cx, cy, w, h = (float(x) for x in parts[1:])
            # keep boxes inside [0,1]
            x1 = max(0.0, min(1.0, cx - w / 2))
            y1 = max(0.0, min(1.0, cy - h / 2))
            x2 = max(0.0, min(1.0, cx + w / 2))
            y2 = max(0.0, min(1.0, cy + h / 2))
            if x2 - x1 > 0.001 and y2 - y1 > 0.001:
                class_ids.append(int(parts[0]))
                bboxes.append(((x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1))
    return class_ids, bboxes

def save_labels(path: Path, class_ids: list[int], bboxes: list[tuple]):
    """Write YOLO label file."""
    lines = [
        f"{c} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"
        for c, (cx, cy, w, h) in zip(class_ids, bboxes)
    ]
    path.write_text("\n".join(lines), encoding="utf-8")

def normalise_params(params: dict) -> dict:
    """Turn YAML lists into tuples for albumentations."""
    return {
        k: tuple(v) if isinstance(v, list) else v
        for k, v in (params or {}).items()
    }

def build_transform(function: str, params: dict):
    """YAML function name → albumentations transform (mosaic handled elsewhere)."""
    p = normalise_params(params)

    if function == "mosaic":
        return None

    if function == "combine":
        sub_configs = (params or {}).get("augmentations", [])
        if not sub_configs:
            raise ValueError("'combine' requires a non-empty 'augmentations' list in params")
        return [build_transform(c["function"], c.get("params") or {}) for c in sub_configs]

    registry = {
        "flip_lr":             lambda: A.HorizontalFlip(**p),
        "flip_ud":             lambda: A.VerticalFlip(**p),
        "rotate":              lambda: A.Rotate(**p),
        "perspective":         lambda: A.Perspective(**p),
        "shear":               lambda: A.Affine(
                                   shear=p.pop("shear", (-5, 5)), **p
                               ),
        "translate":           lambda: A.ShiftScaleRotate(
                                   shift_limit=p.pop("shift_limit", 0.1),
                                   scale_limit=0,
                                   rotate_limit=0,
                                   **p,
                               ),
        "scale":               lambda: A.RandomScale(**p),
        "hsv":                 lambda: A.HueSaturationValue(**p),
        "brightness_contrast": lambda: A.RandomBrightnessContrast(**p),
        "blur":                lambda: A.GaussianBlur(**p),
        "noise":               lambda: A.GaussNoise(**p),
        "grayscale":           lambda: A.ToGray(**p),
        "clahe":               lambda: A.CLAHE(**p),
        "jpeg_compression":    lambda: A.ImageCompression(**p),
    }

    if function not in registry:
        available = sorted(registry) + ["combine", "mosaic"]
        raise ValueError(
            f"Unknown function '{function}'. Available: {available}"
        )

    return registry[function]()

def apply_albumentation(
    transform,   # A.BasicTransform  or  list[A.BasicTransform]  (from combine)
    image: np.ndarray,
    class_ids: list[int],
    bboxes: list[tuple],
) -> tuple[np.ndarray, list[int], list[tuple]]:
    """Run one or more transforms, keeping boxes in sync."""
    transforms_list = transform if isinstance(transform, list) else [transform]
    compose = A.Compose(
        transforms_list,
        bbox_params=A.BboxParams(
            format="yolo",
            label_fields=["class_labels"],
            min_visibility=0.2,
        ),
    )
    out = compose(image=image, bboxes=bboxes, class_labels=class_ids)
    return out["image"], list(out["class_labels"]), list(out["bboxes"])

def load_mosaic_pool(
    img_paths: list[Path],
    lbl_dir: Path,
) -> list[tuple[np.ndarray, list[int], list[tuple]]]:
    """Preload images + labels for mosaic aug."""
    pool = []
    for p in tqdm(img_paths, desc="  loading pool"):
        img = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
        cls_ids, bboxes = load_labels(lbl_dir / f"{p.stem}.txt")
        pool.append((img, cls_ids, bboxes))
    return pool

def apply_mosaic(
    pool: list[tuple],
    idx: int,
    size: int = MOSAIC_SIZE,
) -> tuple[np.ndarray, list[int], list[tuple]]:
    """2×2 mosaic from one image + three random others."""
    import random
    others = random.sample([i for i in range(len(pool)) if i != idx], k=3)
    four   = [pool[idx]] + [pool[i] for i in others]

    canvas = np.full((size, size, 3), 114, dtype=np.uint8)
    half   = size // 2
    quads  = [
        (0,    0,    half, half),
        (half, 0,    size, half),
        (0,    half, half, size),
        (half, half, size, size),
    ]

    out_cls, out_bbox = [], []

    for (img, cls_ids, bboxes), (qx1, qy1, qx2, qy2) in zip(four, quads):
        h, w      = img.shape[:2]
        qw, qh    = qx2 - qx1, qy2 - qy1
        scale     = min(qw / w, qh / h)
        nw, nh    = int(w * scale), int(h * scale)
        resized   = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        px        = qx1 + (qw - nw) // 2
        py        = qy1 + (qh - nh) // 2
        canvas[py:py + nh, px:px + nw] = resized

        for (cx_n, cy_n, bw_n, bh_n), cls_id in zip(bboxes, cls_ids):
            mx = (cx_n * nw + px) / size
            my = (cy_n * nh + py) / size
            mw = bw_n * nw / size
            mh = bh_n * nh / size
            if 0.002 < mx < 0.998 and 0.002 < my < 0.998 and mw > 0.005 and mh > 0.005:
                out_cls.append(cls_id)
                out_bbox.append((
                    max(0.0, min(1.0, mx)),
                    max(0.0, min(1.0, my)),
                    max(0.0, min(1.0, mw)),
                    max(0.0, min(1.0, mh)),
                ))

    return canvas, out_cls, out_bbox

def main(config_path: str):
    """Apply every aug in the config and copy originals too."""
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    augmentations = config.get("augmentations", [])
    if not augmentations:
        print("No augmentations defined in config.")
        return

    src_img_dir = SOURCE_DIR / "images"
    src_lbl_dir = SOURCE_DIR / "labels"
    out_img_dir = OUTPUT_DIR / "images"
    out_lbl_dir = OUTPUT_DIR / "labels"

    out_img_dir.mkdir(parents=True, exist_ok=True)
    out_lbl_dir.mkdir(parents=True, exist_ok=True)

    src_images = sorted(
        p for p in src_img_dir.glob("*")
        if p.suffix.lower() in IMG_EXTS
    )
    total_src  = len(src_images)
    total_augs = len(augmentations)

    print(f"Source images : {total_src}")
    print(f"Augmentations : {total_augs}")
    print(f"Output        : {OUTPUT_DIR.resolve()}")
    print()

    print("Copying originals...")
    for img_path in tqdm(src_images):
        shutil.copy2(img_path, out_img_dir / img_path.name)
        lbl_src = src_lbl_dir / f"{img_path.stem}.txt"
        lbl_dst = out_lbl_dir / f"{img_path.stem}.txt"
        shutil.copy2(lbl_src, lbl_dst) if lbl_src.exists() else lbl_dst.write_text("")
    print()

    mosaic_pool = None

    for aug_idx, aug_cfg in enumerate(augmentations):
        name     = aug_cfg.get("name", aug_cfg["function"])
        function = aug_cfg["function"]
        params   = aug_cfg.get("params") or {}

        print(f"Processing augmentation ({aug_idx + 1}/{total_augs}): {name}")

        transform = build_transform(function, params)
        is_mosaic = (function == "mosaic")

        if is_mosaic and mosaic_pool is None:
            print("  Pre-loading image pool for mosaic...")
            mosaic_pool = load_mosaic_pool(src_images, src_lbl_dir)

        suffix = f"__aug{aug_idx + 1}_{function}"

        for i, img_path in enumerate(tqdm(src_images)):
            stem = img_path.stem

            if is_mosaic:
                aug_img, aug_cls, aug_bbox = apply_mosaic(mosaic_pool, i)
            else:
                img = cv2.cvtColor(cv2.imread(str(img_path)), cv2.COLOR_BGR2RGB)
                cls_ids, bboxes = load_labels(src_lbl_dir / f"{stem}.txt")
                aug_img, aug_cls, aug_bbox = apply_albumentation(
                    transform, img, cls_ids, bboxes
                )

            out_img_name = f"{stem}{suffix}.jpg"
            cv2.imwrite(
                str(out_img_dir / out_img_name),
                cv2.cvtColor(aug_img, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 95],
            )
            save_labels(out_lbl_dir / f"{stem}{suffix}.txt", aug_cls, aug_bbox)

        print()

    total_out = len(list(out_img_dir.glob("*")))
    print(f"Complete. {total_out} images written to {OUTPUT_DIR.resolve()}")
    print(f"  {total_src} originals  +  {total_src * total_augs} augmented  "
          f"=  {total_src * (total_augs + 1)} total")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m rummikub.stage1_detection.augment <config.yaml>")
        sys.exit(1)
    main(sys.argv[1])
