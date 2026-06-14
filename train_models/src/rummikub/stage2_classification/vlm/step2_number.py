"""VLM pipeline step 2 — number on each tile from step1/results.json."""

import argparse, base64, importlib.util, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2, numpy as np, requests
from tqdm import tqdm

os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
from rummikub.common import letterbox_square, padded_crop

VALID_NUMBERS = {str(i) for i in range(1, 14)} | {"joker"}

SYS_PROMPT  = "You are a precise Rummikub tile reader. Answer with a single token."
USER_PROMPT = (
    "What number is printed on this Rummikub tile? "
    "Reply with ONLY the number (1 through 13) or the single word joker. "
    "No other text, no punctuation."
)

def b64(img):
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return base64.b64encode(buf.tobytes()).decode()

def detect_model(endpoint):
    r = requests.get(f"{endpoint}/models", timeout=10)
    r.raise_for_status()
    d = r.json().get("data", [])
    if not d: sys.exit("No model loaded in LM Studio.")
    for m in d:
        if any(k in m["id"].lower() for k in ("vl", "vision", "llava", "pixtral")):
            return m["id"]
    return d[0]["id"]

def _parse_number(text):
    t = text.strip().lower()
    if "joker" in t: return "joker"
    m = re.search(r'\b(1[0-3]|[1-9])\b', t)
    if m and m.group() in VALID_NUMBERS: return m.group()
    return None

def _call(endpoint, model, img):
    r = requests.post(f"{endpoint}/chat/completions", json={
        "model": model, "temperature": 0.0, "max_tokens": 8,
        "messages": [
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": USER_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64(img)}"}},
            ]},
        ],
    }, timeout=(5, 15))
    r.raise_for_status()
    return _parse_number(r.json()["choices"][0]["message"]["content"])

def query(endpoint, model, img, max_retries=6):
    """Returns number string or None (→ review). Retries on server errors."""
    delay = 2.0
    for attempt in range(max_retries):
        try:
            result = _call(endpoint, model, img)
            if result is not None:
                return result
            # Unparseable: retry without sleep (might be a weird response)
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(delay); delay = min(delay * 2, 30)
    return None

def save_grouped_montage(by_num, path, cell=128):
    """Tile grid grouped by number with a header row per group."""
    cols = 12
    font = cv2.FONT_HERSHEY_SIMPLEX
    order = [str(i) for i in range(1, 14)] + ["joker", "review"]
    rows_img = []
    for num in order:
        tiles = by_num.get(num, [])
        if not tiles: continue
        # Header strip
        hdr = np.full((28, cols * cell, 3), 20, np.uint8)
        cv2.putText(hdr, f"  {num}  ({len(tiles)} tiles)", (4, 20),
                    font, 0.65, (80, 200, 255), 1, cv2.LINE_AA)
        rows_img.append(hdr)
        # Tile rows
        n_rows = (len(tiles) + cols - 1) // cols
        band = np.full((n_rows * cell, cols * cell, 3), 35, np.uint8)
        for i, img in enumerate(tiles):
            r, c = divmod(i, cols)
            y0, x0 = r * cell, c * cell
            thumb = cv2.resize(img, (cell - 4, cell - 4))
            band[y0+2:y0+2+thumb.shape[0], x0+2:x0+2+thumb.shape[1]] = thumb
        rows_img.extend([band])

    if not rows_img: return
    total_h = sum(r.shape[0] for r in rows_img)
    canvas = np.full((total_h, cols * cell, 3), 20, np.uint8)
    y = 0
    for r in rows_img:
        canvas[y:y+r.shape[0]] = r; y += r.shape[0]
    cv2.imwrite(str(path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="http://localhost:1234/v1")
    ap.add_argument("--model",    default=None)
    ap.add_argument("--workers",  type=int, default=2)
    ap.add_argument("--out",      default="data/stage2_vlm")
    args = ap.parse_args()

    endpoint  = args.endpoint.rstrip("/")
    base_dir  = ROOT / args.out
    step1_dir = base_dir / "step1"
    step_dir  = base_dir / "step2"
    review_dir = step_dir / "review"

    if not (step1_dir / "results.json").exists():
        sys.exit("step1/results.json not found — run vlm_step1_filter.py first.")

    import shutil
    if step_dir.exists(): shutil.rmtree(step_dir)
    review_dir.mkdir(parents=True, exist_ok=True)

    try:
        model = args.model or detect_model(endpoint)
    except requests.exceptions.RequestException:
        sys.exit(f"Cannot reach LM Studio at {endpoint}.")
    print(f"Model: {model}  workers: {args.workers}")

    # Scan tiles/ directory directly — respects manual additions/removals.
    tiles_dir  = step1_dir / "tiles"
    native_dir = step1_dir / "tiles_native"
    tile_files = sorted(tiles_dir.glob("*.jpg"))
    print(f"Tiles found in step1/tiles/: {len(tile_files)}")

    jobs = []
    for tf in tile_files:
        tid = tf.stem
        native_path = native_dir / tf.name
        # Prefer native resolution for VLM; fall back to 128px crop.
        img = cv2.imread(str(native_path)) if native_path.exists() else None
        img128 = cv2.imread(str(tf))
        if img is None: img = img128       # no native → use 128px for VLM too
        if img is None: continue
        jobs.append({"tile_id": tid, "native_img": img, "crop_128": img128})

    print(f"\nVLM number identification with {args.workers} workers ...")
    results_out = {}
    def identify(j):
        return j["tile_id"], query(endpoint, model, j["native_img"])

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(identify, j): j for j in jobs}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Numbers"):
            tid, num = fut.result()
            results_out[tid] = num

    # Save crops
    records, by_num = [], {}
    n_accepted = n_review = 0
    for j in jobs:
        num = results_out.get(j["tile_id"])
        img128 = j["crop_128"] if j.get("crop_128") is not None else letterbox_square(j["native_img"])
        if num:
            dst_dir = step_dir / num
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / f"{j['tile_id']}.jpg"
            cv2.imwrite(str(dst), img128, [cv2.IMWRITE_JPEG_QUALITY, 95])
            records.append({**{k:v for k,v in j.items() if k not in ("native_img","crop_128")},
                            "number": num, "status": "accepted",
                            "crop_path": dst.relative_to(ROOT).as_posix()})
            by_num.setdefault(num, []).append(img128)
            n_accepted += 1
        else:
            dst = review_dir / f"{j['tile_id']}.jpg"
            cv2.imwrite(str(dst), img128, [cv2.IMWRITE_JPEG_QUALITY, 95])
            records.append({**{k:v for k,v in j.items() if k not in ("native_img","crop_128")},
                            "number": None, "status": "review",
                            "crop_path": dst.relative_to(ROOT).as_posix()})
            by_num.setdefault("review", []).append(img128)
            n_review += 1

    (step_dir / "results.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    save_grouped_montage(by_num, step_dir / "montage.jpg")

    print(f"\n{'='*52}")
    print(f"STEP 2 DONE  —  {len(jobs)} tiles")
    print(f"  Number identified : {n_accepted}")
    print(f"  Review            : {n_review}")
    print(f"\nPer-number breakdown:")
    for n in [str(i) for i in range(1,14)] + ["joker"]:
        c = len(by_num.get(n, []))
        if c: print(f"  {n:>5} : {c}")
    print(f"\nReview montage (grouped by number):")
    print(f"  {step_dir / 'montage.jpg'}")
    print(f"\nWhen satisfied -> run vlm_step3_color.py")
    print(f"{'='*52}")

if __name__ == "__main__":
    main()
