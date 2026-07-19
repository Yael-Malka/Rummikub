"""Group detected tiles into rows and melds."""

from __future__ import annotations

import math
import statistics
from typing import Sequence

# Thresholds (fractions of the median tile size). Tunable on real photos.
ROW_GAP_FRAC      = 0.6   # new row when |cy - row_mean| > ROW_GAP_FRAC * H
SET_GAP_FRAC      = 0.4   # fallback split when neighbour gap > SET_GAP_FRAC * W
DESKEW_MIN_DEG    = 2.0   # only de-skew if the estimated angle exceeds this


# ── basic geometry helpers ────────────────────────────────────────────────────

def _bbox(t: dict) -> tuple[float, float, float, float]:
    return tuple(float(v) for v in t["bbox"])


def _center(t: dict) -> tuple[float, float]:
    x1, y1, x2, y2 = _bbox(t)
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def estimate_tile_metrics(tiles: Sequence[dict]) -> tuple[float, float]:
    """Median tile width and height across all detections."""
    if not tiles:
        return 0.0, 0.0
    widths  = [max(1.0, x2 - x1) for (x1, y1, x2, y2) in (_bbox(t) for t in tiles)]
    heights = [max(1.0, y2 - y1) for (x1, y1, x2, y2) in (_bbox(t) for t in tiles)]
    return statistics.median(widths), statistics.median(heights)


# ── de-skew ────────────────────────────────────────────────────────────────────

def estimate_skew_angle(tiles: Sequence[dict], tile_w: float) -> float:
    """
    Estimate the dominant row tilt (radians) from the angle of each tile to its
    nearest right-hand neighbour. Tiles inside a set sit side by side, so the
    vector to the next tile in the row reveals the board's tilt.
    """
    centers = [_center(t) for t in tiles]
    angles: list[float] = []
    for i, (cx, cy) in enumerate(centers):
        best = None
        best_d = float("inf")
        for j, (ox, oy) in enumerate(centers):
            if j == i or ox <= cx:
                continue
            d = math.hypot(ox - cx, oy - cy)
            # Only trust near neighbours (likely same set) for the angle estimate.
            if d < best_d and d < 2.5 * tile_w:
                best_d, best = d, (ox - cx, oy - cy)
        if best is not None:
            angles.append(math.atan2(best[1], best[0]))
    if not angles:
        return 0.0
    return statistics.median(angles)


def deskew(tiles: Sequence[dict], tile_w: float) -> tuple[list[dict], float]:
    """
    Rotate tile *centers* by -angle so rows become horizontal. Returns new tile
    records with an added private '_c' (rotated center); original bbox untouched.
    The angle (radians) is returned so callers can report it.
    """
    angle = estimate_skew_angle(tiles, tile_w)
    out = []
    if abs(math.degrees(angle)) < DESKEW_MIN_DEG:
        # Not worth rotating; use raw centers.
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
    return t["_c"][1] if "_c" in t else _center(t)[1]


def _cx(t: dict) -> float:
    return t["_c"][0] if "_c" in t else _center(t)[0]


# ── row banding ────────────────────────────────────────────────────────────────

def band_rows(tiles: Sequence[dict], tile_h: float) -> list[list[dict]]:
    """Cluster tiles into horizontal bands by their (rotated) vertical center.

    Uses *single-linkage*: a band breaks only where the gap between two
    consecutive (sorted-by-cy) tiles exceeds the threshold: never against a
    running mean. A running mean drifts when a band is slightly tilted (residual
    skew after de-skew), which makes it break a meld mid-row and glue stray tiles
    onto the wrong band. Single-linkage tolerates that gradual drift.

    This may *over*-merge two melds that happen to share a band (their cross-band
    gap is small), but that is safe: ``split_sets_in_row`` then separates them by
    their along-row gap. Over-splitting (the running-mean failure) is the
    dangerous direction, because nothing downstream can re-join a meld.
    """
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



# ── within-row set splitting ────────────────────────────────────────────────────

def _adaptive_gap_threshold(gaps: list[float], tile_w: float) -> float:
    """
    Pick a gap threshold separating intra-set gaps (~0) from inter-set gaps (large).
    1D 2-means on the gap values; fall back to SET_GAP_FRAC * W when the gaps don't
    clearly split into two clusters.
    """
    fallback = SET_GAP_FRAC * tile_w
    pos = [g for g in gaps if g > 0]
    if len(pos) < 2:
        return fallback

    lo, hi = min(pos), max(pos)
    if hi - lo < 0.15 * tile_w:
        # All gaps similar -> either one set or evenly spaced; use fallback.
        return fallback

    c0, c1 = lo, hi  # init centroids at extremes
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
    # Threshold midway between the "touching" and "separated" clusters.
    return (c0 + c1) / 2.0


def split_sets_in_row(row: Sequence[dict], tile_w: float, angle: float = 0.0) -> list[list[dict]]:
    """Split one row (ordered left->right) into series at large horizontal gaps in rotated space."""
    if len(row) <= 1:
        return [list(row)]
    ordered = sorted(row, key=_cx)

    cos_a = abs(math.cos(-angle))
    sin_a = abs(math.sin(-angle))

    rotated_spans = []
    for t in ordered:
        x1, y1, x2, y2 = _bbox(t)
        w = x2 - x1
        h = y2 - y1
        rotated_half_w = (w * cos_a + h * sin_a) / 2.0
        cx = _cx(t)
        rotated_spans.append((cx - rotated_half_w, cx + rotated_half_w))

    gaps = []
    for i in range(len(ordered) - 1):
        ax2 = rotated_spans[i][1]
        bx1 = rotated_spans[i+1][0]
        gaps.append(max(0.0, bx1 - ax2))

    spans_w = [sp[1] - sp[0] for sp in rotated_spans]
    effective_tile_w = statistics.median(spans_w) if spans_w else tile_w

    thresh = _adaptive_gap_threshold(gaps, effective_tile_w)

    sets: list[list[dict]] = [[ordered[0]]]
    for tile, gap in zip(ordered[1:], gaps):
        if gap > thresh:
            sets.append([tile])
        else:
            sets[-1].append(tile)
    return sets


# ── orchestrator ────────────────────────────────────────────────────────────────

def _recursive_resplit(
    series: list[dict],
    score_fn,
    min_len: int = 3,
    improve_thresh: float = 0.5,
) -> list[list[dict]]:
    """
    Recursively try to find a binary split point that meaningfully improves the
    total content-fit score. Stops when no split improves by more than
    `improve_thresh` weighted tile-coverage units.

    This handles the case where two (or more) melds are geometrically touching
    (zero gap): pure geometry cannot separate them, but if they belong to
    different runs/groups the content score of each half will be much higher
    than the score of the merged sequence.
    """
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
    """
    Content-assisted refinement: for each series that might be two or more melds
    merged together by the geometric pass, try to find a better split point using
    the meld-fit score from rules.py.

    Call this after `group_tiles` with `score_fn = rules.meld_score`.
    """
    result = []
    for s in series_list:
        result.extend(_recursive_resplit(s, score_fn, min_len))
    return result


def group_tiles(tiles: Sequence[dict]) -> tuple[list[list[dict]], dict]:
    """
    Group tiles into series. Returns (series_list, meta) where each series is a
    list of tile records ordered left->right, and meta holds tile_w/tile_h/angle.
    """
    if not tiles:
        return [], {"tile_w": 0.0, "tile_h": 0.0, "skew_deg": 0.0}

    tile_w, tile_h = estimate_tile_metrics(tiles)
    rotated, angle = deskew(tiles, tile_w)
    rows           = band_rows(rotated, tile_h)

    series: list[list[dict]] = []
    for row in rows:
        for s in split_sets_in_row(row, tile_w, angle):
            # Strip the private rotated-center key before returning.
            series.append([{k: v for k, v in t.items() if k != "_c"} for t in s])

    meta = {"tile_w": tile_w, "tile_h": tile_h, "skew_deg": math.degrees(angle)}

    return series, meta
