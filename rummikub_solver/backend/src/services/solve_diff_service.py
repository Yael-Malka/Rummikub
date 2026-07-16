"""Turn solver output to UI move list."""

import uuid
from typing import List, Dict, Any, Tuple
from src.models.play import TileMove, Tile, BoardSet, SolveResult

def _get_tile_key(tile: dict) -> Tuple[str, str]:
    c = str(tile.get("color", "")).lower()
    n = str(tile.get("number", "0")).lower()
    if c == "joker" or n == "joker":
        return ("joker", "joker")
    return (c, n)

def _get_set_signature(tiles: List[dict]) -> tuple:
    return tuple(_get_tile_key(t) for t in tiles)

def generate_moves(initial_sets: List[dict], initial_hand: List[dict], solution_dict: dict) -> SolveResult:
    """Build TileMove steps by comparing pre-solve state to the solution.
    Matches unchanged sets by tile signature, then emits moves for tiles that
    moved from hand to board or between sets. solution_dict uses solver keys
    new_board and placed.
    """
    
    # 1. Ensure all initial tiles and sets have IDs
    board_tiles_pool = {}  # key -> list of (tile_dict, original_set_id)
    hand_tiles_pool = {}   # key -> list of tile_dict
    
    # Map solver format to standard format helper
    def map_solver_to_std(t: dict) -> dict:
        color_map = {"k": "black", "b": "blue", "r": "red", "o": "orange", "j": "joker"}
        c = color_map.get(str(t.get("c")), "black")
        n = str(t.get("n"))
        if c == "joker" or n == "j":
            c = "joker"
            n = "joker"
        return {"color": c, "number": n}

    # Initialize initial sets
    formatted_initial_sets = []
    for s_idx, s in enumerate(initial_sets):
        s_id = s.get("id") or str(uuid.uuid4())
        tiles = s.get("tiles", [])
        formatted_tiles = []
        for t in tiles:
            t_id = t.get("id") or str(uuid.uuid4())
            t_copy = dict(t)
            t_copy["id"] = t_id
            t_copy["number"] = str(t_copy.get("number", "0"))
            formatted_tiles.append(t_copy)
        formatted_initial_sets.append({"id": s_id, "tiles": formatted_tiles})
        
    # Initialize initial hand
    formatted_hand = []
    for t in initial_hand:
        t_id = t.get("id") or str(uuid.uuid4())
        t_copy = dict(t)
        t_copy["id"] = t_id
        t_copy["number"] = str(t_copy.get("number", "0"))
        formatted_hand.append(t_copy)
        
    # 2. Find exact matching sets to keep them unchanged
    new_board_raw = solution_dict.get("new_board", [])
    
    new_board_std = []
    for b in new_board_raw:
        new_board_std.append([map_solver_to_std(t) for t in b])
        
    matched_initial_set_ids = set()
    final_sets = []
    
    unmatched_new_sets = []
    
    for std_set in new_board_std:
        sig = _get_set_signature(std_set)
        match_found = False
        for initial_set in formatted_initial_sets:
            init_s_id = initial_set["id"]
            if init_s_id in matched_initial_set_ids:
                continue
            if _get_set_signature(initial_set["tiles"]) == sig:
                # Perfect match!
                matched_initial_set_ids.add(init_s_id)
                final_sets.append({
                    "id": init_s_id,
                    "tiles": initial_set["tiles"]
                })
                match_found = True
                break
        
        if not match_found:
            unmatched_new_sets.append(std_set)
            
    # 3. Populate pools from dismantled sets and hand
    for initial_set in formatted_initial_sets:
        if initial_set["id"] not in matched_initial_set_ids:
            for t in initial_set["tiles"]:
                key = _get_tile_key(t)
                board_tiles_pool.setdefault(key, []).append((t, initial_set["id"]))
                
    for t in formatted_hand:
        key = _get_tile_key(t)
        hand_tiles_pool.setdefault(key, []).append(t)
        
    # We only use hand tiles that were actually placed
    placed_raw = solution_dict.get("placed", [])
    placed_std = [map_solver_to_std(t) for t in placed_raw]
    
    available_hand = {}
    for t in placed_std:
        key = _get_tile_key(t)
        if key in hand_tiles_pool and len(hand_tiles_pool[key]) > 0:
            tile_obj = hand_tiles_pool[key].pop(0)
            available_hand.setdefault(key, []).append(tile_obj)
            
    # Remaining tiles in hand_tiles_pool stay in hand
    remaining_hand = []
    for tiles_list in hand_tiles_pool.values():
        remaining_hand.extend(tiles_list)
        
    # 4. Construct new sets and generate moves
    moves = []
    step_idx = 0
    
    for std_set in unmatched_new_sets:
        new_s_id = str(uuid.uuid4())
        new_set_tiles = []
        for t in std_set:
            key = _get_tile_key(t)
            # Try to grab from board first
            if key in board_tiles_pool and len(board_tiles_pool[key]) > 0:
                t_obj, origin_s_id = board_tiles_pool[key].pop(0)
                new_set_tiles.append(t_obj)
                moves.append(TileMove(
                    tile_id=t_obj["id"],
                    tile=Tile(**t_obj),
                    source_type="board_set",
                    source_id=origin_s_id,
                    destination_id=new_s_id,
                    step_index=step_idx
                ))
                step_idx += 1
            # Otherwise grab from hand
            elif key in available_hand and len(available_hand[key]) > 0:
                t_obj = available_hand[key].pop(0)
                new_set_tiles.append(t_obj)
                moves.append(TileMove(
                    tile_id=t_obj["id"],
                    tile=Tile(**t_obj),
                    source_type="hand",
                    source_id=None,
                    destination_id=new_s_id,
                    step_index=step_idx
                ))
                step_idx += 1
            else:
                # Should theoretically never happen if solver is correct
                pass 
                
        final_sets.append({
            "id": new_s_id,
            "tiles": new_set_tiles
        })
        
    return SolveResult(
        status="solved" if len(moves) > 0 else "no_moves",
        final_board=[BoardSet(**s) for s in final_sets],
        remaining_hand=[Tile(**t) for t in remaining_hand],
        moves=moves
    )
