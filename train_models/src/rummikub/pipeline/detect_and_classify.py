"""Detect tiles, classify each crop, save as numbered JPEGs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import torch

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from rummikub.common import letterbox_square, padded_crop, preprocess_bgr
from rummikub.paths import STAGE1_WEIGHTS, STAGE2_METADATA, STAGE2_WEIGHTS
from rummikub.stage2_classification.model import TileClassifier

DET_CONF = 0.25

def load_classifier():
    """Load stage-2 weights + metadata from disk."""
    meta        = json.loads(STAGE2_METADATA.read_text(encoding="utf-8"))
    num_classes = meta["number_classes"]
    col_classes = meta["color_classes"]
    inp_size    = meta["input_size"]
    preprocess  = meta.get("preprocess", "none")
    mean = np.array(meta["normalize_mean"], dtype=np.float32).reshape(1, 1, 3)
    std  = np.array(meta["normalize_std"],  dtype=np.float32).reshape(1, 1, 3)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = TileClassifier(n_numbers=len(num_classes), n_colors=len(col_classes))
    model.load_state_dict(torch.load(STAGE2_WEIGHTS, map_location=device, weights_only=True))
    model.eval().to(device)

    return model, num_classes, col_classes, inp_size, mean, std, device, preprocess

def classify_crop(crop_bgr, model, num_classes, col_classes, inp_size, mean, std, device, preprocess="none"):
    """Return (number, color) for one crop."""
    # same preprocessing as training (see geometry.py)
    crop_bgr = letterbox_square(crop_bgr, inp_size)
    crop_bgr = preprocess_bgr(crop_bgr, preprocess)
    img = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    x = (img.astype(np.float32) / 255.0 - mean) / std
    x = torch.from_numpy(x.transpose(2, 0, 1)).unsqueeze(0).to(device)

    with torch.no_grad(), torch.autocast(device_type=device.type, dtype=torch.float16):
        nl, cl = model(x)

    return num_classes[nl.argmax(1).item()], col_classes[cl.argmax(1).item()]

def main():
    """CLI entry: image in, classified crops out."""
    parser = argparse.ArgumentParser()
    parser.add_argument("image",      help="Input image path")
    parser.add_argument("output_dir", help="Directory to save classified crops")
    parser.add_argument("--conf", type=float, default=DET_CONF)
    args = parser.parse_args()

    img_path = Path(args.image)
    out_dir  = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    from ultralytics import YOLO
    print(f"Stage 1: detecting tiles in {img_path.name} ...")
    det_model = YOLO(str(STAGE1_WEIGHTS))
    results   = det_model.predict(source=str(img_path), conf=args.conf, imgsz=640, verbose=False)
    r         = results[0]
    print(f"  Detected {len(r.boxes)} tiles")

    img = cv2.imread(str(img_path))
    if img is None:
        sys.exit(f"Cannot read image: {img_path}")

    crops = []
    for box in r.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(img.shape[1], x2); y2 = min(img.shape[0], y2)
        pc = padded_crop(img, x1, y1, x2 - x1, y2 - y1)
        crops.append(pc if pc is not None else img[y1:y2, x1:x2])

    print("Stage 2: classifying crops (parallel) ...")
    model, num_classes, col_classes, inp_size, mean, std, device, preprocess = load_classifier()

    def classify_one(arg):
        idx, crop = arg
        num, col = classify_crop(crop, model, num_classes, col_classes, inp_size, mean, std, device, preprocess)
        return idx, num, col

    results_list = [None] * len(crops)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(classify_one, (i, c)): i for i, c in enumerate(crops)}
        for fut in as_completed(futures):
            idx, num, col = fut.result()
            results_list[idx] = (num, col)

    print(f"Saving to {out_dir} ...")
    for idx, (crop, (num, col)) in enumerate(zip(crops, results_list)):
        fname = f"{num} - {col} - {idx}.jpg"
        cv2.imwrite(str(out_dir / fname), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])

    print(f"\nDone. {len(crops)} crops saved to {out_dir}/")
    num_counts = Counter(r[0] for r in results_list)
    col_counts = Counter(r[1] for r in results_list)
    print("Numbers:", dict(sorted(num_counts.items(), key=lambda x: (len(x[0]), x[0]))))
    print("Colors: ", dict(col_counts))

if __name__ == "__main__":
    main()
