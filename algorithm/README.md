# Rummikub Solver Algorithm

Solver for the single-move problem: given the board and a hand, find the move that places the most tiles.

```bash
pip install -r requirements.txt
python -m pytest tests/
```

- `tiles.py` - tile tuples and string parsing
- `solver.py` - dynamic-programming solver
- `validator.py` - meld checks used in tests
