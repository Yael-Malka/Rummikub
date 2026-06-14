"""Label tiles via Qwen-VL in LM Studio (--image or --zip). Disagreements -> crops_review/."""

import argparse
import base64
import csv
import importlib.util
import io
import json
import os
import random
import re
import sys
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import requests
from tqdm import tqdm

os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
from rummikub.common import letterbox_square, padded_crop
S1_WEIGHTS = MODELS_DIR / "stage1_detection/rummikub-yolo11m/weights/best.pt"

COLORS  = ("black", "blue", "orange", "red")
SYSTEM_PROMPT = (
    "You are a precise Rummikub tile reader. You always answer with strict JSON."
)
USER_PROMPT = (
    "This image is a single Rummikub tile. Identify:\n"
    "1) number: the printed value 1-13, or \"joker\" if it shows a joker/smiley "
    "(no number).\n"
    "2) color: the color of the printed digit — one of black, blue, orange, red. "
    "Orange is a light/amber tone; red is a deep red. Use \"joker\" for a joker "
    "tile.\n"
    'Respond with ONLY this JSON, nothing else: {"number": "...", "color": "..."}'
)

def detect_model(endpoint: str) -> str:
    r = requests.get(f"{endpoint}/models", timeout=10)
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        sys.exit("LM Studio reports no loaded model. Load a vision model first.")
    return data[0]["id"]

def _b64_jpeg(img_bgr) -> str:
    ok, buf = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    return base64.b64encode(buf.tobytes()).decode("ascii")

def query_vlm(endpoint: str, model: str, img_bgr, temperature: float):
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": 80,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": USER_PROMPT},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{_b64_jpeg(img_bgr)}"}},
            ]},
        ],
    }
    r = requests.post(f"{endpoint}/chat/completions", json=payload, timeout=120)
    r.raise_for_status()
    return parse_label(r.json()["choices"][0]["message"]["content"])

def canon_number(s) -> str | None:
    s = str(s).strip().lower()
    if s in ("j", "joker", "wild", "wildcard"):
        return "joker"
    m = re.search(r"\d+", s)
    if m and 1 <= int(m.group()) <= 13:
        return str(int(m.group()))
    return None

def canon_color(s) -> str | None:
    s = str(s).strip().lower()
    for c in COLORS:
        if c in s:
            return c
    if "joker" in s:
        return "joker"
    return None

def parse_label(content: str):
    m = re.search(r"\{.*?\}", content, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError:
        return None
    num = canon_number(obj.get("number", ""))
    col = canon_color(obj.get("color", ""))
    if num is None or col is None:
        return None
    if num == "joker":
        col = "joker"
    elif col == "joker":
        return None
    return (num, col)

def jitter(img_bgr, rng: random.Random):
    h, w = img_bgr.shape[:2]
    ang = rng.uniform(-5, 5)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
    rot = cv2.warpAffine(img_bgr, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    p = rng.uniform(0.03, 0.08)
    py, px = int(h * p), int(w * p)
    return rot[py:h - py or h, px:w - px or w]

def vote(labels: list, passes: int):
    valid = [l for l in labels if l is not None]
    if not valid:
        return None, 0.0, "review"
    label, cnt = Counter(valid).most_common(1)[0]
    agreement = cnt / passes
    if cnt == passes:
        status = "accept"
    elif cnt * 2 > passes:
        status = "review-light"
    else:
        status = "review"
    return label, agreement, status

def load_image_bytes(data: bytes):
    buf = np.frombuffer(data, np.uint8)
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)

def detect_tiles(det_model, img_bgr, conf: float):
    """Run YOLO on img_bgr, return list of (x1,y1,x2,y2) boxes."""
    import tempfile
    h, w = img_bgr.shape[:2]
    results = det_model.predict(source=img_bgr, conf=conf, imgsz=640, verbose=False)
    boxes = []
    for b in results[0].boxes:
        x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
        boxes.append((max(0, x1), max(0, y1), min(w, x2), min(h, y2)))
    return boxes

def extract_crops(img_bgr, boxes):
    crops = []
    for x1, y1, x2, y2 in boxes:
        c = padded_crop(img_bgr, x1, y1, x2 - x1, y2 - y1)
        crops.append(c if c is not None else img_bgr[y1:y2, x1:x2])
    return crops

def save_montage(tiles: list, path: Path, cell: int = 150, cols: int = 8):
    n = len(tiles)
    if n == 0:
        return
    rows = (n + cols - 1) // cols
    grid = np.full((rows * cell, cols * cell, 3), 40, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for i, t in enumerate(tiles):
        rr, cc = divmod(i, cols)
        y0, x0 = rr * cell, cc * cell
        lb = t.get("letterbox")
        if lb is not None:
            thumb = cv2.resize(lb, (cell - 8, cell - 28))
            grid[y0 + 4:y0 + 4 + thumb.shape[0], x0 + 4:x0 + 4 + thumb.shape[1]] = thumb
        lab = f"{t['label'][0]}/{t['label'][1]}" if t["label"] else "??"
        txt = f"{lab} {int(t['agreement'] * 100)}%"
        review = t["status"] not in ("accept", "review-light")
        col = (0, 140, 255) if review else (0, 220, 0)
        cv2.putText(grid, txt, (x0 + 3, y0 + cell - 8), font, 0.38, col, 1, cv2.LINE_AA)
        if review:
            cv2.rectangle(grid, (x0 + 1, y0 + 1), (x0 + cell - 2, y0 + cell - 2), col, 2)
    cv2.imwrite(str(path), grid, [cv2.IMWRITE_JPEG_QUALITY, 92])

def label_tiles_parallel(
    tile_jobs: list[dict],   # [{tile_id, crop, bbox, stem}]
    endpoint: str,
    model: str,
    passes: int,
    temp: float,
    workers: int,
) -> list[dict]:
    """
    Run all VLM calls (N passes × all tiles) in parallel via ThreadPoolExecutor.
    Returns list of tile result dicts.
    """
    rng = random.Random(42)

    # Build flat job list: (tile_id, pass_idx, sub_crop, temperature)
    jobs = []
    for t in tile_jobs:
        crop = t["crop"]
        for p in range(passes):
            sub  = crop if p == 0 else jitter(crop, rng)
            jobs.append((t["tile_id"], p, sub, 0.0 if p == 0 else temp))

    # Run all jobs in parallel.
    results: dict[str, list] = {t["tile_id"]: [None] * passes for t in tile_jobs}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {
            pool.submit(query_vlm, endpoint, model, sub, t_val): (tile_id, p_idx)
            for tile_id, p_idx, sub, t_val in jobs
        }
        with tqdm(total=len(jobs), desc="VLM calls", unit="call") as bar:
            for fut in as_completed(future_map):
                tile_id, p_idx = future_map[fut]
                try:
                    results[tile_id][p_idx] = fut.result()
                except Exception:
                    results[tile_id][p_idx] = None
                bar.update(1)

    # Vote per tile.
    out = []
    for t in tile_jobs:
        labels      = results[t["tile_id"]]
        label, agr, status = vote(labels, passes)
        out.append({
            **t,
            "letterbox":  letterbox_square(t["crop"]),
            "label":      label,
            "agreement":  round(agr, 3),
            "status":     status,
            "passes":     [list(l) if l else None for l in labels],
        })
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image",   default=None, help="Single image path")
    ap.add_argument("--zip",     default=None, help="Zip of board photos")
    ap.add_argument("--endpoint", default="http://localhost:1234/v1")
    ap.add_argument("--model",   default=None)
    ap.add_argument("--passes",  type=int,   default=3)
    ap.add_argument("--temp",    type=float, default=0.4)
    ap.add_argument("--conf",    type=float, default=0.25, help="YOLO conf threshold")
    ap.add_argument("--workers", type=int,   default=4,
                    help="Parallel VLM request threads (LM Studio queue size)")
    ap.add_argument("--out",     default="data/stage2_vlm")
    args = ap.parse_args()

    if not args.image and not args.zip:
        args.image = "testcase.jpeg"  # pilot default

    endpoint = args.endpoint.rstrip("/")
    out_dir  = (ROOT / args.out) if not Path(args.out).is_absolute() else Path(args.out)

    try:
        model = args.model or detect_model(endpoint)
    except requests.exceptions.RequestException:
        sys.exit(
            f"Cannot reach LM Studio at {endpoint}.\n"
            "  - Start LM Studio, load a vision model (e.g. Qwen-VL),\n"
            "  - enable the local server (Developer tab).")
    print(f"VLM model  : {model}")
    print(f"Workers    : {args.workers}  Passes: {args.passes}")

    image_items: list[tuple[str, bytes]] = []  # (stem, raw_bytes)

    if args.zip:
        zpath = (ROOT / args.zip) if not Path(args.zip).is_absolute() else Path(args.zip)
        print(f"Reading zip: {zpath.name}")
        with zipfile.ZipFile(zpath) as z:
            names = sorted(n for n in z.namelist()
                           if n.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')))
        print(f"  {len(names)} images found")
        zpath_str = str(zpath)
        def _read(name):
            with zipfile.ZipFile(zpath_str) as z:
                return (Path(name).stem, z.read(name))
        with ThreadPoolExecutor(max_workers=8) as pool:
            image_items = list(tqdm(
                pool.map(_read, names), total=len(names), desc="Reading zip"))
    else:
        img_path = (ROOT / args.image) if not Path(args.image).is_absolute() \
                   else Path(args.image)
        image_items = [(img_path.stem, img_path.read_bytes())]

    from ultralytics import YOLO
    det_model = YOLO(str(S1_WEIGHTS))

    tile_jobs: list[dict] = []
    img_tile_counts: dict[str, int] = {}

    print(f"\nRunning YOLO detection on {len(image_items)} images ...")
    for stem, raw in tqdm(image_items, desc="Detecting", unit="img"):
        img = load_image_bytes(raw)
        if img is None:
            continue
        boxes = detect_tiles(det_model, img, args.conf)
        crops = extract_crops(img, boxes)
        safe_stem = re.sub(r"[^\w\-]", "_", stem)
        for idx, (box, crop) in enumerate(zip(boxes, crops)):
            tile_jobs.append({
                "tile_id": f"{safe_stem}__{idx}",
                "stem":    safe_stem,
                "idx":     idx,
                "bbox":    list(box),
                "crop":    crop,
            })
        img_tile_counts[stem] = len(boxes)

    total_tiles = len(tile_jobs)
    total_calls = total_tiles * args.passes
    print(f"\nDetected {total_tiles} tiles across {len(image_items)} images "
          f"({total_calls} VLM calls with {args.workers} workers)")

    if total_tiles == 0:
        sys.exit("No tiles detected. Check images and YOLO weights.")

    print()
    labeled = label_tiles_parallel(
        tile_jobs, endpoint, model, args.passes, args.temp, args.workers)

    crops_dir  = out_dir / "crops"
    review_dir = out_dir / "crops_review"
    out_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)

    manifest, review_rows, raw_records = [], [], []
    for t in labeled:
        accepted = t["status"] in ("accept", "review-light") and t["label"] is not None
        if accepted:
            num, col = t["label"]
            dst = crops_dir / num / col / f"vlm_{t['stem']}_{t['idx']}.jpg"
            dst.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(dst), t["letterbox"], [cv2.IMWRITE_JPEG_QUALITY, 95])
            manifest.append({
                "filepath": dst.relative_to(ROOT).as_posix(),
                "number": num, "color": col, "source": "vlm", "split": "train",
            })
        else:
            dst = review_dir / f"{t['stem']}_{t['idx']}.jpg"
            cv2.imwrite(str(dst), t["letterbox"], [cv2.IMWRITE_JPEG_QUALITY, 95])
            review_rows.append({
                "filepath":        dst.relative_to(ROOT).as_posix(),
                "proposed_number": t["label"][0] if t["label"] else "",
                "proposed_color":  t["label"][1] if t["label"] else "",
                "agreement": t["agreement"], "status": t["status"],
            })
        raw_records.append({
            "tile_id": t["tile_id"], "bbox": t["bbox"],
            "label": list(t["label"]) if t["label"] else None,
            "agreement": t["agreement"], "status": t["status"],
            "passes": t["passes"],
        })

    # Write manifest (append if exists, so repeated runs accumulate).
    man_path = out_dir / "manifest.csv"
    write_header = not man_path.exists()
    with open(man_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filepath","number","color","source","split"])
        if write_header:
            w.writeheader()
        w.writerows(manifest)

    with open(out_dir / "review.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filepath","proposed_number",
                                          "proposed_color","agreement","status"])
        w.writeheader(); w.writerows(review_rows)

    (out_dir / "vlm_raw.json").write_text(
        json.dumps(raw_records, indent=2), encoding="utf-8")

    save_montage(labeled, out_dir / "review_montage.jpg")

    n_acc = len(manifest); n_rev = len(review_rows)
    assert n_acc + n_rev == total_tiles
    cls_counts = Counter((m["number"], m["color"]) for m in manifest)
    accept_full = sum(1 for t in labeled if t["status"] == "accept")
    accept_light= sum(1 for t in labeled if t["status"] == "review-light")

    print(f"\n{'='*55}")
    print(f"DONE — {total_tiles} tiles from {len(image_items)} images")
    print(f"  accepted (full):  {accept_full}")
    print(f"  accepted (light): {accept_light}")
    print(f"  review:           {n_rev}")
    print(f"\nClass distribution (accepted):")
    for (num, col), cnt in sorted(cls_counts.items(), key=lambda x: (len(x[0][0]), x[0])):
        print(f"  {num:>5}/{col:<8} {cnt:>4}")
    print(f"\n-> {man_path}")
    print(f"-> {out_dir / 'review_montage.jpg'}")
    print(f"{'='*55}")

if __name__ == "__main__":
    main()
