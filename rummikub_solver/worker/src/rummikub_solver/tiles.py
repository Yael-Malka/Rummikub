"""Tile types and board/hand counters."""

from __future__ import annotations

NUM_VALUES = 13
NUM_COLORS = 4
MAX_COPIES = 2
MAX_JOKERS = 2

COLOR_NAMES = ("black", "blue", "red", "orange")
COLOR_CODES = "kbro"  # one-letter color codes used by the string helpers

Tile = tuple  # (value, color)

JOKER: Tile = (0, 0)


def is_joker(t) -> bool:
    return tuple(t) == JOKER


def tile(spec: str) -> Tile:
    """Parse a tile from a compact string such as ``"7r"``, ``"13k"`` or
    ``"j"`` for the joker."""
    spec = spec.strip().lower()
    if spec in ("j", "jj"):
        return JOKER
    if len(spec) < 2 or spec[-1] not in COLOR_CODES:
        raise ValueError(f"cannot parse tile spec {spec!r}")
    value = int(spec[:-1])
    color = COLOR_CODES.index(spec[-1])
    if not 1 <= value <= NUM_VALUES:
        raise ValueError(f"tile value out of range in {spec!r}")
    return (value, color)


def tiles(specs: str) -> list:
    """Parse a whitespace-separated list of tile specs, e.g. ``"1k 2k 3k"``."""
    return [tile(s) for s in specs.split()]


def fmt(t: Tile) -> str:
    if is_joker(t):
        return "j"
    return f"{t[0]}{COLOR_CODES[t[1]]}"


def fmt_meld(meld) -> str:
    return "[" + " ".join(fmt(t) for t in meld) + "]"


def fmt_board(melds) -> str:
    return "  ".join(fmt_meld(m) for m in melds)
