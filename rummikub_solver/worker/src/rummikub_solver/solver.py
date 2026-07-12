"""Rummikub move solver (DP over values 1..13).

The board is processed value by value (1 through 13). At each value we decide
how to use the tiles of that number: extend open runs, start new runs, or form
groups (sets of same value, different colors). Dynamic programming keeps the
best partial score for every reachable board state.

Public API: solve(), solve_first_drop(), optimal_move().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, combinations_with_replacement, product

from .tiles import NUM_VALUES, NUM_COLORS, MAX_COPIES, MAX_JOKERS, JOKER, Tile

# Rummikub rules encoded as constants
RUN_MIN = 3           # a run needs at least 3 consecutive tiles of one color
GROUP_SIZES = (3, 4)  # a group is 3 or 4 tiles of the same value
MAX_GROUP = 4

# How many open (incomplete) runs of one color can overlap at a single value.
# Each open run holds one slot; we have at most 2 real copies + 2 jokers per tile.
MAX_OPEN = MAX_COPIES + MAX_JOKERS

# At one value we can form at most this many groups in parallel.
# 4 colors x 2 copies + 2 jokers = 10 slots; each group needs >= 3 tiles.
MAX_GROUPS_PER_VALUE = (NUM_COLORS * MAX_COPIES + MAX_JOKERS) // RUN_MIN

_OK_SIZES = frozenset({0, *GROUP_SIZES})  # valid group sizes (0 = not started)

# Run-state encoding per color
# An open run is tracked by its current length (1, 2, or 3=complete).
# Up to MAX_OPEN runs can be open at once, giving 35 distinct states per color.
# Example: (1, 2) means one run of length 1 and one of length 2.
COLOR_STATES = tuple(
    s
    for size in range(MAX_OPEN + 1)
    for s in combinations_with_replacement((1, 2, RUN_MIN), size)
)
STATE_INDEX = {s: i for i, s in enumerate(COLOR_STATES)}
N_CS = len(COLOR_STATES)  # 35

# Pack all 4 color states + joker count into one integer key.
# Layout: [jokers_used][color3][color2][color1][color0], each color digit is 0..34.
P = tuple(N_CS ** c for c in range(NUM_COLORS))
JMULT = N_CS ** NUM_COLORS

# After processing value 13, every open run must be complete (length 3).
CLOSEABLE = frozenset(
    i for i, s in enumerate(COLOR_STATES) if all(x == RUN_MIN for x in s)
)


def _extension_assignments(lengths, target):
    """Given current run lengths, list ways to extend some runs to reach target.

    Used during reconstruction: the DP only stores counts (e, g, jr), not which
    physical run received which tile. This function picks a valid assignment.
    """
    n = len(lengths)
    tlist = list(target)
    r = len(tlist)
    for mask in range(1 << n):
        ext = [i for i in range(n) if mask >> i & 1]
        if any(lengths[i] < RUN_MIN for i in range(n) if not mask >> i & 1):
            continue  # unextended runs must already be complete (length 3)
        s = r - len(ext)
        if s < 0:
            continue
        produced = sorted([min(lengths[i] + 1, RUN_MIN) for i in ext] + [1] * s)
        if produced == tlist:
            yield ext, s


def _reachable(old, new):
    """True if run state old can become new in one DP step (one tile placed)."""
    for _ in _extension_assignments(list(old), new):
        return True
    return False


def _build_options():
    """Precompute all legal per-color transitions for one tile at one value.

    Key: (old_state_index, tiles_on_board, tiles_in_hand) for this color.
    Value: list of (new_state, tiles_to_group, tiles_to_extend, jokers_used).
    Built once at import time into OPTS.
    """
    opts = {}
    for oi, old in enumerate(COLOR_STATES):
        for t in range(MAX_COPIES + 1):          # board tiles of this (value, color)
            for h in range(MAX_COPIES + 1 - t):  # hand tiles of this (value, color)
                acc = []
                for ni, new in enumerate(COLOR_STATES):
                    if not _reachable(old, new):
                        continue
                    r = len(new)
                    for jr in range(min(r, MAX_JOKERS) + 1):  # jokers placed in runs
                        for g in range(MAX_COPIES + 1):       # tiles sent to a group
                            e = (r - jr) + g - t  # tiles used to extend runs
                            if 0 <= e <= h:
                                acc.append((ni, g, e, jr))
                opts[(oi, t, h)] = tuple(acc)
    return opts


OPTS = _build_options()

# Group-building state: track sizes of groups currently being formed at this value.
# Up to MAX_GROUPS_PER_VALUE groups can be built in parallel (sorted triple of sizes).
GP3_STATES = tuple(
    combinations_with_replacement(range(MAX_GROUP + 1), MAX_GROUPS_PER_VALUE)
)
GP3_INDEX = {s: i for i, s in enumerate(GP3_STATES)}
GP3_EMPTY = GP3_INDEX[(0,) * MAX_GROUPS_PER_VALUE]


def _compositions(total, parts):
    """Split total into parts nonnegative integers (distribute jokers across groups)."""
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in _compositions(total - first, parts - 1):
            yield (first,) + rest


def _build_gp3():
    """Precompute group transitions: add a tile to a group, finish groups with jokers."""
    nxt = [[() for _ in range(MAX_COPIES + 1)] for _ in GP3_STATES]
    fin = [[False] * (MAX_JOKERS + 1) for _ in GP3_STATES]
    for i, trip in enumerate(GP3_STATES):
        for g in range(MAX_COPIES + 1):
            outs = set()
            # Pick g distinct groups and add one tile from this color to each
            for pos in combinations(range(MAX_GROUPS_PER_VALUE), g):
                if all(trip[p] < MAX_GROUP for p in pos):
                    nt = list(trip)
                    for p in pos:
                        nt[p] += 1
                    outs.add(GP3_INDEX[tuple(sorted(nt))])
            nxt[i][g] = tuple(outs)
        for jg in range(MAX_JOKERS + 1):
            for dist in _compositions(jg, MAX_GROUPS_PER_VALUE):
                sizes = tuple(trip[k] + dist[k] for k in range(MAX_GROUPS_PER_VALUE))
                # Every group must end at size 0 (unused), 3, or 4
                if all(sz in _OK_SIZES for sz in sizes):
                    fin[i][jg] = True
                    break
    return nxt, fin


GP3_NEXT, GP3_FINISH = _build_gp3()


def _group_witness(gvec, jg):
    """Rebuild which colors belong to which group after DP finishes a value.

    gvec[c] = how many groups color c contributed to.
    jg = jokers distributed across groups at this value.
    """
    color_choices = [
        list(combinations(range(MAX_GROUPS_PER_VALUE), gvec[c]))
        for c in range(NUM_COLORS)
    ]
    for assign in product(*color_choices):
        members = [[] for _ in range(MAX_GROUPS_PER_VALUE)]
        for c, grps in enumerate(assign):
            for k in grps:
                members[k].append(c)
        base = [len(m) for m in members]
        for dist in _compositions(jg, MAX_GROUPS_PER_VALUE):
            if all(base[k] + dist[k] in _OK_SIZES and not (base[k] == 0 and dist[k])
                   for k in range(MAX_GROUPS_PER_VALUE)):
                return members, dist
    raise AssertionError("group reconstruction failed")


@dataclass
class Solution:
    """Solver output: tiles placed from hand and resulting board melds."""

    placed: list = field(default_factory=list)  # tiles taken from hand
    melds: list = field(default_factory=list)   # final board layout as list of melds
    objective: int = 0                          # score the DP optimized
    points: int = 0                             # Rummikub point total (first-drop only)

    @property
    def is_draw(self) -> bool:
        """True when the best move is to pass without placing tiles."""
        return not self.placed


class InfeasibleBoardError(ValueError):
    """Raised when the board tiles cannot be arranged into valid melds."""


def _as_tile(t) -> Tile:
    """Normalize input to (value, color) or JOKER. Accepts tuples or joker aliases."""
    try:
        v, c = t
    except (TypeError, ValueError):
        raise ValueError(f"not a tile: {t!r} (expected (value, color))") from None
    if (v, c) == JOKER or (str(v).lower(), str(c).lower()) == ("j", "j"):
        return JOKER
    try:
        v, c = int(v), int(c)
    except (TypeError, ValueError):
        raise ValueError(f"not a tile: {t!r} (expected (value, color))") from None
    if not (1 <= v <= NUM_VALUES and 0 <= c < NUM_COLORS):
        raise ValueError(f"tile out of range: {(v, c)}")
    return (v, c)


def _tile_counts(tile_list):
    """Count real (non-joker) tiles: cnt[value][color]."""
    cnt = [[0] * NUM_COLORS for _ in range(NUM_VALUES + 1)]
    for (v, c) in tile_list:
        cnt[v][c] += 1
    return cnt


def solve(board, hand, weight=None, joker_weight=None) -> Solution:
    """Find the highest-scoring legal rearrangement of board + hand tiles.

  Board melds must stay valid; any subset of the hand may be played.
  weight(v) scores each real tile of value v placed from hand (default 1).
  joker_weight scores each hand joker used (default 0 when weight is set, else 1).
    """
    # Flatten input melds into tile lists and validate counts
    board_tiles = [_as_tile(t) for meld in board for t in meld]
    hand_tiles = [_as_tile(t) for t in hand]

    jb = sum(1 for t in board_tiles if t == JOKER)
    jh = sum(1 for t in hand_tiles if t == JOKER)
    n_jokers = jb + jh
    if n_jokers > MAX_JOKERS:
        raise ValueError(f"more than {MAX_JOKERS} jokers in play")

    T = _tile_counts(t for t in board_tiles if t != JOKER)  # board counts
    H = _tile_counts(t for t in hand_tiles if t != JOKER)   # hand counts
    for v in range(1, NUM_VALUES + 1):
        for c in range(NUM_COLORS):
            if T[v][c] + H[v][c] > MAX_COPIES:
                raise ValueError(
                    f"more than {MAX_COPIES} copies of tile {(v, c)} in play"
                )

    # Scoring: w[v] per real tile of value v; wj per hand joker consumed
    w = [0] * (NUM_VALUES + 1)
    for v in range(1, NUM_VALUES + 1):
        w[v] = 1 if weight is None else weight(v)
        if w[v] < 0:
            raise ValueError("weights must be nonnegative")
    if joker_weight is None:
        wj = 1 if weight is None else 0
    else:
        wj = joker_weight
    if wj < 0:
        raise ValueError("joker weight must be nonnegative")

    # Phase 1: forward DP, one layer per value 1..13
    # dp maps packed_state_key -> best score so far.
    # parents[v] stores back-pointers to reconstruct decisions.
    # Per-color decision is packed in 6 bits: e (extend) + 3*g (group) + 9*jr (joker in run).
    # Bits 24+ hold jg (jokers spent finishing groups at this value).
    dp = {0: 0}
    parents = []
    for v in range(1, NUM_VALUES + 1):
        wv = w[v]
        layer = {}
        for s, sc in dp.items():
            layer[(s, GP3_EMPTY)] = (sc, s, 0)

        # Process each color at this value, updating run states and group progress
        for c in range(NUM_COLORS):
            mult = P[c]
            shift = 6 * c
            t_vc, h_vc = T[v][c], H[v][c]
            # Pre-fold OPTS transitions for this color's tile counts
            folded = tuple(
                tuple(
                    ((ni - oi) * mult + jr * JMULT, g, e * wv, jr,
                     (e + 3 * g + 9 * jr) << shift)
                    for (ni, g, e, jr) in OPTS[(oi, t_vc, h_vc)]
                    if jr <= n_jokers
                )
                for oi in range(N_CS)
            )
            nxt = {}
            nxt_get = nxt.get
            for (skey, gp), (sc, prev, dec) in layer.items():
                javail = n_jokers - skey // JMULT  # jokers still available
                gp_row = GP3_NEXT[gp]
                for delta, g, gain, jr, dcode in folded[skey // mult % N_CS]:
                    if jr > javail:
                        continue
                    nk = skey + delta
                    nv = sc + gain
                    nd = dec | dcode
                    for gp2 in gp_row[g]:
                        k = (nk, gp2)
                        cur = nxt_get(k)
                        if cur is None or nv > cur[0]:
                            nxt[k] = (nv, prev, nd)
            layer = nxt

        # Finish any groups at this value (optionally using jokers), collapse layer -> dp
        ndp, npar = {}, {}
        for (skey, gp), (sc, prev, dec) in layer.items():
            fin = GP3_FINISH[gp]
            javail = n_jokers - skey // JMULT
            for jg in range(min(javail, MAX_JOKERS) + 1):
                if fin[jg]:
                    fk = skey + jg * JMULT
                    cur = ndp.get(fk)
                    if cur is None or sc > cur:
                        ndp[fk] = sc
                        npar[fk] = (prev, dec | jg << 24)
        if not ndp:
            raise InfeasibleBoardError(
                "the board tiles cannot be arranged into valid melds"
            )
        dp = ndp
        parents.append(npar)

    # Phase 2: pick the best terminal state
    # Requirements: all runs closed, all board jokers used, maximize score + hand joker bonus
    best_key, best_total = None, None
    for skey, sc in dp.items():
        j_used = skey // JMULT
        if j_used < jb:
            continue  # board jokers must all be reassigned
        if all(skey // P[c] % N_CS in CLOSEABLE for c in range(NUM_COLORS)):
            total = sc + wj * (j_used - jb)
            if best_total is None or total > best_total:
                best_key, best_total = skey, total
    if best_key is None:
        raise InfeasibleBoardError(
            "the board tiles cannot be arranged into valid melds"
        )

    # Phase 3: backtrack decisions value by value (13 down to 1)
    seq = []
    cur = best_key
    for v in range(NUM_VALUES, 0, -1):
        prev, dec = parents[v - 1][cur]
        seq.append((cur, dec))
        cur = prev
    seq.reverse()

    # Phase 4: replay decisions forward to build melds and the placed-from-hand list
    melds = []
    placed = []
    active = [[] for _ in range(NUM_COLORS)]  # per color: list of open runs (each run is a list)
    for v in range(1, NUM_VALUES + 1):
        skey, dec = seq[v - 1]
        for c in range(NUM_COLORS):
            code = dec >> (6 * c) & 63
            jr_c, rem = divmod(code, 9)
            g_c, e_c = divmod(rem, 3)
            target = COLOR_STATES[skey // P[c] % N_CS]
            runs = active[c]
            try:
                ext, n_new = next(
                    _extension_assignments([len(r) for r in runs], target)
                )
            except StopIteration:
                raise AssertionError("run reconstruction failed") from None
            ext_set = set(ext)
            recipients = [runs[i] for i in ext]
            # Runs not extended close here and become finished melds
            for i, run in enumerate(runs):
                if i not in ext_set:
                    melds.append(run)
            recipients.extend([] for _ in range(n_new))
            # Place one (v,c) tile (or joker) into each recipient run
            n_rec = len(recipients)
            for idx, run in enumerate(recipients):
                run.append(JOKER if idx >= n_rec - jr_c else (v, c))
            active[c] = recipients
            placed.extend([(v, c)] * e_c)
        # Emit completed groups for this value
        jg = dec >> 24 & 15
        gvec = tuple((dec >> (6 * c) & 63) % 9 // 3 for c in range(NUM_COLORS))
        if any(gvec) or jg:
            members, jdist = _group_witness(gvec, jg)
            for k in range(MAX_GROUPS_PER_VALUE):
                if members[k]:
                    melds.append(
                        [(v, c) for c in sorted(members[k])] + [JOKER] * jdist[k]
                    )
    # Any runs still open after value 13 become melds
    for c in range(NUM_COLORS):
        melds.extend(active[c])
    placed.extend([JOKER] * (best_key // JMULT - jb))

    return Solution(placed=placed, melds=melds, objective=best_total)


def optimal_move(board, hand, weight=None, joker_weight=None) -> Solution:
    """Alias for solve() with a clearer call-site name."""
    return solve(board, hand, weight, joker_weight)


def solve_first_drop(hand, min_points: int = 30) -> Solution:
    """First opening play: hand only, must reach min_points (default 30).

    Same DP structure as solve() but with an empty board and a point cap
    instead of a tile-placement score. Returns an empty Solution if no
    legal opening exists.
    """
    if min_points <= 0:
        raise ValueError("min_points must be positive")

    hand_tiles = [_as_tile(t) for t in hand]

    n_jokers = sum(1 for t in hand_tiles if t == JOKER)
    if n_jokers > MAX_JOKERS:
        raise ValueError(f"more than {MAX_JOKERS} jokers in play")

    H = _tile_counts(t for t in hand_tiles if t != JOKER)
    for v in range(1, NUM_VALUES + 1):
        for c in range(NUM_COLORS):
            if H[v][c] > MAX_COPIES:
                raise ValueError(
                    f"more than {MAX_COPIES} copies of tile {(v, c)} in play"
                )

    # DP state: (packed_run_key, points_so_far) -> tile count placed.
    # points_so_far is capped at min_points during the sweep.
    dp = {(0, 0): 0}
    parents = []
    for v in range(1, NUM_VALUES + 1):
        # Within one value, layer also tracks uncapped tile count before groups close
        layer = {}
        for (s, p), sc in dp.items():
            layer[(s, GP3_EMPTY, 0)] = (sc, (s, p), 0)
        for c in range(NUM_COLORS):
            mult = P[c]
            shift = 6 * c
            h_vc = H[v][c]
            folded = tuple(
                tuple(
                    ((ni - oi) * mult + jr * JMULT, g, e, jr,
                     (e + 3 * g + 9 * jr) << shift)
                    for (ni, g, e, jr) in OPTS[(oi, 0, h_vc)]
                    if jr <= n_jokers
                )
                for oi in range(N_CS)
            )
            nxt = {}
            nxt_get = nxt.get
            for (skey, gp, cnt), (sc, prevkey, dec) in layer.items():
                javail = n_jokers - skey // JMULT
                gp_row = GP3_NEXT[gp]
                for delta, g, e, jr, dcode in folded[skey // mult % N_CS]:
                    if jr > javail:
                        continue
                    nk = skey + delta
                    nv = sc + e  # objective: maximize tiles placed
                    nd = dec | dcode
                    ncnt = cnt + e + jr
                    for gp2 in gp_row[g]:
                        k = (nk, gp2, ncnt)
                        cur = nxt_get(k)
                        if cur is None or nv > cur[0]:
                            nxt[k] = (nv, prevkey, nd)
            layer = nxt

        # Close groups, add v * tile_count to points, fold back to (skey, p) keys
        ndp, npar = {}, {}
        for (skey, gp, cnt), (sc, prevkey, dec) in layer.items():
            fin = GP3_FINISH[gp]
            javail = n_jokers - skey // JMULT
            for jg in range(min(javail, MAX_JOKERS) + 1):
                if fin[jg]:
                    fk = skey + jg * JMULT
                    total_cnt = cnt + jg
                    old_p = prevkey[1]
                    new_p = min(min_points, old_p + v * total_cnt)
                    nv = sc + jg
                    key = (fk, new_p)
                    cur = ndp.get(key)
                    if cur is None or nv > cur:
                        ndp[key] = nv
                        npar[key] = (prevkey, dec | jg << 24)
        dp = ndp
        parents.append(npar)

    # Need min_points reached and all runs closed
    best_key, best_total = None, None
    for (skey, p), sc in dp.items():
        if p < min_points:
            continue
        if all(skey // P[c] % N_CS in CLOSEABLE for c in range(NUM_COLORS)):
            total = sc + skey // JMULT
            if best_total is None or total > best_total:
                best_key, best_total = (skey, p), total

    if best_key is None:
        return Solution()  # no valid first-drop move

    # Backtrack and reconstruct (same logic as solve, but track Rummikub points)
    seq = []
    cur = best_key
    for v in range(NUM_VALUES, 0, -1):
        prev, dec = parents[v - 1][cur]
        seq.append((cur, dec))
        cur = prev
    seq.reverse()

    melds = []
    placed = []
    points = 0
    active = [[] for _ in range(NUM_COLORS)]
    for v in range(1, NUM_VALUES + 1):
        (skey, _p), dec = seq[v - 1]
        for c in range(NUM_COLORS):
            code = dec >> (6 * c) & 63
            jr_c, rem = divmod(code, 9)
            g_c, e_c = divmod(rem, 3)
            target = COLOR_STATES[skey // P[c] % N_CS]
            runs = active[c]
            try:
                ext, n_new = next(
                    _extension_assignments([len(r) for r in runs], target)
                )
            except StopIteration:
                raise AssertionError("run reconstruction failed") from None
            ext_set = set(ext)
            recipients = [runs[i] for i in ext]
            for i, run in enumerate(runs):
                if i not in ext_set:
                    melds.append(run)
            recipients.extend([] for _ in range(n_new))
            n_rec = len(recipients)
            for idx, run in enumerate(recipients):
                run.append(JOKER if idx >= n_rec - jr_c else (v, c))
            active[c] = recipients
            placed.extend([(v, c)] * e_c)
            points += v * (e_c + jr_c)
        jg = dec >> 24 & 15
        gvec = tuple((dec >> (6 * c) & 63) % 9 // 3 for c in range(NUM_COLORS))
        if any(gvec) or jg:
            members, jdist = _group_witness(gvec, jg)
            for k in range(MAX_GROUPS_PER_VALUE):
                if members[k]:
                    melds.append(
                        [(v, c) for c in sorted(members[k])] + [JOKER] * jdist[k]
                    )
        points += v * jg
    for c in range(NUM_COLORS):
        melds.extend(active[c])
    final_skey, _ = best_key
    placed.extend([JOKER] * (final_skey // JMULT))

    return Solution(placed=placed, melds=melds, objective=best_total, points=points)
