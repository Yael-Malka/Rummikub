"""Step 3: read tile color and write the final manifest under step3/."""

import argparse, base64, csv, importlib.util, json, os, re, sys, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2, numpy as np, requests
from tqdm import tqdm

os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
from rummikub.common import letterbox_square, padded_crop

VALID_COLORS = {"black", "blue", "orange", "red"}

SYS_PROMPT  = "You are a precise Rummikub tile reader. Answer with a single word."
USER_PROMPT = (
    "What color is the number (or joker symbol) printed on this Rummikub tile? "
    "Reply with ONLY one word: black, blue, orange, or red. "
    "Orange is a warm amber/golden tone. Red is a vivid deep red. "
    "No other text."
)

def b64(img):
    """Encode a BGR image as a base64 JPEG string."""
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return base64.b64encode(buf.tobytes()).decode()

def detect_model(endpoint):
    """Pick a vision-capable model from the LM Studio server."""
    r = requests.get(f"{endpoint}/models", timeout=10)
    r.raise_for_status()
    d = r.json().get("data", [])
    if not d: sys.exit("No model loaded in LM Studio.")
    for m in d:
        if any(k in m["id"].lower() for k in ("vl", "vision", "llava", "pixtral")):
            return m["id"]
    return d[0]["id"]

def _parse_color(text):
    """Pull a valid color name out of VLM text."""
    t = text.strip().lower()
    for c in VALID_COLORS:
        if c in t: return c
    return None

def _call(endpoint, model, img):
    """One VLM call; returns parsed color or None."""
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
    return _parse_color(r.json()["choices"][0]["message"]["content"])

def query(endpoint, model, img, max_retries=8):
    """Returns color string or None; retries on errors with backoff."""
    delay = 1.0
    for attempt in range(max_retries):
        try:
            result = _call(endpoint, model, img)
            if result is not None:
                return result
            time.sleep(0.5)
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay = min(delay * 2, 15)
    return None

COLOR_BGR = {"black": (80,80,80), "blue": (220,130,0), "orange": (0,165,255),
             "red": (0,0,220), "unknown": (60,60,180)}

def save_grid_montage(by_num_col, path, cell=96):
    """Grid montage: rows = numbers, columns = colors."""
    numbers = [str(i) for i in range(1, 14)] + ["joker"]
    colors  = ["black", "blue", "orange", "red", "unknown"]
    font    = cv2.FONT_HERSHEY_SIMPLEX
    max_per_cell = 6      # max thumbnails per (number, color) cell
    sub = cell // 3       # thumbnail size within a cell

    total_w = (len(colors) + 1) * cell  # +1 for row label
    total_h = (len(numbers) + 1) * cell  # +1 for col header
    canvas = np.full((total_h, total_w, 3), 25, np.uint8)

    for ci, col in enumerate(colors):
        x0 = (ci + 1) * cell
        cv2.rectangle(canvas, (x0, 0), (x0 + cell - 2, cell - 2), COLOR_BGR[col], -1)
        cv2.putText(canvas, col[:3], (x0 + 4, cell // 2 + 6), font, 0.55, (255,255,255), 1, cv2.LINE_AA)

    for ri, num in enumerate(numbers):
        y0 = (ri + 1) * cell
        cv2.putText(canvas, num, (4, y0 + cell // 2 + 6), font, 0.65, (200,200,200), 1, cv2.LINE_AA)
        for ci, col in enumerate(colors):
            imgs = (by_num_col.get(num) or {}).get(col, [])
            x0 = (ci + 1) * cell
            count = min(len(imgs), max_per_cell)
            for k in range(count):
                kr, kc = divmod(k, 3)
                tx, ty = x0 + kc * sub + 1, y0 + kr * sub + 1
                thumb = cv2.resize(imgs[k], (sub - 2, sub - 2))
                canvas[ty:ty+thumb.shape[0], tx:tx+thumb.shape[1]] = thumb
            if count:
                cv2.putText(canvas, str(len(imgs)), (x0 + cell - 22, y0 + cell - 4),
                            font, 0.4, COLOR_BGR[col], 1, cv2.LINE_AA)

    cv2.imwrite(str(path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])

def main():
    """Label colors and write step3 manifest."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="http://localhost:1234/v1")
    ap.add_argument("--model",    default=None)
    ap.add_argument("--workers",  type=int, default=2)
    ap.add_argument("--out",      default="data/stage2_vlm")
    args = ap.parse_args()

    endpoint  = args.endpoint.rstrip("/")
    base_dir  = ROOT / args.out
    step2_dir = base_dir / "step2"
    step_dir  = base_dir / "step3"

    if not step2_dir.exists():
        sys.exit("step2/ not found — run vlm_step2_number.py first.")

    import shutil
    if step_dir.exists(): shutil.rmtree(step_dir)
    step_dir.mkdir(parents=True, exist_ok=True)

    try:
        model = args.model or detect_model(endpoint)
    except requests.exceptions.RequestException:
        sys.exit(f"Cannot reach LM Studio at {endpoint}.")
    print(f"Model: {model}  workers: {args.workers}")

    step1_dir  = base_dir / "step1"
    native_dir = step1_dir / "tiles_native"
    valid_nums = [str(i) for i in range(1, 14)] + ["joker"]

    jobs = []
    for num in valid_nums:
        num_dir = step2_dir / num
        if not num_dir.is_dir():
            continue
        for tf in sorted(num_dir.glob("*.jpg")):
            tid   = tf.stem
            img128 = cv2.imread(str(tf))
            native_path = native_dir / f"{tid}.jpg"
            img = cv2.imread(str(native_path)) if native_path.exists() else None
            if img is None:
                img = img128
            if img is None:
                continue
            jobs.append({"tile_id": tid, "number": num,
                         "native_img": img, "img128": img128})

    print(f"Tiles from step2 folders: {len(jobs)}")

    joker_jobs  = [j for j in jobs if j["number"] == "joker"]
    color_jobs  = [j for j in jobs if j["number"] != "joker"]

    print(f"\nVLM color identification with {args.workers} workers ...")
    print(f"  {len(color_jobs)} tiles need color, {len(joker_jobs)} jokers (auto-labeled)")

    results_out = {j["tile_id"]: "joker" for j in joker_jobs}

    def identify(j):
        img = j["img128"] if j["img128"] is not None else j["native_img"]
        return j["tile_id"], query(endpoint, model, img)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(identify, j): j for j in color_jobs}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Colors"):
            tid, col = fut.result()
            results_out[tid] = col

    records, manifest_rows = [], []
    by_num_col = {}
    for j in jobs:
        col = results_out.get(j["tile_id"])
        num = j["number"]
        effective_col = col if col else "unknown"
        if num == "joker": effective_col = "joker"

        dst_dir = step_dir / num / effective_col
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / f"{j['tile_id']}.jpg"
        cv2.imwrite(str(dst), j["img128"], [cv2.IMWRITE_JPEG_QUALITY, 95])

        rec = {k:v for k,v in j.items() if k not in ("native_img","img128")}
        rec.update(color=effective_col, final_path=dst.relative_to(ROOT).as_posix())
        records.append(rec)

        by_num_col.setdefault(num, {}).setdefault(effective_col, []).append(j["img128"])

        if effective_col != "unknown":
            manifest_rows.append({
                "filepath": dst.relative_to(ROOT).as_posix(),
                "number": num, "color": effective_col,
                "source": "vlm", "split": "train",
            })

    (step_dir / "results.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    with open(step_dir / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filepath","number","color","source","split"])
        w.writeheader(); w.writerows(manifest_rows)

    save_grid_montage(by_num_col, step_dir / "montage.jpg")

    n_colored  = sum(1 for r in records if r["color"] != "unknown")
    n_unknown  = sum(1 for r in records if r["color"] == "unknown")
    cls = Counter((r["number"], r["color"]) for r in records if r["color"] != "unknown")

    print(f"\n{'='*52}")
    print(f"STEP 3 DONE  —  {len(jobs)} tiles processed")
    print(f"  Color identified : {n_colored}")
    print(f"  Unknown color    : {n_unknown}  (in <number>/unknown/)")
    print(f"  Manifest entries : {len(manifest_rows)}")
    print(f"\nClass counts (in manifest):")
    for num in [str(i) for i in range(1,14)] + ["joker"]:
        row = {col: cls.get((num,col),0) for col in ["black","blue","orange","red","joker"]}
        if any(row.values()):
            line = "  ".join(f"{c[:3]}={v}" for c,v in row.items() if v)
            print(f"  {num:>5} : {line}")
    print(f"\nReview grid (number × color):")
    print(f"  {step_dir / 'montage.jpg'}")
    print(f"\nFinal manifest: {step_dir / 'manifest.csv'}")
    print(f"{'='*52}")

if __name__ == "__main__":
    main()
