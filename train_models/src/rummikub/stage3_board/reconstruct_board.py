"""Full board read: detect → classify → group → validate.

Writes board_annotated.jpg, tiles_classified.jpg, board_state.json.
CLI: rummikub-board <image> <out_dir>
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from rummikub.common import letterbox_square, padded_crop, preprocess_bgr
from rummikub.paths import STAGE1_WEIGHTS
from rummikub.pipeline.detect_and_classify import load_classifier
from rummikub.stage3_board import grouping, rules, visualize

def classify_probs(crop_bgr, model, num_classes, col_classes, inp_size, mean, std, device, preprocess="none"):
    """One crop → number, num_conf, color, col_conf."""
    # same preprocessing as training (see geometry.py)
    crop_bgr = letterbox_square(crop_bgr, inp_size)
    crop_bgr = preprocess_bgr(crop_bgr, preprocess)
    img = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    x = (img.astype(np.float32) / 255.0 - mean) / std
    x = torch.from_numpy(x.transpose(2, 0, 1)).unsqueeze(0).to(device)

    with torch.no_grad(), torch.autocast(device_type=device.type, dtype=torch.float16):
        nl, cl = model(x)

    npb = F.softmax(nl.float(), dim=1)[0]
    cpb = F.softmax(cl.float(), dim=1)[0]
    ni = int(npb.argmax()); ci = int(cpb.argmax())
    return num_classes[ni], float(npb[ni]), col_classes[ci], float(cpb[ci])

COLOR_BGR = {
    "black":  (80,  80,  80),
    "blue":   (220, 130,  0),
    "orange": (0,  165, 255),
    "red":    (0,   0,  200),
    "joker":  (180, 100, 180),
}

def _save_tile_sheet(img_bgr, tiles, boxes, out_path, cell=160):
    """Montage of all tile crops with preds."""
    cols = min(8, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    canvas = np.full((rows * cell, cols * cell, 3), 40, dtype=np.uint8)
    font   = cv2.FONT_HERSHEY_SIMPLEX

    for idx, t in enumerate(tiles):
        r, c = divmod(idx, cols)
        x1, y1, x2, y2 = boxes[idx]
        crop = img_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        thumb = cv2.resize(crop, (cell - 4, cell - 40), interpolation=cv2.INTER_AREA)
        cy, cx = r * cell + 2, c * cell + 2
        canvas[cy:cy + thumb.shape[0], cx:cx + thumb.shape[1]] = thumb

        # color bar under each thumb
        col_name = t["color"]
        bar_col  = COLOR_BGR.get(col_name, (160, 160, 160))
        by = r * cell + cell - 38
        cv2.rectangle(canvas, (c * cell, by), (c * cell + cell - 1, r * cell + cell - 1), bar_col, -1)

        label1 = f"{t['number']} / {col_name}"
        label2 = f"n:{t['num_conf']:.2f} c:{t['col_conf']:.2f}"
        cv2.putText(canvas, label1, (c * cell + 3, by + 16), font, 0.52, (255,255,255), 1, cv2.LINE_AA)
        cv2.putText(canvas, label2, (c * cell + 3, by + 32), font, 0.38, (220,220,220), 1, cv2.LINE_AA)

        # tile index
        cv2.putText(canvas, f"#{idx}", (c * cell + 3, r * cell + 14), font, 0.38, (200,255,200), 1, cv2.LINE_AA)

    cv2.imwrite(str(out_path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 95])

def main():
    """Run all three stages and write outputs."""
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("out_dir")
    ap.add_argument("--conf", type=float, default=0.25)
    args = ap.parse_args()

    img_path = Path(args.image)
    out_dir  = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(img_path))
    if img is None:
        sys.exit(f"Cannot read image: {img_path}")

    from ultralytics import YOLO
    print(f"Stage 1: detecting tiles in {img_path.name} ...")
    det = YOLO(str(STAGE1_WEIGHTS))
    r   = det.predict(source=str(img_path), conf=args.conf, imgsz=640, verbose=False)[0]
    n   = len(r.boxes)
    print(f"  detected {n} tiles")

    boxes, crops, det_confs = [], [], []
    for box in r.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(img.shape[1], x2); y2 = min(img.shape[0], y2)
        boxes.append((x1, y1, x2, y2))
        pc = padded_crop(img, x1, y1, x2 - x1, y2 - y1)
        crops.append(pc if pc is not None else img[y1:y2, x1:x2])
        det_confs.append(float(box.conf[0]))

    print("Stage 2: classifying crops ...")
    model, num_classes, col_classes, inp_size, mean, std, device, preprocess = load_classifier()

    def work(i):
        num, ncf, col, ccf = classify_probs(
            crops[i], model, num_classes, col_classes, inp_size, mean, std, device, preprocess)
        return i, num, ncf, col, ccf

    preds = [None] * n
    with ThreadPoolExecutor(max_workers=8) as pool:
        for fut in as_completed([pool.submit(work, i) for i in range(n)]):
            i, num, ncf, col, ccf = fut.result()
            preds[i] = (num, ncf, col, ccf)

    tiles = []
    for i in range(n):
        num, ncf, col, ccf = preds[i]
        tiles.append({
            "index": i, "bbox": list(boxes[i]),
            "number": num, "color": col,
            "det_conf": round(det_confs[i], 3),
            "num_conf": round(ncf, 3), "col_conf": round(ccf, 3),
        })

    print("Stage 3: grouping into series ...")
    series, meta = grouping.group_tiles(tiles)
    series = grouping.refine_series(series, rules.meld_score)
    print(f"  after refinement: {len(series)} series")

    sets = []
    assigned = 0
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

    unassigned: list[dict] = []   # geometry puts every tile in a series
    assert assigned + len(unassigned) == n, \
        f"tile conservation failed: {assigned}+{len(unassigned)} != {n}"

    annotated = visualize.draw_board(img, sets, meta)
    img_out   = out_dir / "board_annotated.jpg"
    cv2.imwrite(str(img_out), annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])
    visualize.write_state(out_dir / "board_state.json", img_path.name, meta, sets, unassigned)

    sheet_out = out_dir / "tiles_classified.jpg"
    _save_tile_sheet(img, tiles, boxes, sheet_out)

    n_valid  = sum(1 for s in sets if s["valid"])
    n_review = sum(1 for s in sets if not s["valid"] and s["type"] != "incomplete")
    n_inc    = sum(1 for s in sets if s["type"] == "incomplete")
    n_sug    = sum(1 for s in sets for t in s["tiles"] if t.get("suggestion"))
    print(f"\nDone. {n} tiles -> {len(sets)} series "
          f"({n_valid} valid, {n_review} needs-review, {n_inc} incomplete)")
    print(f"  skew: {meta['skew_deg']:.1f} deg | tile ~{meta['tile_w']:.0f}x{meta['tile_h']:.0f}px"
          f" | {n_sug} correction suggestion(s)")
    print(f"  -> {img_out}")
    print(f"  -> {sheet_out}")
    print(f"  -> {out_dir / 'board_state.json'}")

if __name__ == "__main__":
    main()
