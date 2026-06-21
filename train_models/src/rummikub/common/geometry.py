"""Crop helpers — keep letterbox/padding identical in train and inference."""

from __future__ import annotations

import re
from pathlib import Path

import cv2
import numpy as np

CROP_SIZE    = 128
PAD_COLOR    = (114, 114, 114)  # gray bars in letterbox
PADDING_PCT  = 0.05
JPEG_QUALITY = 95
MIN_DIM      = 10               # ignore tiny slivers

def letterbox_square(img: np.ndarray, size: int = CROP_SIZE) -> np.ndarray:
    """Fit crop into a square canvas with gray padding."""
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return np.full((size, size, 3), PAD_COLOR, dtype=np.uint8)

    scale = size / max(h, w)
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    canvas = np.full((size, size, 3), PAD_COLOR, dtype=np.uint8)
    y_off = (size - new_h) // 2
    x_off = (size - new_w) // 2
    canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
    return canvas

def padded_crop(img: np.ndarray, x: int, y: int, w: int, h: int):
    """Crop with a little padding; None if the box is too small."""
    img_h, img_w = img.shape[:2]
    pad_x = int(round(w * PADDING_PCT))
    pad_y = int(round(h * PADDING_PCT))

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(img_w, x + w + pad_x)
    y2 = min(img_h, y + h + pad_y)

    if (x2 - x1) < MIN_DIM or (y2 - y1) < MIN_DIM:
        return None
    return img[y1:y2, x1:x2]

def normalize_number(raw: str) -> str:
    """'J' → joker, otherwise pass through 1–13."""
    raw = raw.strip()
    if raw.upper() == "J":
        return "joker"
    return raw

def normalize_color(raw: str) -> str:
    """Lowercase color name."""
    return raw.strip().lower()

def safe_stem(stem: str) -> str:
    """Filename-safe stem."""
    return re.sub(r"[^\w\-]", "_", stem)

def save_crop(crop: np.ndarray, out_path: Path) -> bool:
    """Write a JPEG crop, creating parent dirs."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return cv2.imwrite(str(out_path), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
