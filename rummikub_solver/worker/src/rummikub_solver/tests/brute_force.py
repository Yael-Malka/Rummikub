"""Exponential brute-force reference solver, used only as a test oracle."""

from collections import Counter
from itertools import combinations

NUM_VALUES = 13
NUM_COLORS = 4
JOKER = (0, 0)


def _all_melds():
    """List every canonical meld as (real_tiles, joker_count)."""
    melds = set()
    # Runs: window [a..b] of one color; up to 2 positions filled by jokers
    # (at least one real tile must remain).  Windows are capped at length 5
    # without loss of exactness: any run of length >= 6 splits into valid
    # runs of length 3..5, and each piece keeps >= 1 real tile because at
    # most 2 jokers exist while every piece has >= 3 tiles.
    for c in range(NUM_COLORS):
        for a in range(1, NUM_VALUES + 1):
            for b in range(a + 2, min(a + 4, NUM_VALUES) + 1):
                window = range(a, b + 1)
                for q in range(min(2, b - a) + 1):
                    for jok in combinations(window, q):
                        reals = tuple(
                            (v, c) for v in window if v not in jok
                        )
                        melds.add((reals, q))
    # Groups: distinct colors of one value; jokers stand for missing colors.
    for v in range(1, NUM_VALUES + 1):
        for size in (3, 4):
            for q in range(min(2, size - 1) + 1):
                for cols in combinations(range(NUM_COLORS), size - q):
                    melds.add((tuple((v, c) for c in cols), q))
    return sorted(melds)


MELDS = _all_melds()
MELDS_WITH = {}
for _m in MELDS:
    for _t in _m[0]:
        MELDS_WITH.setdefault(_t, []).append(_m)
MELDS_WITH_JOKER = [m for m in MELDS if m[1] > 0]
# Index joker melds by each of their real tiles for faster lookup.
_JOKER_MELDS_BY_TILE = {}
for _m in MELDS_WITH_JOKER:
    for _t in _m[0]:
        _JOKER_MELDS_BY_TILE.setdefault(_t, []).append(_m)


def brute_max(board_tiles, hand_tiles):
    """Find the maximum hand tiles placeable while using every board tile."""
    board_tiles = [tuple(t) for t in board_tiles]
    hand_tiles = [tuple(t) for t in hand_tiles]
    jb0 = sum(1 for t in board_tiles if t == JOKER)
    jh0 = sum(1 for t in hand_tiles if t == JOKER)
    bd0 = dict(Counter(t for t in board_tiles if t != JOKER))
    hd0 = dict(Counter(t for t in hand_tiles if t != JOKER))
    memo = {}

    def consume(bd, hd, reals):
        """Remove reals from board then hand counts."""
        # Take board copies first: copies are indistinguishable and board
        # tiles must all be used eventually, so this is without loss.
        nbd, nhd = dict(bd), dict(hd)
        used = 0
        for t in reals:
            b = nbd.get(t, 0)
            if b:
                if b == 1:
                    del nbd[t]
                else:
                    nbd[t] = b - 1
            else:
                h = nhd.get(t, 0)
                if not h:
                    return None
                if h == 1:
                    del nhd[t]
                else:
                    nhd[t] = h - 1
                used += 1
        return nbd, nhd, used

    def rec(bd, jb, hd, jh):
        """Search meld covers for remaining board tiles and jokers."""
        if not bd and not jb:
            return hand_rec(hd, jh)
        key = (tuple(sorted(bd.items())), jb, tuple(sorted(hd.items())), jh)
        if key in memo:
            return memo[key]
        if bd:
            # Some meld must contain the smallest uncovered board tile.
            candidates = MELDS_WITH[min(bd)]
        elif hd:
            # Only board jokers remain.  Every valid meld must draw at least one
            # real tile from hd.  Union the joker-meld lists for every hand tile
            # to get all feasible candidates (deduplicated) without scanning all
            # 1464 joker melds blindly.
            seen: set = set()
            candidates = []
            for _anchor in hd:
                for _m in _JOKER_MELDS_BY_TILE.get(_anchor, []):
                    if _m not in seen:
                        seen.add(_m)
                        candidates.append(_m)
        else:
            # No real tiles left; board jokers cannot be re-melded alone.
            candidates = []
        best = -1
        for reals, q in candidates:
            if q > jb + jh:
                continue
            r = consume(bd, hd, reals)
            if r is None:
                continue
            jb_use = min(q, jb)  # board jokers first, without loss
            jh_use = q - jb_use
            sub = rec(r[0], jb - jb_use, r[1], jh - jh_use)
            if sub >= 0 and sub + r[2] + jh_use > best:
                best = sub + r[2] + jh_use
        memo[key] = best
        return best

    def hand_rec(hd, jh):
        """Maximize hand-only placements after the board is covered."""
        if not hd:
            return 0  # leftover hand jokers cannot form melds alone
        key = ("H", tuple(sorted(hd.items())), jh)
        if key in memo:
            return memo[key]
        t = min(hd)
        h2 = dict(hd)  # option 1: leave one copy of t in the hand
        if h2[t] == 1:
            del h2[t]
        else:
            h2[t] -= 1
        best = hand_rec(h2, jh)
        for reals, q in MELDS_WITH[t]:  # option 2: play t inside some meld
            if q > jh:
                continue
            r = consume({}, hd, reals)
            if r is None:
                continue
            sub = hand_rec(r[1], jh - q) + r[2] + q
            if sub > best:
                best = sub
        memo[key] = best
        return best

    return rec(bd0, jb0, hd0, jh0)
