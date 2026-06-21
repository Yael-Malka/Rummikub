"""Random test image → annotated output in _scratch/."""

import random
import shutil
from pathlib import Path

import cv2
from ultralytics import YOLO

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
WEIGHTS    = MODELS_DIR / "stage1_detection/rummikub-yolo11m/weights/best.pt"
DATA_ROOT  = DATA_DIR / "stage1_detection/ready"
IMAGE_DIRS = [
    DATA_ROOT / "images/test",
    DATA_ROOT / "images/val",
    DATA_ROOT / "images/train",
]
SCRATCH    = ROOT / "_scratch"
IMG_EXTS   = {".jpg", ".jpeg", ".png"}
CONF       = 0.25

def pick_random_image() -> Path:
    """Grab any image from test/val/train."""
    for d in IMAGE_DIRS:
        if d.exists():
            imgs = [p for p in d.glob("*") if p.suffix.lower() in IMG_EXTS]
            if imgs:
                return random.choice(imgs)
    raise FileNotFoundError("No images found in datasets/stage1_detection/ready/.")

def main():
    """Detect on a random ready/ image and save before/after JPEGs."""
    if not WEIGHTS.exists():
        raise FileNotFoundError(f"Weights not found: {WEIGHTS}")

    print(f"Loading model: {WEIGHTS}")
    model = YOLO(str(WEIGHTS))

    img_path = pick_random_image()
    print(f"Random image : {img_path}")

    # keep a clean copy in _scratch
    SCRATCH.mkdir(parents=True, exist_ok=True)
    orig_out = SCRATCH / f"test_original_{img_path.stem}.jpg"
    shutil.copy(img_path, orig_out)
    print(f"Original  -> {orig_out}")

    results = model.predict(source=str(img_path), conf=CONF, imgsz=640, verbose=False)
    r = results[0]
    n = len(r.boxes)
    print(f"Detected {n} tile(s) at conf>={CONF}")

    annotated = r.plot()
    pred_out = SCRATCH / f"test_detected_{img_path.stem}.jpg"
    cv2.imwrite(str(pred_out), annotated)
    print(f"Annotated -> {pred_out}")

    print("\nDone. Open the two test_*.jpg files in _scratch/ to compare.")

if __name__ == "__main__":
    main()
