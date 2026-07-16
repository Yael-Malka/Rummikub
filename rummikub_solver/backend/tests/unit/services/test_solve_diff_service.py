"""Solve diff unit tests."""

import pytest
from src.services.solve_diff_service import generate_moves

def test_generate_moves_unchanged_board():
    initial_sets = [
        {"id": "set1", "tiles": [{"id": "t1", "color": "red", "number": "1"}, {"id": "t2", "color": "red", "number": "2"}, {"id": "t3", "color": "red", "number": "3"}]}
    ]
    initial_hand = [{"id": "h1", "color": "blue", "number": "1"}]
    solution_dict = {
        "new_board": [[{"n": "1", "c": "r"}, {"n": "2", "c": "r"}, {"n": "3", "c": "r"}]],
        "placed": [],
        "count": 0,
        "is_draw": True
    }
    
    res = generate_moves(initial_sets, initial_hand, solution_dict)
    
    assert res.status == "no_moves"
    assert len(res.moves) == 0
    assert len(res.final_board) == 1
    assert res.final_board[0].id == "set1"
    assert len(res.remaining_hand) == 1
    assert res.remaining_hand[0].id == "h1"

def test_generate_moves_with_placement():
    initial_sets = [
        {"id": "set1", "tiles": [{"id": "t1", "color": "red", "number": "1"}, {"id": "t2", "color": "red", "number": "2"}, {"id": "t3", "color": "red", "number": "3"}]}
    ]
    initial_hand = [{"id": "h1", "color": "red", "number": "4"}, {"id": "h2", "color": "blue", "number": "1"}]
    
    solution_dict = {
        "new_board": [[{"n": "1", "c": "r"}, {"n": "2", "c": "r"}, {"n": "3", "c": "r"}, {"n": "4", "c": "r"}]],
        "placed": [{"n": "4", "c": "r"}],
        "count": 1,
        "is_draw": False
    }
    
    res = generate_moves(initial_sets, initial_hand, solution_dict)
    
    assert res.status == "solved"
    assert len(res.moves) == 4 # The original set was dismantled and rebuilt + 1 from hand
    assert len(res.final_board) == 1
    assert len(res.final_board[0].tiles) == 4
    
    # Verify the move destinations are the new set
    new_set_id = res.final_board[0].id
    assert new_set_id != "set1"  # Since it changed, it's a new set
    for m in res.moves:
        assert m.destination_id == new_set_id
        if m.tile.number == "4":
            assert m.source_type == "hand"
            assert m.source_id is None
        else:
            assert m.source_type == "board_set"
            assert m.source_id == "set1"
            
    assert len(res.remaining_hand) == 1
    assert res.remaining_hand[0].id == "h2"
