"""Tests for the first-drop solver path."""

from __future__ import annotations

import pytest

from ..solver import solve_first_drop
from ..api import first_drop_play
from ..tiles import JOKER, is_joker, tile, tiles
from ..validator import is_valid_run, is_valid_group, validate_solution


def _meld_points(meld) -> int:
    """Independent oracle for meld point value."""
    if is_valid_group(meld):
        v = next(t[0] for t in meld if not is_joker(t))
        return v * len(meld)
    assert is_valid_run(meld), f"meld is neither a valid run nor group: {meld}"
    # Run melds list tiles in ascending value order (solver contract); a
    # joker's value is therefore derivable from its offset relative to any
    # real tile in the same meld.
    i0, v0 = next((i, t[0]) for i, t in enumerate(meld) if not is_joker(t))
    return sum(v0 + (i - i0) for i in range(len(meld)))


def _total_points(melds) -> int:
    return sum(_meld_points(m) for m in melds)


def _assert_valid_first_drop(hand, sol, min_points=30):
    """Common assertions for any non-draw first-drop result."""
    assert not sol.is_draw
    assert sol.placed  # at least one tile placed
    validate_solution([], hand, sol)  # valid melds + exact tile conservation
    assert _total_points(sol.melds) == sol.points
    assert sol.points >= min_points


def test_exactly_30_via_group_qualifies():
    hand = tiles("10k 10b 10r")  # group of 3, value 10 each = 30
    sol = solve_first_drop(hand)
    _assert_valid_first_drop(hand, sol)
    assert sol.points == 30
    assert sol.objective == 3


def test_exactly_30_via_run_qualifies():
    hand = tiles("9k 10k 11k")  # run, 9+10+11 = 30
    sol = solve_first_drop(hand)
    _assert_valid_first_drop(hand, sol)
    assert sol.points == 30
    assert sol.objective == 3


def test_under_threshold_reports_no_valid_move():
    hand = tiles("1k 2k 3k")  # only 6 points possible
    sol = solve_first_drop(hand)
    assert sol.is_draw
    assert sol.placed == []
    assert sol.melds == []
    assert sol.points == 0


def test_empty_hand_reports_no_valid_move():
    sol = solve_first_drop([])
    assert sol.is_draw
    assert sol.points == 0


# Regression for joker placement: the same single joker can complete either
# a low-value or a high-value run of equal tile count. Only the high-value
# placement reaches the 30-point threshold. A first-drop scorer that treats
# every joker with a fixed weight can miss the qualifying meld.

def test_joker_is_deployed_on_the_qualifying_meld_not_an_arbitrary_one():
    hand = tiles("1k 2k 11k 12k") + [JOKER]
    # Only two possible melds exist at all (each needs the sole joker):
    #   [1k, 2k, J=3k]  -> 6 points  (does NOT qualify)
    #   [11k, 12k, J=13k] -> 36 points (qualifies)
    # A first drop exists (the second option), so the solver must find it.
    sol = solve_first_drop(hand)
    _assert_valid_first_drop(hand, sol)
    assert sol.points == 36
    assert sol.objective == 3
    # The chosen meld must be the high-value run, not the low-value one.
    assert any(t == (1, 0) for meld in sol.melds for t in meld) is False
    assert any(t == (11, 0) for meld in sol.melds for t in meld)


def test_joker_lifts_meld_over_threshold_in_isolation():
    hand = tiles("11k 12k") + [JOKER]  # 11-12-J(=13) = 36
    sol = solve_first_drop(hand)
    _assert_valid_first_drop(hand, sol)
    assert sol.points == 36
    assert sol.objective == 3


def test_max_tiles_chosen_among_qualifying_arrangements():
    # Any 3 of these 4 tiles already form a qualifying group (30 points);
    # using all 4 also qualifies (40 points) and places one more tile.
    hand = tiles("10k 10b 10r 10o")
    sol = solve_first_drop(hand)
    _assert_valid_first_drop(hand, sol)
    assert sol.objective == 4
    assert sol.points == 40


def test_multiple_disjoint_melds_combine():
    hand = tiles("6k 7k 8k 12b 13b") + [JOKER]
    # [6,7,8]k = 21 (no joker needed) and [J=11,12,13]b = 36 can both be
    # played simultaneously (different colors -> independent runs).
    sol = solve_first_drop(hand)
    _assert_valid_first_drop(hand, sol)
    assert sol.objective == 6
    assert sol.points == 57


def test_too_many_jokers_raises():
    with pytest.raises(ValueError):
        solve_first_drop([JOKER, JOKER, JOKER])


def test_too_many_copies_raises():
    with pytest.raises(ValueError):
        solve_first_drop(tiles("5k 5k 5k"))


def test_malformed_tile_raises():
    with pytest.raises(ValueError):
        solve_first_drop([(14, 0)])  # value out of range


def test_non_positive_min_points_raises():
    with pytest.raises(ValueError):
        solve_first_drop(tiles("10k 10b 10r"), min_points=0)


def test_first_drop_play_dict_format_qualifying():
    hand = [
        {"n": 10, "c": "k"}, {"n": 10, "c": "b"}, {"n": 10, "c": "r"},
        {"n": 1, "c": "o"},  # spare, unused
    ]
    play = first_drop_play(hand)
    assert play["is_draw"] is False
    assert play["count"] == 3
    assert play["points"] == 30
    assert len(play["new_melds"]) == 1
    assert len(play["new_melds"][0]) == 3


def test_first_drop_play_dict_format_no_valid_move():
    hand = [{"n": 1, "c": "k"}, {"n": 2, "c": "k"}, {"n": 3, "c": "k"}]
    play = first_drop_play(hand)
    assert play["is_draw"] is True
    assert play["placed"] == []
    assert play["new_melds"] == []
    assert play["points"] == 0
