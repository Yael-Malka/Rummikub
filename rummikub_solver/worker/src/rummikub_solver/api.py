"""Dict-oriented helpers around the core solver."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .tiles import COLOR_CODES, NUM_VALUES, NUM_COLORS, JOKER, is_joker
from .solver import solve, solve_first_drop, InfeasibleBoardError   # re-export for convenience

JOKER_DICT = {"n": "j", "c": "j"}


@dataclass
class Play:
    """Optimal move: placed, new_board, count, is_draw."""

    placed: list = field(default_factory=list)
    new_board: list = field(default_factory=list)
    count: int = 0
    is_draw: bool = True

    def to_dict(self) -> dict:
        return {
            "placed": self.placed,
            "new_board": self.new_board,
            "count": self.count,
            "is_draw": self.is_draw,
        }

    # dict-style access so callers can do play["placed"]
    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def keys(self):
        return self.to_dict().keys()

    def __repr__(self) -> str:
        if self.is_draw:
            return "Play(is_draw=True)"
        return f"Play(count={self.count}, placed={self.placed})"


_COLOR_TO_INT: dict[str, int] = {ch: i for i, ch in enumerate(COLOR_CODES)}
_INT_TO_COLOR: dict[int, str] = {i: ch for i, ch in enumerate(COLOR_CODES)}


def _tile_from_dict(d: dict) -> tuple:
    """Convert ``{"n": 5, "c": "r"}`` → internal ``(5, 2)``; the joker
    ``{"n": "j", "c": "j"}`` → ``JOKER``."""
    try:
        n_raw = d["n"]
        c_str = str(d["c"]).lower()
    except (KeyError, TypeError) as exc:
        raise ValueError(
            f"invalid tile dict {d!r}: expected {{\"n\": 1-13, \"c\": \"k\"|\"b\"|\"r\"|\"o\"}}"
            f" or the joker {{\"n\": \"j\", \"c\": \"j\"}}"
        ) from exc
    if str(n_raw).lower() == "j" or c_str == "j":
        if str(n_raw).lower() == "j" and c_str == "j":
            return JOKER
        raise ValueError(
            f"invalid tile dict {d!r}: the joker must be {{\"n\": \"j\", \"c\": \"j\"}}"
        )
    try:
        n = int(n_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid tile value {n_raw!r} in {d!r}") from exc
    if not 1 <= n <= NUM_VALUES:
        raise ValueError(f"tile value {n!r} out of range 1-{NUM_VALUES}")
    if c_str not in _COLOR_TO_INT:
        raise ValueError(
            f"unknown color {c_str!r}; use one of {list(_COLOR_TO_INT)} or \"j\""
        )
    return (n, _COLOR_TO_INT[c_str])


def _tile_to_dict(t: tuple) -> dict:
    """Convert internal ``(5, 2)`` → ``{"n": 5, "c": "r"}``; ``JOKER`` →
    ``{"n": "j", "c": "j"}``."""
    if is_joker(t):
        return dict(JOKER_DICT)
    return {"n": t[0], "c": _INT_TO_COLOR[t[1]]}


def _meld_from_dicts(meld: list) -> list:
    return [_tile_from_dict(td) for td in meld]


def _meld_to_dicts(meld: list) -> list:
    return [_tile_to_dict(t) for t in meld]


def most_cards_down(board: list, hand: list) -> Play:
    """Best move maximizing tiles placed from hand. Returns Play."""
    # Convert inputs to internal tuple format.
    internal_board = [_meld_from_dicts(meld) for meld in board]
    internal_hand = [_tile_from_dict(td) for td in hand]

    sol = solve(internal_board, internal_hand)

    placed_dicts = [_tile_to_dict(t) for t in sol.placed]
    new_board_dicts = [_meld_to_dicts(meld) for meld in sol.melds]

    return Play(
        placed=placed_dicts,
        new_board=new_board_dicts,
        count=sol.objective,
        is_draw=sol.is_draw,
    )


def _tile_key(td: dict) -> tuple:
    """Return a hashable key for a tile dict, for multiset arithmetic."""
    n = td.get("n", "")
    if str(n).lower() == "j":
        return ("j", "j")
    return (n, str(td.get("c", "")).lower())


def most_tiles(board: list, hand: list) -> tuple:
    """Best move; returns (new_board, remaining_hand)."""
    play = most_cards_down(board, hand)

    # Compute solution_hand = hand minus placed tiles (multiset subtraction).
    placed_counts: Counter = Counter(_tile_key(td) for td in play.placed)
    solution_hand: list = []
    for td in hand:
        k = _tile_key(td)
        if placed_counts[k] > 0:
            placed_counts[k] -= 1
        else:
            solution_hand.append(td)

    return play.new_board, solution_hand


def first_drop_play(hand: list, min_points: int = 30) -> dict:
    """Initial meld from hand only; min_points default 30. Returns dict."""
    internal_hand = [_tile_from_dict(td) for td in hand]

    sol = solve_first_drop(internal_hand, min_points=min_points)

    return {
        "placed": [_tile_to_dict(t) for t in sol.placed],
        "new_melds": [_meld_to_dicts(meld) for meld in sol.melds],
        "count": sol.objective,
        "points": sol.points,
        "is_draw": sol.is_draw,
    }
