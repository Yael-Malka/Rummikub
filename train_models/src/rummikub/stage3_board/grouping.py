"""Turn detected tiles into rows and horizontal sets using bbox layout."""

from __future__ import annotations

import math
import statistics
from typing import Sequence

ROW_GAP_FRAC      = 0.6   # vertical gap (× tile height) that starts a new row
SET_GAP_FRAC      = 0.4   # horizontal gap (× tile width) that splits a set
DESKEW_MIN_DEG    = 2.0   # ignore tiny camera tilt below this

def _bbox(t: dict) -> tuple[float, float, float, float]:
    """x1, y1, x2, y2 from a tile dict."""
    return tuple(float(v) for v in t["bbox"])

def _center(t: dict) -> tuple[float, float]:
    """BBox center."""
    x1, y1, x2, y2 = _bbox(t)
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0

def estimate_tile_metrics(tiles: Sequence[dict]) -> tuple[float, float]:
    """Median tile width and height across all boxes."""
    if not tiles:
        return 0.0, 0.0
    widths  = [max(1.0, x2 - x1) for (x1, y1, x2, y2) in (_bbox(t) for t in tiles)]
    heights = [max(1.0, y2 - y1) for (x1, y1, x2, y2) in (_bbox(t) for t in tiles)]
    return statistics.median(widths), statistics.median(heights)

def estimate_skew_angle(tiles: Sequence[dict], tile_w: float) -> float:
    """Guess board tilt in radians from nearby tile pairs."""
    centers = [_center(t) for t in tiles]
    angles: list[float] = []
    for i, (cx, cy) in enumerate(centers):
        best = None
        best_d = float("inf")
        for j, (ox, oy) in enumerate(centers):
            if j == i or ox <= cx:
                continue
            d = math.hypot(ox - cx, oy - cy)
            # stick to close neighbours — probably same run
            if d < best_d and d < 2.5 * tile_w:
                best_d, best = d, (ox - cx, oy - cy)
        if best is not None:
            angles.append(math.atan2(best[1], best[0]))
    if not angles:
        return 0.0
    return statistics.median(angles)

def deskew(tiles: Sequence[dict], tile_w: float) -> tuple[list[dict], float]:
    """Rotate tile centers to straighten rows; stores _c on each tile, bbox unchanged."""
    angle = estimate_skew_angle(tiles, tile_w)
    out = []
    if abs(math.degrees(angle)) < DESKEW_MIN_DEG:
        # angle too small — skip rotation
        for t in tiles:
            t2 = dict(t)
            t2["_c"] = _center(t)
            out.append(t2)
        return out, 0.0

    cos_a, sin_a = math.cos(-angle), math.sin(-angle)
    for t in tiles:
        cx, cy = _center(t)
        out.append({**t, "_c": (cx * cos_a - cy * sin_a, cx * sin_a + cy * cos_a)})
    return out, angle

def _cy(t: dict) -> float:
    """Y center (deskewed if available)."""
    return t["_c"][1] if "_c" in t else _center(t)[1]

def _cx(t: dict) -> float:
    """X center (deskewed if available)."""
    return t["_c"][0] if "_c" in t else _center(t)[0]

def band_rows(tiles: Sequence[dict], tile_h: float) -> list[list[dict]]:
    """Group tiles into rows by how far apart they sit vertically."""
    if not tiles:
        return []
    ordered = sorted(tiles, key=_cy)
    thresh  = ROW_GAP_FRAC * tile_h
    rows: list[list[dict]] = [[ordered[0]]]
    for prev, t in zip(ordered, ordered[1:]):
        if _cy(t) - _cy(prev) > thresh:
            rows.append([t])
        else:
            rows[-1].append(t)
    return rows

def _adaptive_gap_threshold(gaps: list[float], tile_w: float) -> float:
    """Pick a gap cutoff with simple 2-cluster means, else use SET_GAP_FRAC."""
    fallback = SET_GAP_FRAC * tile_w
    pos = [g for g in gaps if g > 0]
    if len(pos) < 2:
        return fallback

    lo, hi = min(pos), max(pos)
    if hi - lo < 0.15 * tile_w:
        # gaps all look the same — fall back to fixed fraction
        return fallback

    c0, c1 = lo, hi  # start at min/max gap
    for _ in range(20):
        g0 = [g for g in pos if abs(g - c0) <= abs(g - c1)]
        g1 = [g for g in pos if abs(g - c0) >  abs(g - c1)]
        if not g0 or not g1:
            break
        n0, n1 = statistics.mean(g0), statistics.mean(g1)
        if abs(n0 - c0) < 1e-6 and abs(n1 - c1) < 1e-6:
            c0, c1 = n0, n1
            break
        c0, c1 = n0, n1
    # split point between tight and loose gaps
    return (c0 + c1) / 2.0

def split_sets_in_row(row: Sequence[dict], tile_w: float) -> list[list[dict]]:
    """Break one row into separate horizontal sets by gap size."""
    if len(row) <= 1:
        return [list(row)]
    ordered = sorted(row, key=_cx)

    gaps = []
    for a, b in zip(ordered, ordered[1:]):
        ax2 = _bbox(a)[2]
        bx1 = _bbox(b)[0]
        gaps.append(max(0.0, bx1 - ax2))  # overlapping boxes → gap 0

    thresh = _adaptive_gap_threshold(gaps, tile_w)

    sets: list[list[dict]] = [[ordered[0]]]
    for tile, gap in zip(ordered[1:], gaps):
        if gap > thresh:
            sets.append([tile])
        else:
            sets[-1].append(tile)
    return sets

def _recursive_resplit(
    series: list[dict],
    score_fn,
    min_len: int = 3,
    improve_thresh: float = 0.5,
) -> list[list[dict]]:
    """Try splitting a long series if meld_score gets better."""
    n = len(series)
    if n < min_len * 2:
        return [series]

    base_score = score_fn(series) * n
    best_score  = base_score
    best_i      = None

    for i in range(min_len, n - min_len + 1):
        left, right = series[:i], series[i:]
        s = score_fn(left) * len(left) + score_fn(right) * len(right)
        if s > best_score + improve_thresh:
            best_score = s
            best_i     = i

    if best_i is None:
        return [series]

    return (
        _recursive_resplit(series[:best_i], score_fn, min_len, improve_thresh)
        + _recursive_resplit(series[best_i:], score_fn, min_len, improve_thresh)
    )

def refine_series(
    series_list: list[list[dict]],
    score_fn,
    min_len: int = 3,
) -> list[list[dict]]:
    """Re-split each series where the rules scorer likes a break."""
    result = []
    for s in series_list:
        result.extend(_recursive_resplit(s, score_fn, min_len))
    return result

def group_tiles(tiles: Sequence[dict]) -> tuple[list[list[dict]], dict]:
    """Full pipeline: deskew → rows → sets. Returns series list + size/skew meta."""
    if not tiles:
        return [], {"tile_w": 0.0, "tile_h": 0.0, "skew_deg": 0.0}

    tile_w, tile_h = estimate_tile_metrics(tiles)
    rotated, angle = deskew(tiles, tile_w)
    rows           = band_rows(rotated, tile_h)

    series: list[list[dict]] = []
    for row in rows:
        for s in split_sets_in_row(row, tile_w):
            # drop internal _c before we hand tiles back
            series.append([{k: v for k, v in t.items() if k != "_c"} for t in s])

    meta = {"tile_w": tile_w, "tile_h": tile_h, "skew_deg": math.degrees(angle)}
    return series, meta
