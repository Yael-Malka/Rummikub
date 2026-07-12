"""Check that a board layout is legal."""

from __future__ import annotations

from collections import Counter

from .tiles import NUM_VALUES, NUM_COLORS, MAX_JOKERS, JOKER, is_joker
from .solver import RUN_MIN, GROUP_SIZES, Solution


def _split(meld):
    """Separate real tiles from jokers in a meld list.
    Returns (real_tiles, joker_count) for run/group validation helpers.
    """
    reals = [tuple(t) for t in meld if not is_joker(t)]
    return reals, len(meld) - len(reals)


def is_valid_run(meld) -> bool:
    """True if meld is a same-color consecutive run with optional joker gaps.
    Jokers can fill missing values inside 1..13 but cannot change color.
    """
    reals, j = _split(meld)
    if len(meld) < RUN_MIN or j > MAX_JOKERS or not reals:
        return False
    if len({c for _, c in reals}) != 1:
        return False
    vals = sorted(v for v, _ in reals)
    if len(set(vals)) != len(vals):
        return False
    gaps = (vals[-1] - vals[0] + 1) - len(vals)
    if gaps > j:
        return False
    spare = j - gaps
    room = (vals[0] - 1) + (NUM_VALUES - vals[-1])
    return spare <= room


def is_valid_group(meld) -> bool:
    """True if meld is a same-number group with distinct colors, size 3 or 4.
    Jokers count toward size but real tiles must share one value.
    """
    reals, j = _split(meld)
    if len(meld) not in GROUP_SIZES or j > MAX_JOKERS or not reals:
        return False
    vals = {v for v, _ in reals}
    cols = [c for _, c in reals]
    return len(vals) == 1 and len(set(cols)) == len(cols)


def is_valid_meld(meld) -> bool:
    """True if meld is a legal run or group under Rummikub rules.
    Convenience wrapper used by validate_solution on every output meld.
    """
    return is_valid_run(meld) or is_valid_group(meld)


def validate_solution(board, hand, sol: Solution) -> bool:
    """Assert solver output is legal and conserves every tile.
    Checks each meld, then verifies new board == old board + placed tiles
    and that nothing was played from outside the hand.
    """
    board_tiles = Counter(tuple(t) for meld in board for t in meld)
    placed = Counter(tuple(t) for t in sol.placed)
    hand_cnt = Counter(tuple(t) for t in hand)

    for meld in sol.melds:
        assert is_valid_meld([tuple(t) for t in meld]), f"invalid meld: {meld}"

    new_board = Counter(tuple(t) for meld in sol.melds for t in meld)
    assert new_board == board_tiles + placed, (
        "tile conservation violated: new board != board + placed"
    )
    assert not (placed - hand_cnt), "placed tiles not available in hand"
    return True
