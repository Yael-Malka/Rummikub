"""Joker-specific solver tests and randomized cross-checks against brute force."""

import random
from collections import Counter

import pytest

from rummikub_solver import (
    solve,
    tiles,
    JOKER,
    validate_solution,
    InfeasibleBoardError,
)

from brute_force import brute_max


def check(board, hand, expected):
    """Run solve, validate, and assert the placement count."""
    sol = solve(board, hand)
    validate_solution(board, hand, sol)
    assert len(sol.placed) == sol.objective
    assert sol.objective == expected, (board, hand, sol.objective, expected)
    return sol


def test_lone_joker_cannot_be_played():
    """Leave a lone hand joker unplaced and report a draw."""
    sol = check([], [JOKER], 0)
    assert sol.is_draw


def test_two_jokers_alone_cannot_be_played():
    """Leave two hand jokers unplaced when no real tile is available."""
    check([], [JOKER, JOKER], 0)


def test_one_real_plus_two_jokers_form_a_meld():
    """Form a valid three-tile meld from one real tile and two jokers."""
    sol = check([], tiles("5k") + [JOKER, JOKER], 3)
    assert sorted(sol.placed) == [JOKER, JOKER, (5, 0)]


def test_joker_fills_run_gap():
    """Use a joker to fill a one-step gap in a run."""
    check([], tiles("11r 13r") + [JOKER], 3)


def test_joker_extends_at_lower_boundary():
    """Place a joker at the low end of a run near value 13."""
    sol = check([], tiles("12r 13r") + [JOKER], 3)
    run = next(m for m in sol.melds if len(m) == 3)
    assert run[0] == JOKER


def test_two_jokers_bridge_a_run():
    """Bridge a run gap with two jokers between real tiles."""
    check([], tiles("3r 6r") + [JOKER, JOKER], 4)


def test_joker_joins_group_of_three():
    """Add a hand joker to an existing three-tile group."""
    board = [tiles("5k 5b 5r")]
    check(board, [JOKER], 1)


def test_joker_cannot_join_full_group_alone():
    """Place zero tiles when a lone joker cannot join a full four-color group."""
    board = [tiles("5k 5b 5r 5o")]
    sol = solve(board, [JOKER])
    validate_solution(board, [JOKER], sol)
    assert sol.objective == 0


def test_joker_as_duplicate_of_a_tile_already_in_play():
    """Use a joker as a third copy of a value already on the table in a new run."""
    board = [tiles("6r 7r 8r"), tiles("7r 8r 9r")]
    hand = tiles("5r 6r") + [JOKER]
    sol = solve(board, hand)
    validate_solution(board, hand, sol)
    assert sol.objective == 3


def test_board_joker_stays_on_table():
    """Keep a board joker on the table after a real tile replaces its slot."""
    board = [[JOKER] + tiles("5r 6r")]
    sol = check(board, tiles("4r"), 1)
    joker_count = sum(1 for m in sol.melds for t in m if t == JOKER)
    assert joker_count == 1


def test_board_joker_conservation_two_jokers():
    """Preserve two board jokers while placing hand tiles."""
    board = [[JOKER] + tiles("5r 6r"), tiles("9k 9b") + [JOKER]]
    hand = tiles("4r 9o")
    sol = solve(board, hand)
    validate_solution(board, hand, sol)
    new_board_jokers = sum(1 for m in sol.melds for t in m if t == JOKER)
    assert new_board_jokers == 2
    assert sol.objective == 2


def test_infeasible_board_with_joker():
    """Raise InfeasibleBoardError for a two-tile board meld that includes a joker."""
    with pytest.raises(InfeasibleBoardError):
        solve([[JOKER] + tiles("5r")], [])


def test_three_jokers_rejected():
    """Raise ValueError when more than two jokers appear in the position."""
    with pytest.raises(ValueError):
        solve([[JOKER] + tiles("5r 6r")], [JOKER, JOKER])


def test_joker_weight_default_zero_with_custom_weight():
    """Count zero weight for jokers under the default joker_weight with value weights."""
    hand = tiles("1k 2k 3k") + [JOKER]
    sol = solve([], hand, weight=lambda v: v)
    validate_solution([], hand, sol)
    assert sol.objective == 6


def test_joker_weight_explicit():
    """Add joker_weight to the objective when joker_weight is set explicitly."""
    hand = tiles("1k 2k 3k") + [JOKER]
    sol = solve([], hand, weight=lambda v: v, joker_weight=10)
    validate_solution([], hand, sol)
    assert sol.objective == 16


def _random_joker_instance(rng):
    """Random position that may include jokers (for brute-force cross-check)."""
    from brute_force import MELDS

    real_melds = [m for (m, q) in MELDS if q == 0 and len(m) <= 5]
    rng.shuffle(real_melds)
    cnt = Counter()
    board = []
    target = rng.randint(0, 2)
    for m in real_melds:
        if len(board) == target:
            break
        if all(cnt[t] < 2 for t in m):
            board.append(list(m))
            cnt.update(m)
    n_jokers = rng.randint(0, 2)
    board_jokers = 0
    for _ in range(n_jokers):
        if board and rng.random() < 0.5:
            for meld in board:
                colors = {c for _, c in meld}
                vals = sorted(v for v, _ in meld)
                if len(colors) == 1 and vals[-1] - vals[0] + 1 == len(vals):
                    if vals[-1] < 13:
                        meld.append(JOKER)
                        board_jokers += 1
                        break
                    if vals[0] > 1:
                        meld.insert(0, JOKER)
                        board_jokers += 1
                        break
                elif len(set(vals)) == 1 and len(meld) == 3:
                    meld.append(JOKER)
                    board_jokers += 1
                    break
    hand_jokers = n_jokers - board_jokers
    pool = []
    for v in range(1, 14):
        for c in range(4):
            pool.extend([(v, c)] * (2 - cnt[(v, c)]))
    hand = rng.sample(pool, rng.randint(0, 4)) + [JOKER] * hand_jokers
    return board, hand


def test_random_joker_instances_match_brute_force():
    """Match brute-force counts on ten random joker positions."""
    rng = random.Random(99)
    for _ in range(10):
        board, hand = _random_joker_instance(rng)
        sol = solve(board, hand)
        validate_solution(board, hand, sol)
        assert sol.objective == len(sol.placed)
        ref = brute_max([t for m in board for t in m], hand)
        assert sol.objective == ref, (board, hand, sol.objective, ref)
