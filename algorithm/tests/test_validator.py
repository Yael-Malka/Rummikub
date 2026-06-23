"""Unit tests for run, group, and meld validation helpers."""

from rummikub_solver import is_valid_run, is_valid_group, is_valid_meld, tiles


def test_valid_runs():
    """Feed consecutive same-color tile strings to is_valid_run; each call should return True."""
    assert is_valid_run(tiles("1k 2k 3k"))
    assert is_valid_run(tiles("5r 6r 7r 8r 9r"))
    assert is_valid_run(tiles("11b 12b 13b"))


def test_invalid_runs():
    """Feed short, gapped, mixed-color, or duplicate runs to is_valid_run; each call should return False."""
    assert not is_valid_run(tiles("1k 2k"))            # too short
    assert not is_valid_run(tiles("1k 2k 4k"))         # gap
    assert not is_valid_run(tiles("1k 2b 3k"))         # mixed colors
    assert not is_valid_run(tiles("5k 5k 6k 7k"))      # duplicate value


def test_valid_groups():
    """Feed same-value distinct-color groups to is_valid_group; each call should return True."""
    assert is_valid_group(tiles("7k 7b 7r"))
    assert is_valid_group(tiles("13k 13b 13r 13o"))


def test_invalid_groups():
    """Reject groups that are too small, repeat a color, or mix values."""
    assert not is_valid_group(tiles("7k 7b"))          # too small
    assert not is_valid_group(tiles("7k 7b 7b"))       # repeated color
    assert not is_valid_group(tiles("7k 7b 8r"))       # mixed values


def test_meld_dispatch():
    """Feed runs and groups to is_valid_meld; valid melds return True and invalid mixes return False."""
    assert is_valid_meld(tiles("1k 2k 3k"))
    assert is_valid_meld(tiles("7k 7b 7r 7o"))
    assert not is_valid_meld(tiles("1k 2b 3r"))
