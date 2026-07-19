"""YOLO detect + classify pipeline for board photos."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

# Local geometry, rules, and serialization helpers.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import grouping   # noqa: E402
import rules       # noqa: E402
import visualize   # noqa: E402

BASE       = Path(__file__).resolve().parent
MODELS_DIR = BASE / "models"


# ─────────────────────────────────────────────────────────────────────────────
# Vendored crop geometry (must match training exactly: this is what makes
# two-digit numbers 10-13 readable: aspect-preserving letterbox, never a stretch).
# ─────────────────────────────────────────────────────────────────────────────

PAD_COLOR   = (114, 114, 114)
PADDING_PCT = 0.05
MIN_DIM     = 10


def letterbox_square(img: np.ndarray, size: int) -> np.ndarray:
    """Resize into a square canvas without stretching: matches training preprocessing.
    Gray bars pad the shorter side so two-digit numbers stay readable.
    """
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return np.full((size, size, 3), PAD_COLOR, dtype=np.uint8)
    scale = size / max(h, w)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((size, size, 3), PAD_COLOR, dtype=np.uint8)
    y_off, x_off = (size - new_h) // 2, (size - new_w) // 2
    canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
    return canvas


def padded_crop(img: np.ndarray, x: int, y: int, w: int, h: int):
    """Crop a detector box with 5% padding on each side.
    Returns None if the crop would be too small to classify reliably.
    """
    img_h, img_w = img.shape[:2]
    pad_x, pad_y = int(round(w * PADDING_PCT)), int(round(h * PADDING_PCT))
    x1, y1 = max(0, x - pad_x), max(0, y - pad_y)
    x2, y2 = min(img_w, x + w + pad_x), min(img_h, y + h + pad_y)
    if (x2 - x1) < MIN_DIM or (y2 - y1) < MIN_DIM:
        return None
    return img[y1:y2, x1:x2]


# ─────────────────────────────────────────────────────────────────────────────
# Vendored deterministic preprocessing (CLAHE-on-L). The active v4 model trains
# with preprocess="none", so this is identity unless metadata says otherwise.
# ─────────────────────────────────────────────────────────────────────────────

_CLAHE_CLIP, _CLAHE_GRID = 2.0, (8, 8)
_clahe = cv2.createCLAHE(clipLimit=_CLAHE_CLIP, tileGridSize=_CLAHE_GRID)


def clahe_on_l(bgr: np.ndarray) -> np.ndarray:
    """Apply CLAHE on the L channel when the model metadata asks for it."""
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


def preprocess_bgr(bgr: np.ndarray, name: str | None) -> np.ndarray:
    """Run the preprocessing step named in the stage-2 metadata."""
    if name == "clahe_on_l":
        return clahe_on_l(bgr)
    return bgr   # "none" / None / unknown -> identity


# ─────────────────────────────────────────────────────────────────────────────
# Vendored Stage-2 classifier architecture (must stay byte-stable so best.pt
# loads by parameter name). Custom CNN backbone, two heads.
# ─────────────────────────────────────────────────────────────────────────────

def _build_custom_cnn() -> nn.Module:
    """Build the small CNN backbone used by the tile classifier."""
    def block(cin, cout, pool=True):
        layers = [
            nn.Conv2d(cin, cout, 3, padding=1, bias=False),
            nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
            nn.Conv2d(cout, cout, 3, padding=1, bias=False),
            nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
        ]
        if pool:
            layers.append(nn.MaxPool2d(2))
        return nn.Sequential(*layers)

    return nn.Sequential(
        block(3, 32), block(32, 64), block(64, 128), block(128, 256),
        block(256, 512, pool=False),
        nn.AdaptiveAvgPool2d(1), nn.Flatten(),
    )


class TileClassifier(nn.Module):
    """Two-headed CNN: one head for number, one for color."""

    def __init__(self, n_numbers: int = 14, n_colors: int = 5):
        super().__init__()
        self.backbone = _build_custom_cnn()
        self.feat_dim = 512
        self.num_head = nn.Linear(self.feat_dim, n_numbers)
        self.col_head = nn.Linear(self.feat_dim, n_colors)

    def forward(self, x: torch.Tensor):
        """Return number logits and color logits for a batch of tile crops."""
        feat = self.backbone(x)
        return self.num_head(feat), self.col_head(feat)


# ─────────────────────────────────────────────────────────────────────────────
# Inference
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Model cache (loaded once per worker process, reused across tasks)
# ─────────────────────────────────────────────────────────────────────────────

_yolo_cache: dict[str, object] = {}
_classifier_cache: dict[str, tuple] = {}


def _resolve_device() -> torch.device:
    """Use CUDA when available, otherwise CPU."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_yolo(models_dir: Path):
    """Cached YOLO model per worker process."""
    key = str(models_dir.resolve())
    if key not in _yolo_cache:
        from ultralytics import YOLO
        device = _resolve_device()
        print(f"Loading YOLO detector on {device} ...")
        _yolo_cache[key] = YOLO(str(models_dir / "stage1" / "best.pt"))
    return _yolo_cache[key]


def get_classifier(models_dir: Path):
    """Return a cached stage-2 classifier bundle (model + preprocess settings)."""
    key = str(models_dir.resolve())
    if key not in _classifier_cache:
        print(f"Loading tile classifier on {_resolve_device()} ...")
        _classifier_cache[key] = load_classifier(models_dir)
    return _classifier_cache[key]


def warmup_models(models_dir: str | Path) -> None:
    """Pre-load YOLO and classifier weights into the process cache.
    Called from celery worker_process_init so the first task is not slow.
    """
    models_dir = Path(models_dir)
    get_yolo(models_dir)
    get_classifier(models_dir)
    print("Inference models warmed up.")


def load_classifier(models_dir: Path):
    """Load the stage-2 CNN and its preprocessing settings from disk."""
    meta = json.loads((models_dir / "stage2" / "metadata.json").read_text(encoding="utf-8"))
    num_classes = meta["number_classes"]
    col_classes = meta["color_classes"]
    inp_size    = meta["input_size"]
    preprocess  = meta.get("preprocess", "none")
    mean = np.array(meta["normalize_mean"], dtype=np.float32).reshape(1, 1, 3)
    std  = np.array(meta["normalize_std"],  dtype=np.float32).reshape(1, 1, 3)

    device = _resolve_device()
    model  = TileClassifier(n_numbers=len(num_classes), n_colors=len(col_classes))
    model.load_state_dict(torch.load(models_dir / "stage2" / "best.pt",
                                     map_location=device, weights_only=True))
    model.eval().to(device)
    return model, num_classes, col_classes, inp_size, mean, std, device, preprocess


def classify_probs(crop_bgr, model, num_classes, col_classes, inp_size, mean, std, device, preprocess):
    """Classify one tile crop and return number/color with confidence scores."""
    results = classify_crops_batch(
        [crop_bgr], model, num_classes, col_classes, inp_size, mean, std, device, preprocess,
    )
    return results[0]


def classify_crops_batch(
    crops_bgr,
    model,
    num_classes,
    col_classes,
    inp_size,
    mean,
    std,
    device,
    preprocess,
    batch_size: int = 32,
):
    """Batch classify crops: much faster than one-by-one on CPU."""
    if not crops_bgr:
        return []

    use_autocast = device.type == "cuda"
    all_results = []

    for start in range(0, len(crops_bgr), batch_size):
        batch_crops = crops_bgr[start:start + batch_size]
        tensors = []
        for crop_bgr in batch_crops:
            crop_bgr = letterbox_square(crop_bgr, inp_size)
            crop_bgr = preprocess_bgr(crop_bgr, preprocess)
            img = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
            x = (img.astype(np.float32) / 255.0 - mean) / std
            tensors.append(x.transpose(2, 0, 1))

        batch = torch.from_numpy(np.stack(tensors)).to(device)
        with torch.no_grad():
            if use_autocast:
                with torch.autocast(device_type=device.type, dtype=torch.float16):
                    nl, cl = model(batch)
            else:
                nl, cl = model(batch)

        npb = F.softmax(nl.float(), dim=1)
        cpb = F.softmax(cl.float(), dim=1)
        for i in range(len(batch_crops)):
            ni, ci = int(npb[i].argmax()), int(cpb[i].argmax())
            all_results.append(
                (num_classes[ni], float(npb[i, ni]), col_classes[ci], float(cpb[i, ci]))
            )

    return all_results


COLOR_BGR = {
    "black":  (80, 80, 80),   "blue": (220, 130, 0), "orange": (0, 165, 255),
    "red":    (0, 0, 200),    "joker": (180, 100, 180),
}


def _save_tile_sheet(img_bgr, tiles, boxes, out_path, cell=160):
    """Write a debug sheet showing every detected tile and its prediction."""
    cols = min(8, max(1, len(tiles)))
    rows = (len(tiles) + cols - 1) // cols
    canvas = np.full((rows * cell, cols * cell, 3), 40, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for idx, t in enumerate(tiles):
        r, c = divmod(idx, cols)
        x1, y1, x2, y2 = boxes[idx]
        crop = img_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        thumb = cv2.resize(crop, (cell - 4, cell - 40), interpolation=cv2.INTER_AREA)
        cy, cx = r * cell + 2, c * cell + 2
        canvas[cy:cy + thumb.shape[0], cx:cx + thumb.shape[1]] = thumb
        bar_col = COLOR_BGR.get(t["color"], (160, 160, 160))
        by = r * cell + cell - 38
        cv2.rectangle(canvas, (c * cell, by), (c * cell + cell - 1, r * cell + cell - 1), bar_col, -1)
        cv2.putText(canvas, f"{t['number']} / {t['color']}", (c * cell + 3, by + 16), font, 0.52, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"n:{t['num_conf']:.2f} c:{t['col_conf']:.2f}", (c * cell + 3, by + 32), font, 0.38, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"#{idx}", (c * cell + 3, r * cell + 14), font, 0.38, (200, 255, 200), 1, cv2.LINE_AA)
    cv2.imwrite(str(out_path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 95])


def run_pipeline(image_path: str | Path, out_dir: str | Path, models_dir: str | Path, conf: float = 0.25) -> dict:
    """Full board pipeline: detect tiles, classify, group into sets.
    Returns a dict with sets/unassigned tiles in the shape the backend API expects.
    """
    img_path   = Path(image_path)
    out_dir    = Path(out_dir)
    models_dir = Path(models_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"Cannot read image: {img_path}")

    # ── Stage 1: detect ──────────────────────────────────────────────────────
    print(f"Stage 1: detecting tiles in {img_path.name} ...")
    det = get_yolo(models_dir)
    r   = det.predict(source=str(img_path), conf=conf, imgsz=640, verbose=False)[0]
    n   = len(r.boxes)
    print(f"  detected {n} tiles")

    boxes, crops, det_confs = [], [], []
    for box in r.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)
        boxes.append((x1, y1, x2, y2))
        pc = padded_crop(img, x1, y1, x2 - x1, y2 - y1)
        crops.append(pc if pc is not None else img[y1:y2, x1:x2])
        det_confs.append(float(box.conf[0]))

    # ── Stage 2: classify (batched) ──────────────────────────────────────────
    print("Stage 2: classifying crops ...")
    model, num_classes, col_classes, inp_size, mean, std, device, preprocess = get_classifier(models_dir)
    preds = classify_crops_batch(
        crops, model, num_classes, col_classes, inp_size, mean, std, device, preprocess,
    )

    tiles = []
    for i in range(n):
        num, ncf, col, ccf = preds[i]
        tiles.append({
            "index": i, "bbox": list(boxes[i]),
            "number": num, "color": col,
            "det_conf": round(det_confs[i], 3),
            "num_conf": round(ncf, 3), "col_conf": round(ccf, 3),
        })

    # ── Stage 3: group + fit melds (the series recognition) ──────────────────
    print("Stage 3: grouping into series ...")
    series, meta = grouping.group_tiles(tiles)
    series = grouping.refine_series(series, rules.meld_score)
    print(f"  after refinement: {len(series)} series")

    sets, assigned = [], 0
    for sid, s in enumerate(series):
        fit = rules.fit_meld(s)
        for li, t in enumerate(s):
            t["suggestion"] = fit["suggestions"].get(li)
        assigned += len(s)
        sets.append({
            "id": sid, "type": fit["type"], "valid": fit["valid"],
            "color": fit["color"], "number": fit["number"],
            "reason": fit["reason"], "tiles": s,
        })

    # ── Output ───────────────────────────────────────────────────────────────
    annotated = visualize.draw_board(img, sets, meta)
    cv2.imwrite(str(out_dir / "board_annotated.jpg"), annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    state = {
        "image": img_path.name,
        "tile_px": {"w": round(meta["tile_w"], 1), "h": round(meta["tile_h"], 1)},
        "skew_deg": round(meta["skew_deg"], 2),
        "sets": sets,
        "unassigned": [],
    }
    
    Path(out_dir / "board_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    _save_tile_sheet(img, tiles, boxes, out_dir / "tiles_classified.jpg")
    
    return state

def run_hand_pipeline(image_path: str | Path, models_dir: str | Path, conf: float = 0.25) -> list[dict]:
    """Detect and classify tiles on a rack/hand photo: no grouping step.
    Returns a flat list of tile dicts merged with board sets in the worker task.
    """
    img_path   = Path(image_path)
    models_dir = Path(models_dir)

    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"Cannot read image: {img_path}")

    # ── Stage 1: detect ──────────────────────────────────────────────────────
    print(f"Stage 1 (Hand): detecting tiles in {img_path.name} ...")
    det = get_yolo(models_dir)
    r   = det.predict(source=str(img_path), conf=conf, imgsz=640, verbose=False)[0]
    n   = len(r.boxes)
    print(f"  detected {n} tiles in hand")

    boxes, crops, det_confs = [], [], []
    for box in r.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)
        boxes.append((x1, y1, x2, y2))
        pc = padded_crop(img, x1, y1, x2 - x1, y2 - y1)
        crops.append(pc if pc is not None else img[y1:y2, x1:x2])
        det_confs.append(float(box.conf[0]))

    # ── Stage 2: classify (batched) ──────────────────────────────────────────
    print("Stage 2 (Hand): classifying crops ...")
    model, num_classes, col_classes, inp_size, mean, std, device, preprocess = get_classifier(models_dir)
    preds = classify_crops_batch(
        crops, model, num_classes, col_classes, inp_size, mean, std, device, preprocess,
    )

    tiles = []
    for i in range(n):
        num, ncf, col, ccf = preds[i]
        tiles.append({
            "color": col,
            "number": num,
        })
    return tiles


def main():
    """CLI entry point for running the board pipeline on a single image."""
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("out_dir")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--models-dir", default=str(MODELS_DIR),
                    help="directory holding stage1/ and stage2/ (default: ./models)")
    args = ap.parse_args()

    try:
        state = run_pipeline(
            image_path=args.image,
            out_dir=args.out_dir,
            models_dir=args.models_dir,
            conf=args.conf
        )
        sets = state["sets"]
        n_valid  = sum(1 for s in sets if s["valid"])
        n_review = sum(1 for s in sets if not s["valid"] and s["type"] != "incomplete")
        n_inc    = sum(1 for s in sets if s["type"] == "incomplete")
        n_tiles  = sum(len(s["tiles"]) for s in sets)
        
        out_dir = Path(args.out_dir)
        print(f"\nDone. {n_tiles} tiles -> {len(sets)} series "
              f"({n_valid} valid, {n_review} needs-review, {n_inc} incomplete)")
        print(f"  -> {out_dir / 'board_annotated.jpg'}")
        print(f"  -> {out_dir / 'tiles_classified.jpg'}")
        print(f"  -> {out_dir / 'board_state.json'}")
    except Exception as e:
        sys.exit(f"Pipeline failed: {e}")


if __name__ == "__main__":
    main()
