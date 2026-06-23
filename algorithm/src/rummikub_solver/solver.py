"""DP solver for one Rummikub move with full table rearrangement."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, combinations_with_replacement, product

from .tiles import NUM_VALUES, NUM_COLORS, MAX_COPIES, MAX_JOKERS, JOKER, Tile

RUN_MIN = 3           # minimum legal run length; also the cap of the DP state
GROUP_SIZES = (3, 4)  # legal group sizes
MAX_GROUP = 4
# A run open at value v consumes one slot at (v, c): at most 2 real copies
# plus at most 2 jokers exist, so at most 4 runs of one color overlap.
MAX_OPEN = MAX_COPIES + MAX_JOKERS
# Groups of one value draw on 4 colors x 2 copies + 2 jokers = 10 slots,
# each group needs >= 3 of them: at most 3 groups per value.
MAX_GROUPS_PER_VALUE = (NUM_COLORS * MAX_COPIES + MAX_JOKERS) // RUN_MIN

_OK_SIZES = frozenset({0, *GROUP_SIZES})

# Per-color run states: multisets of capped run lengths (35 states).

COLOR_STATES = tuple(
    s
    for size in range(MAX_OPEN + 1)
    for s in combinations_with_replacement((1, 2, RUN_MIN), size)
)
STATE_INDEX = {s: i for i, s in enumerate(COLOR_STATES)}
N_CS = len(COLOR_STATES)                       # 35
P = tuple(N_CS ** c for c in range(NUM_COLORS))  # packed-state digit weights
JMULT = N_CS ** NUM_COLORS                     # joker counter lives above the digits

# Color states whose runs are all complete (length >= RUN_MIN): the only
# ones admissible after the last value has been processed.
CLOSEABLE = frozenset(
    i for i, s in enumerate(COLOR_STATES) if all(x == RUN_MIN for x in s)
)


def _extension_assignments(lengths, target):
    """Enumerate ways to extend or close open runs to reach target lengths."""
    n = len(lengths)
    tlist = list(target)
    r = len(tlist)
    for mask in range(1 << n):
        ext = [i for i in range(n) if mask >> i & 1]
        if any(lengths[i] < RUN_MIN for i in range(n) if not mask >> i & 1):
            continue  # an unextended run closes here, so it must be complete
        s = r - len(ext)
        if s < 0:
            continue
        produced = sorted([min(lengths[i] + 1, RUN_MIN) for i in ext] + [1] * s)
        if produced == tlist:
            yield ext, s


def _reachable(old, new):
    """Return True if color state old can transition to new in one step."""
    for _ in _extension_assignments(list(old), new):
        return True
    return False


def _build_options():
    """Precompute legal per-cell transitions for each color state and tile count."""
    opts = {}
    for oi, old in enumerate(COLOR_STATES):
        for t in range(MAX_COPIES + 1):
            for h in range(MAX_COPIES + 1 - t):
                acc = []
                for ni, new in enumerate(COLOR_STATES):
                    if not _reachable(old, new):
                        continue
                    r = len(new)
                    for jr in range(min(r, MAX_JOKERS) + 1):
                        for g in range(MAX_COPIES + 1):
                            e = (r - jr) + g - t
                            if 0 <= e <= h:
                                acc.append((ni, g, e, jr))
                opts[(oi, t, h)] = tuple(acc)
    return opts


OPTS = _build_options()

# Group progress: sorted triples of in-progress group sizes.

GP3_STATES = tuple(
    combinations_with_replacement(range(MAX_GROUP + 1), MAX_GROUPS_PER_VALUE)
)
GP3_INDEX = {s: i for i, s in enumerate(GP3_STATES)}
GP3_EMPTY = GP3_INDEX[(0,) * MAX_GROUPS_PER_VALUE]


def _compositions(total, parts):
    """Split total into parts nonnegative integers that sum to total."""
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in _compositions(total - first, parts - 1):
            yield (first,) + rest


def _build_gp3():
    """Build group-state transition and finish tables for the DP."""
    nxt = [[() for _ in range(MAX_COPIES + 1)] for _ in GP3_STATES]
    fin = [[False] * (MAX_JOKERS + 1) for _ in GP3_STATES]
    for i, trip in enumerate(GP3_STATES):
        for g in range(MAX_COPIES + 1):
            outs = set()
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
                # jokers-only "groups" (size from jokers alone) are rejected
                # automatically: jg <= 2 can never lift a 0 to {3, 4}.
                if all(sz in _OK_SIZES for sz in sizes):
                    fin[i][jg] = True
                    break
    return nxt, fin


GP3_NEXT, GP3_FINISH = _build_gp3()


def _group_witness(gvec, jg):
    """Rebuild concrete groups from per-color counts and joker use."""
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
    """Internal optimal move: placed hand tiles, full meld list, and score."""

    placed: list = field(default_factory=list)
    melds: list = field(default_factory=list)
    objective: int = 0

    @property
    def is_draw(self) -> bool:
        """True when no hand tile was placed."""
        return not self.placed


class InfeasibleBoardError(ValueError):
    """Raised when board tiles cannot form any legal meld layout."""


def _as_tile(t) -> Tile:
    """Normalize input to a Tile tuple or JOKER."""
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
    """Count real tiles per (value, color)."""
    cnt = [[0] * NUM_COLORS for _ in range(NUM_VALUES + 1)]
    for (v, c) in tile_list:
        cnt[v][c] += 1
    return cnt


def solve(board, hand, weight=None, joker_weight=None) -> Solution:
    """Find the best single move using internal tile tuples."""
    board_tiles = [_as_tile(t) for meld in board for t in meld]
    hand_tiles = [_as_tile(t) for t in hand]

    jb = sum(1 for t in board_tiles if t == JOKER)
    jh = sum(1 for t in hand_tiles if t == JOKER)
    n_jokers = jb + jh
    if n_jokers > MAX_JOKERS:
        raise ValueError(f"more than {MAX_JOKERS} jokers in play")

    T = _tile_counts(t for t in board_tiles if t != JOKER)
    H = _tile_counts(t for t in hand_tiles if t != JOKER)
    for v in range(1, NUM_VALUES + 1):
        for c in range(NUM_COLORS):
            if T[v][c] + H[v][c] > MAX_COPIES:
                raise ValueError(
                    f"more than {MAX_COPIES} copies of tile {(v, c)} in play"
                )

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

    # forward DP
    # dp: packed key -> best score, where key = j_used * JMULT + per-color
    # state digits (base 35).  parents[v-1]: packed key after value v ->
    # (predecessor key, packed decisions).  Decisions: 6 bits per color
    # encoding e + 3*g + 9*jr, plus jg (group jokers) in bits 24+.
    dp = {0: 0}
    parents = []
    for v in range(1, NUM_VALUES + 1):
        wv = w[v]
        layer = {}
        for s, sc in dp.items():
            layer[(s, GP3_EMPTY)] = (sc, s, 0)
        # Contract one color at a time, sharing the joker budget.
        for c in range(NUM_COLORS):
            mult = P[c]
            shift = 6 * c
            t_vc, h_vc = T[v][c], H[v][c]
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
                javail = n_jokers - skey // JMULT
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
        # Complete the value's groups (optionally with jokers) and collapse.
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

    # pick best final state
    # All open runs must be complete, all board jokers must have been used;
    # each hand joker used scores wj.
    best_key, best_total = None, None
    for skey, sc in dp.items():
        j_used = skey // JMULT
        if j_used < jb:
            continue
        if all(skey // P[c] % N_CS in CLOSEABLE for c in range(NUM_COLORS)):
            total = sc + wj * (j_used - jb)
            if best_total is None or total > best_total:
                best_key, best_total = skey, total
    if best_key is None:
        raise InfeasibleBoardError(
            "the board tiles cannot be arranged into valid melds"
        )

    # backtrack decisions
    seq = []
    cur = best_key
    for v in range(NUM_VALUES, 0, -1):
        prev, dec = parents[v - 1][cur]
        seq.append((cur, dec))
        cur = prev
    seq.reverse()

    # rebuild melds and placed tiles
    melds = []
    placed = []
    active = [[] for _ in range(NUM_COLORS)]  # per color: list of tile lists
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
            except StopIteration:  # cannot happen for a DP-certified path
                raise AssertionError("run reconstruction failed") from None
            ext_set = set(ext)
            recipients = [runs[i] for i in ext]
            for i, run in enumerate(runs):
                if i not in ext_set:  # run closes just before value v
                    melds.append(run)
            recipients.extend([] for _ in range(n_new))
            # Each recipient absorbs one slot at (v, c); the last jr_c of
            # them take jokers (capped-state equivalence makes any
            # assignment optimal -- see Lemma on replay soundness).
            n_rec = len(recipients)
            for idx, run in enumerate(recipients):
                run.append(JOKER if idx >= n_rec - jr_c else (v, c))
            active[c] = recipients
            placed.extend([(v, c)] * e_c)
        jg = dec >> 24 & 15
        gvec = tuple((dec >> (6 * c) & 63) % 9 // 3 for c in range(NUM_COLORS))
        if any(gvec) or jg:
            members, jdist = _group_witness(gvec, jg)
            for k in range(MAX_GROUPS_PER_VALUE):
                if members[k]:
                    melds.append(
                        [(v, c) for c in sorted(members[k])] + [JOKER] * jdist[k]
                    )
    for c in range(NUM_COLORS):
        melds.extend(active[c])
    placed.extend([JOKER] * (best_key // JMULT - jb))

    return Solution(placed=placed, melds=melds, objective=best_total)


def optimal_move(board, hand, weight=None, joker_weight=None) -> Solution:
    """Same as solve()."""
    return solve(board, hand, weight, joker_weight)
