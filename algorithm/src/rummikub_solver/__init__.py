"""Core Rummikub solver: tiles, DP solver, and meld validation."""

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
from .solver import solve, optimal_move, Solution, InfeasibleBoardError
from .validator import is_valid_meld, is_valid_run, is_valid_group, validate_solution

__all__ = [
    "Tile", "JOKER", "is_joker", "tile", "tiles", "fmt", "fmt_meld", "fmt_board",
    "COLOR_NAMES", "COLOR_CODES", "NUM_VALUES", "NUM_COLORS", "MAX_COPIES",
    "MAX_JOKERS",
    "solve", "optimal_move", "Solution", "InfeasibleBoardError",
    "is_valid_meld", "is_valid_run", "is_valid_group", "validate_solution",
]
