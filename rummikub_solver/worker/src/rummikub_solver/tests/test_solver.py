"""Core solver tests: placement counts, rearrangement, weights, and error handling."""

import pytest

from rummikub_solver import (
    solve,
    tiles,
    validate_solution,
    InfeasibleBoardError,
)


def check(board, hand, expected, weight=None):
    """Run solve, validate, and assert the objective."""
    sol = solve(board, hand, weight=weight)
    validate_solution(board, hand, sol)
    if weight is None:
        assert len(sol.placed) == sol.objective
        assert sol.objective == expected
    else:
        assert sol.objective == expected
    return sol


def test_empty_everything():
    """An empty board and empty hand is a draw with no melds."""
    sol = check([], [], 0)
    assert sol.is_draw
    assert sol.melds == []


def test_hand_run_on_empty_board():
    """Place a three-tile run from the hand onto an empty board."""
    check([], tiles("1k 2k 3k 7b"), 3)


def test_draw_when_nothing_fits():
    """Return a draw when no hand tile can join the board."""
    sol = check([tiles("1k 2k 3k")], tiles("5b 9r"), 0)
    assert sol.is_draw


def test_simple_run_extension():
    """Extend an existing run by one tile from the hand."""
    check([tiles("3k 4k 5k")], tiles("6k 1b"), 1)


def test_steal_from_group_to_build_run():
    """Borrow a tile from a group to place a hand tile in a new run."""
    board = [tiles("5k 5b 5r 5o"), tiles("6r 7r 8r")]
    sol = check(board, tiles("4r"), 1)
    assert sol.placed == [(4, 2)]


def test_run_split():
    """Place multiple hand tiles by extending or splitting long runs."""
    check([tiles("1r 2r 3r 4r 5r 6r")], tiles("7r 8r"), 2)


def test_whole_hand_dump():
    """Place every tile from a six-tile hand when melds exist for all of them."""
    board = [tiles("9k 10k 11k")]
    hand = tiles("1b 2b 3b 4b 12k 13k")
    check(board, hand, 6)


def test_board_tiles_all_preserved():
    """Keep every original board tile in the rearranged solution."""
    board = [tiles("2k 3k 4k"), tiles("11r 11b 11o")]
    sol = check(board, tiles("1k 11k"), 2)
    new_tiles = sorted(t for m in sol.melds for t in m)
    expected = sorted([t for m in board for t in m] + sol.placed)
    assert new_tiles == expected


def test_infeasible_board_raises():
    """Raise InfeasibleBoardError when the board cannot be covered by valid melds."""
    with pytest.raises(InfeasibleBoardError):
        solve([tiles("1k 2k")], [])  # an invalid 2-tile "meld"


def test_too_many_copies_rejected():
    """Raise ValueError when more than two copies of a tile appear on the board."""
    with pytest.raises(ValueError):
        solve([tiles("5k 5k 5k")], [])


def test_value_weighted_objective():
    """Sum tile values as the objective when a weight function is supplied."""
    sol = check([], tiles("1k 2k 3k"), 6, weight=lambda v: v)
    assert len(sol.placed) == 3


def test_weighted_prefers_high_values():
    """Pick the higher-weight meld when count and value objectives disagree."""
    hand = tiles("1k 2k 3k 4k 5k")
    sol = solve([], hand, weight=lambda v: v)
    validate_solution([], hand, sol)
    assert sol.objective == 15  # actually all five tiles form one run 1..5
    hand = tiles("1k 2k 3k 3b 3r")  # run 1k2k3k (6) vs group 3k3b3r (9)
    sol = solve([], hand, weight=lambda v: v)
    validate_solution([], hand, sol)
    assert sol.objective == 9


def test_midgame_scenario():
    """Place at least three tiles in a realistic multi-meld mid-game position."""
    board = [
        tiles("1k 2k 3k 4k"),
        tiles("8b 9b 10b"),
        tiles("11k 11b 11r"),
        tiles("5r 6r 7r"),
        tiles("13k 13b 13o"),
    ]
    hand = tiles("5k 8r 11o 12b 1o 4b")
    sol = solve(board, hand)
    validate_solution(board, hand, sol)
    assert sol.objective >= 3
