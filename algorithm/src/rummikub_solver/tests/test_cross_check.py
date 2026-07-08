"""Randomized equivalence tests comparing the DP solver to the brute-force oracle."""

import random
from collections import Counter

from rummikub_solver import solve, validate_solution

from brute_force import brute_max, MELDS


def random_instance(rng, n_melds, hand_size):
    """Random feasible board + hand for property tests."""
    cnt = Counter()
    board = []
    candidates = [reals for (reals, q) in MELDS if q == 0]
    rng.shuffle(candidates)
    for m in candidates:
        if len(board) == n_melds:
            break
        if all(cnt[t] < 2 for t in m):
            board.append(list(m))
            cnt.update(m)
    pool = []
    for v in range(1, 14):
        for c in range(4):
            pool.extend([(v, c)] * (2 - cnt[(v, c)]))
    hand = rng.sample(pool, hand_size)
    return board, hand


def test_random_instances_match_brute_force():
    """Match brute-force placement counts on 60 random board-plus-hand instances."""
    rng = random.Random(20260612)
    for _ in range(60):
        board, hand = random_instance(rng, rng.randint(0, 3), rng.randint(0, 6))
        sol = solve(board, hand)
        validate_solution(board, hand, sol)
        assert sol.objective == len(sol.placed)
        ref = brute_max([t for m in board for t in m], hand)
        assert sol.objective == ref, (board, hand, sol.objective, ref)


def test_hand_only_instances_match_brute_force():
    """Match brute-force placement counts on 30 random hand-only instances."""
    rng = random.Random(77)
    for _ in range(30):
        _, hand = random_instance(rng, 0, rng.randint(0, 8))
        sol = solve([], hand)
        validate_solution([], hand, sol)
        ref = brute_max([], hand)
        assert sol.objective == ref, (hand, sol.objective, ref)
