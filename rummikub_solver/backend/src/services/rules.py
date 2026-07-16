"""Meld validation (mirror of worker rules)."""

from __future__ import annotations
import statistics
from collections import Counter
from typing import Sequence

CONF_SUGGEST = 0.60
MIN_MELD_LEN = 3
MAX_GROUP_LEN = 4
JOKER = "joker"


def _num(t: dict) -> int | None:
    """Predicted number as int, or None for jokers / unparseable."""
    v = t.get("number")
    if v is None or v == JOKER:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _is_joker(t: dict) -> bool:
    return t.get("number") == JOKER or t.get("color") == JOKER


def _weighted_vote(pairs: list[tuple[object, float]]):
    """Return the value with the highest summed weight (ties -> highest single)."""
    score: dict = {}
    for val, w in pairs:
        score[val] = score.get(val, 0.0) + w
    return max(score, key=score.get) if score else None


# ── RUN hypothesis ───────────────────────────────────────────────────────────

def _fit_run(series: Sequence[dict]) -> dict:
    n = len(series)
    nonjok = [t for t in series if not _is_joker(t)]

    run_color = _weighted_vote([(t["color"], t.get("col_conf", 1.0)) for t in nonjok])

    # Anchor the sequence: base = median(predicted_number_i - position_i).
    offsets = [_num(t) - i for i, t in enumerate(series) if _num(t) is not None]
    base = round(statistics.median(offsets)) if offsets else 1

    expected = [base + i for i in range(n)]
    in_range = all(1 <= e <= 13 for e in expected)

    suggestions: dict[int, dict] = {}
    ok = 0
    for i, t in enumerate(series):
        if _is_joker(t):
            ok += 1
            continue
        exp = expected[i]
        num_ok = _num(t) == exp
        col_ok = t["color"] == run_color
        if num_ok and col_ok:
            ok += 1
            continue
        sug: dict = {}
        if not num_ok and t.get("num_conf", 1.0) < CONF_SUGGEST and 1 <= exp <= 13:
            sug["number"] = str(exp)
        if not col_ok and t.get("col_conf", 1.0) < CONF_SUGGEST:
            sug["color"] = run_color
        if sug:
            sug["reason"] = f"run {run_color} expects {exp} here"
            suggestions[i] = sug

    score = ok / n if n else 0.0
    seq = "-".join("_" if _is_joker(t) else str(expected[i]) for i, t in enumerate(series))
    valid = n >= MIN_MELD_LEN and in_range and score == 1.0
    return {
        "type": "run", "valid": valid, "color": run_color, "number": None,
        "reason": f"{run_color} {seq}" + ("" if in_range else " (out of range)"),
        "suggestions": suggestions, "_score": score,
    }


# ── GROUP hypothesis ─────────────────────────────────────────────────────────

def _fit_group(series: Sequence[dict]) -> dict:
    n = len(series)
    nonjok = [t for t in series if not _is_joker(t)]

    grp_num = _weighted_vote([(_num(t), t.get("num_conf", 1.0))
                              for t in nonjok if _num(t) is not None])

    # Colors already used confidently: duplicates should pick a different color.
    used = Counter(t["color"] for t in nonjok)
    all_colors = ["black", "blue", "orange", "red"]

    suggestions: dict[int, dict] = {}
    ok = 0
    seen: set[str] = set()
    for i, t in enumerate(series):
        if _is_joker(t):
            ok += 1
            continue
        num_ok = _num(t) == grp_num
        col_ok = t["color"] not in seen          # distinct within the group
        if num_ok and col_ok:
            ok += 1
            seen.add(t["color"])
            continue
        sug: dict = {}
        if not num_ok and t.get("num_conf", 1.0) < CONF_SUGGEST and grp_num is not None:
            sug["number"] = str(grp_num)
        if not col_ok and t.get("col_conf", 1.0) < CONF_SUGGEST:
            free = [c for c in all_colors if c not in seen and used.get(c, 0) == 0]
            if free:
                sug["color"] = free[0]
        if sug:
            sug["reason"] = f"group of {grp_num} needs distinct colors"
            suggestions[i] = sug
        else:
            seen.add(t["color"])

    score = ok / n if n else 0.0
    valid = (MIN_MELD_LEN <= n <= MAX_GROUP_LEN and grp_num is not None
             and score == 1.0 and len({t["color"] for t in nonjok}) == len(nonjok))
    return {
        "type": "group", "valid": valid, "color": None, "number": grp_num,
        "reason": f"group of {grp_num}" + ("" if valid else " (mismatch)"),
        "suggestions": suggestions, "_score": score,
    }


def fit_meld(series: Sequence[dict]) -> dict:
    """Classify a spatial series and attach advisory correction suggestions."""
    n = len(series)
    if n < MIN_MELD_LEN:
        return {
            "type": "incomplete", "valid": False, "color": None, "number": None,
            "reason": f"only {n} tile(s); a meld needs {MIN_MELD_LEN}+",
            "suggestions": {},
        }

    run = _fit_run(series)
    grp = _fit_group(series)
    best = run if run["_score"] >= grp["_score"] else grp

    if not best["valid"] and best["_score"] < 1.0:
        best = {**best, "reason": best["reason"] + ": needs-review"}

    best.pop("_score", None)
    return best
