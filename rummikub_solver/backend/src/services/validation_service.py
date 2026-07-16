"""Validate corrected board JSON from the client."""

from typing import List, Dict
from src.services.rules import fit_meld


def validate_tile(tile: Dict) -> None:
    """Check one tile dict has allowed color/number values.
    Jokers must have both fields set to 'joker': half-joker rows usually
    mean a bad edit or a bad export from recognition.
    """
    color = tile.get("color")
    number = tile.get("number")
    
    valid_colors = {"red", "blue", "black", "orange", "joker"}
    valid_numbers = {str(i) for i in range(1, 14)} | {"joker"}
    
    if color not in valid_colors:
        raise ValueError(f"Invalid tile color: '{color}'. Permitted: {sorted(valid_colors)}")
    if number not in valid_numbers:
        raise ValueError(f"Invalid tile number: '{number}'. Permitted: {sorted(valid_numbers)}")
        
    if (color == "joker" or number == "joker") and (color != "joker" or number != "joker"):
        raise ValueError("Joker tile must have both color and number set to 'joker'")


def validate_board_layout(sets: List[Dict], unassigned: List[Dict], hand: List[Dict]) -> None:
    """Validate a full corrected layout before save or solve.
    Every table tile must sit in a set of at least 3 tiles that passes fit_meld().
    Unassigned tiles on the table are rejected: move them into a set or hand.
    """
    if unassigned:
        raise ValueError("Board correction cannot contain unassigned tiles on the table")
        
    for idx, tile in enumerate(hand):
        try:
            validate_tile(tile)
        except ValueError as e:
            raise ValueError(f"Invalid tile in hand at index {idx}: {str(e)}")
            
    for set_idx, set_obj in enumerate(sets):
        if not isinstance(set_obj, dict) or "tiles" not in set_obj:
            raise ValueError(f"Set at index {set_idx} is malformed; must contain a 'tiles' list")
            
        tiles = set_obj["tiles"]
        if not isinstance(tiles, list):
            raise ValueError(f"Set at index {set_idx} tiles must be a list")
            
        if len(tiles) < 3:
            raise ValueError(f"Set at index {set_idx} contains only {len(tiles)} tile(s); a set needs at least 3 tiles")
            
        for tile_idx, tile in enumerate(tiles):
            try:
                validate_tile(tile)
            except ValueError as e:
                raise ValueError(f"Invalid tile in set {set_idx} at index {tile_idx}: {str(e)}")
                
        meld_res = fit_meld(tiles)
        if not meld_res.get("valid"):
            reason = meld_res.get("reason", "unknown error")
            raise ValueError(f"Set at index {set_idx} is not a valid run or group: {reason}")
