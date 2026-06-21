"""Draw annotated boards and dump board_state.json."""

from __future__ import annotations

import json
from pathlib import Path

import cv2

# outline colors by set status (BGR)
STATUS_COLOR = {
    "valid":        (0, 170, 0),
    "review":       (0, 140, 255),
    "incomplete":   (150, 150, 150),
}
SUGGEST_COLOR = (200, 0, 200)        # suggested label fixes
TILE_TEXT     = (255, 255, 255)
FONT          = cv2.FONT_HERSHEY_SIMPLEX

def _status(s: dict) -> str:
    """Map set dict to valid / review / incomplete."""
    if s["type"] == "incomplete":
        return "incomplete"
    return "valid" if s["valid"] else "review"

def _set_bounds(tiles: list[dict]) -> tuple[int, int, int, int]:
    """Bounding box around all tiles in a set."""
    xs1 = [t["bbox"][0] for t in tiles]; ys1 = [t["bbox"][1] for t in tiles]
    xs2 = [t["bbox"][2] for t in tiles]; ys2 = [t["bbox"][3] for t in tiles]
    return int(min(xs1)), int(min(ys1)), int(max(xs2)), int(max(ys2))

def _label(s: dict) -> str:
    """Short text label for a set header."""
    head = s["type"].upper()
    if s["type"] == "run":
        body = f"{s.get('color')}"
    elif s["type"] == "group":
        body = f"{s.get('number')}"
    else:
        body = ""
    mark = "OK" if s.get("valid") else ("--" if s["type"] == "incomplete" else "REVIEW")
    return f"#{s['id']} {head} {body} [{mark}]".strip()

def draw_board(image_bgr, sets: list[dict], meta: dict,
               target_tile_px: float = 80.0, max_scale: float = 8.0):
    """Overlay set boxes and per-tile labels; upscales if tiles are tiny."""
    tile_h = meta.get("tile_h", 0) or target_tile_px
    scale  = max(1.0, min(max_scale, target_tile_px / tile_h))
    img = cv2.resize(image_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    sc_th    = tile_h * scale
    lab_font = max(0.4, min(0.9, sc_th / 130.0))
    tile_font = max(0.35, min(0.7, sc_th / 170.0))
    box_thick = max(2, round(scale))
    pad       = max(3, round(2 * scale))

    def S(v):
        """Scale a coordinate for the upsized canvas."""
        return int(round(v * scale))

    for s in sets:
        color = STATUS_COLOR[_status(s)]
        x1, y1, x2, y2 = _set_bounds(s["tiles"])
        x1, y1, x2, y2 = S(x1), S(y1), S(x2), S(y2)
        cv2.rectangle(img, (x1 - pad, y1 - pad), (x2 + pad, y2 + pad), color, box_thick)

        # header above the set (or below if we're near the top)
        text = _label(s)
        (tw, th), _ = cv2.getTextSize(text, FONT, lab_font, 2)
        ly = y1 - pad - 4 if y1 - pad - 4 > th else y2 + pad + th + 4
        cv2.rectangle(img, (x1 - pad, ly - th - 4), (x1 - pad + tw + 6, ly + 4), color, -1)
        cv2.putText(img, text, (x1 - pad + 3, ly), FONT, lab_font, (255, 255, 255), 1, cv2.LINE_AA)

        # prediction + optional fix hint on each tile
        for t in s["tiles"]:
            bx1, by1, bx2, by2 = S(t["bbox"][0]), S(t["bbox"][1]), S(t["bbox"][2]), S(t["bbox"][3])
            pred = f"{t['number']}/{t['color'][:3]}"
            cv2.putText(img, pred, (bx1 + 1, by2 - 3), FONT, tile_font, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(img, pred, (bx1 + 1, by2 - 3), FONT, tile_font, TILE_TEXT, 1, cv2.LINE_AA)
            sug = t.get("suggestion")
            if sug:
                fix = "->" + "/".join(str(sug[k]) for k in ("number", "color") if k in sug)
                cv2.putText(img, fix, (bx1 + 1, by1 + S(tile_h) // 2), FONT, tile_font,
                            (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(img, fix, (bx1 + 1, by1 + S(tile_h) // 2), FONT, tile_font,
                            SUGGEST_COLOR, 1, cv2.LINE_AA)

    return img

def write_state(path, image_name: str, meta: dict,
                sets: list[dict], unassigned: list[dict]) -> None:
    """Write board_state.json."""
    state = {
        "image": image_name,
        "tile_px": {"w": round(meta["tile_w"], 1), "h": round(meta["tile_h"], 1)},
        "skew_deg": round(meta["skew_deg"], 2),
        "sets": sets,
        "unassigned": unassigned,
    }
    Path(path).write_text(json.dumps(state, indent=2), encoding="utf-8")
