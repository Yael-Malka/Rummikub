"""Optional image tweaks for stage 2 (name comes from metadata.json)."""

from __future__ import annotations

import cv2
import numpy as np

_CLAHE_CLIP = 2.0
_CLAHE_GRID = (8, 8)

_clahe = cv2.createCLAHE(clipLimit=_CLAHE_CLIP, tileGridSize=_CLAHE_GRID)

def clahe_on_l(bgr: np.ndarray) -> np.ndarray:
    """CLAHE on the L channel only."""
    if bgr is None or bgr.size == 0:
        return bgr
    h, w = bgr.shape[:2]
    if h < 2 or w < 2:
        return bgr
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    gx, gy = min(_CLAHE_GRID[0], w), min(_CLAHE_GRID[1], h)
    clahe = (_clahe if (gx, gy) == _CLAHE_GRID
             else cv2.createCLAHE(clipLimit=_CLAHE_CLIP, tileGridSize=(gx, gy)))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

PREPROCESSORS = {
    "none": lambda bgr: bgr,
    "clahe_on_l": clahe_on_l,
}

def preprocess_bgr(bgr: np.ndarray, name: str | None) -> np.ndarray:
    """Run named preprocessor, or return image unchanged."""
    if not name:
        return bgr
    fn = PREPROCESSORS.get(name)
    return fn(bgr) if fn is not None else bgr
