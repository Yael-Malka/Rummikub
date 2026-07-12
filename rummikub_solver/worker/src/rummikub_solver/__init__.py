"""Exact Rummikub single-move solver.

Main API: most_cards_down(board, hand) -> Play.
Tile: {"n": 1-13, "c": "k"|"b"|"r"|"o"}; joker {"n": "j", "c": "j"}.
"""

from .api import most_cards_down, most_tiles, first_drop_play, Play, JOKER_DICT
from .tiles import (
    Tile,
    JOKER,
    is_joker,
    tile,
    tiles,
    fmt,
    fmt_meld,
    fmt_board,
    COLOR_NAMES,
    COLOR_CODES,
    NUM_VALUES,
    NUM_COLORS,
    MAX_COPIES,
    MAX_JOKERS,
)
from .solver import solve, solve_first_drop, optimal_move, Solution, InfeasibleBoardError
from .validator import is_valid_meld, is_valid_run, is_valid_group, validate_solution

__all__ = [
    # primary public API
    "most_tiles", "most_cards_down", "first_drop_play", "Play", "JOKER_DICT",
    # low-level / advanced
    "Tile", "JOKER", "is_joker", "tile", "tiles", "fmt", "fmt_meld", "fmt_board",
    "COLOR_NAMES", "COLOR_CODES", "NUM_VALUES", "NUM_COLORS", "MAX_COPIES",
    "MAX_JOKERS",
    "solve", "solve_first_drop", "optimal_move", "Solution", "InfeasibleBoardError",
    "is_valid_meld", "is_valid_run", "is_valid_group", "validate_solution",
]
