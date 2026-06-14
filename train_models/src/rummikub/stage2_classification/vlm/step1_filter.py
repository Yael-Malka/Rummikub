"""VLM pipeline step 1 — YOLO detect, then ask the model if each crop is a real tile."""

import argparse, base64, importlib.util, json, os, re, sys, time, zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2, numpy as np, requests
from tqdm import tqdm
from ultralytics import YOLO  # import before any HTTP/thread activity

os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
from rummikub.common import letterbox_square, padded_crop
S1_WEIGHTS = MODELS_DIR / "stage1_detection/rummikub-yolo11m/weights/best.pt"

SYS_PROMPT  = "You are a Rummikub tile inspector. Answer with exactly one word."
USER_PROMPT = (
    "Does this image show a Rummikub game tile with a clearly visible number (1–13) "
    "or joker symbol? Reply with ONLY the word YES or NO."
)

def b64(img):
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return base64.b64encode(buf.tobytes()).decode()

def detect_model(endpoint):
    r = requests.get(f"{endpoint}/models", timeout=10)
    r.raise_for_status()
    d = r.json().get("data", [])
    if not d: sys.exit("No model loaded in LM Studio.")
    # Prefer a vision/VL model; fall back to first entry.
    for m in d:
        mid = m["id"].lower()
        if any(k in mid for k in ("vl", "vision", "qwen2.5-vl", "llava", "pixtral")):
            return m["id"]
    return d[0]["id"]

def _call(endpoint, model, img):
    r = requests.post(f"{endpoint}/chat/completions", json={
        "model": model, "temperature": 0.0, "max_tokens": 5,
        "messages": [
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": USER_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64(img)}"}},
            ]},
        ],
    }, timeout=(5, 15))
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip().upper()

def query(endpoint, model, img, max_retries=6):
    """Call VLM; on server error retry with exponential back-off. Returns True/False/None."""
    delay = 2.0
    for attempt in range(max_retries):
        try:
            resp = _call(endpoint, model, img)
            if "YES" in resp: return True
            if "NO"  in resp: return False
            # Unparseable reply — retry immediately (no sleep)
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(delay); delay = min(delay * 2, 30)
    return None  # exhausted

def decode(data):
    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

def save_grid(tiles, path, cols=8, cell=128, label_fn=None):
    n = len(tiles)
    if n == 0: return
    rows = (n + cols - 1) // cols
    grid = np.full((rows * cell, cols * cell, 3), 30, np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        y0, x0 = r * cell, c * cell
        thumb = cv2.resize(t["crop_128"], (cell - 4, cell - 18))
        grid[y0 + 2:y0 + 2 + thumb.shape[0], x0 + 2:x0 + 2 + thumb.shape[1]] = thumb
        if label_fn:
            cv2.putText(grid, label_fn(t), (x0 + 3, y0 + cell - 3),
                        font, 0.38, (0, 220, 0), 1, cv2.LINE_AA)
    cv2.imwrite(str(path), grid, [cv2.IMWRITE_JPEG_QUALITY, 92])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip",      required=True)
    ap.add_argument("--endpoint", default="http://localhost:1234/v1")
    ap.add_argument("--model",    default=None)
    ap.add_argument("--workers",  type=int, default=2)
    ap.add_argument("--conf",     type=float, default=0.25)
    ap.add_argument("--out",      default="data/stage2_vlm")
    args = ap.parse_args()

    endpoint = args.endpoint.rstrip("/")
    step_dir = (ROOT / args.out / "step1")
    import shutil
    if step_dir.exists(): shutil.rmtree(step_dir)
    native_dir = step_dir / "tiles_native"
    tiles_dir  = step_dir / "tiles"
    review_dir = step_dir / "review"
    for d in (native_dir, tiles_dir, review_dir): d.mkdir(parents=True, exist_ok=True)

    try:
        model = args.model or detect_model(endpoint)
    except requests.exceptions.RequestException:
        sys.exit(f"Cannot reach LM Studio at {endpoint}. Start the server first.")
    print(f"Model: {model}  workers: {args.workers}")

    # Load zip
    zp = ROOT / args.zip if not Path(args.zip).is_absolute() else Path(args.zip)
    with zipfile.ZipFile(zp) as z:
        names = sorted(n for n in z.namelist()
                       if n.lower().endswith(('.jpg','.jpeg','.png','.webp')))
    print(f"Images in zip: {len(names)}")

    def read_img(name):
        with zipfile.ZipFile(str(zp)) as z:
            return Path(name).stem, z.read(name)

    with ThreadPoolExecutor(max_workers=8) as pool:
        image_items = list(tqdm(pool.map(read_img, names), total=len(names), desc="Loading"))

    # YOLO detection
    det = YOLO(str(S1_WEIGHTS))
    tile_jobs = []
    print(f"\nDetecting tiles ...")
    for stem, raw in tqdm(image_items, desc="Detecting"):
        img = decode(raw)
        if img is None: continue
        h, w = img.shape[:2]
        res = det.predict(source=img, conf=args.conf, imgsz=640, verbose=False)
        for idx, b in enumerate(res[0].boxes):
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            x1, y1 = max(0,x1), max(0,y1); x2, y2 = min(w,x2), min(h,y2)
            _c = padded_crop(img, x1, y1, x2-x1, y2-y1)
            crop = _c if _c is not None else img[y1:y2, x1:x2]
            safe = re.sub(r"[^\w\-]", "_", stem)
            tile_jobs.append({
                "tile_id": f"{safe}__{idx}", "stem": safe, "idx": idx,
                "bbox": [x1,y1,x2,y2], "native_crop": crop, "crop_128": letterbox_square(crop),
            })
    print(f"Total tiles detected: {len(tile_jobs)}")

    # VLM filter
    print(f"\nVLM filtering with {args.workers} workers ...")
    decisions = {}
    def filter_one(t):
        return t["tile_id"], query(endpoint, model, t["native_crop"])

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(filter_one, t): t for t in tile_jobs}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Filtering"):
            tid, dec = fut.result()
            decisions[tid] = dec

    # Save + collect results
    records, accepted, rejected = [], [], []
    for t in tile_jobs:
        dec = decisions[t["tile_id"]]
        rec = {k: v for k, v in t.items() if k not in ("native_crop", "crop_128")}
        if dec is True:
            n_dst = native_dir / f"{t['tile_id']}.jpg"
            t_dst = tiles_dir   / f"{t['tile_id']}.jpg"
            cv2.imwrite(str(n_dst), t["native_crop"], [cv2.IMWRITE_JPEG_QUALITY, 95])
            cv2.imwrite(str(t_dst), t["crop_128"],    [cv2.IMWRITE_JPEG_QUALITY, 95])
            rec.update(status="accepted",
                       native_path=n_dst.relative_to(ROOT).as_posix(),
                       crop_128_path=t_dst.relative_to(ROOT).as_posix())
            accepted.append(t)
        else:
            dst = review_dir / f"{t['tile_id']}.jpg"
            cv2.imwrite(str(dst), t["crop_128"], [cv2.IMWRITE_JPEG_QUALITY, 95])
            status = "failed" if dec is None else "rejected"
            rec.update(status=status, crop_128_path=dst.relative_to(ROOT).as_posix())
            rejected.append(t)
        records.append(rec)

    (step_dir / "results.json").write_text(json.dumps(records, indent=2), encoding="utf-8")

    save_grid(accepted, step_dir / "montage_accepted.jpg",
              label_fn=lambda t: t["stem"][:12])
    save_grid(rejected, step_dir / "montage_review.jpg",
              label_fn=lambda t: t["stem"][:12])

    print(f"\n{'='*52}")
    print(f"STEP 1 DONE  —  {len(tile_jobs)} tiles detected")
    print(f"  Accepted (real tiles) : {len(accepted)}")
    print(f"  Rejected / failed     : {len(rejected)}")
    print(f"\nReview the montages:")
    print(f"  {step_dir / 'montage_accepted.jpg'}")
    print(f"  {step_dir / 'montage_review.jpg'}")
    print(f"\nWhen satisfied → run vlm_step2_number.py")
    print(f"{'='*52}")

if __name__ == "__main__":
    main()
