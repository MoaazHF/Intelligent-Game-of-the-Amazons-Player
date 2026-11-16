# Intelligent Game of the Amazons Player

AI310/CS361 course project: an AI that plays the Game of the Amazons using Minimax, Alpha-Beta pruning, iterative deepening and a BFS territory evaluation.

## Shared interface

These names are agreed by the whole team. Do not rename them or change their parameters without the agreement of all six members.

| File | Name | Owner |
|---|---|---|
| `game_state.py` | `GameState`: `legal_moves()`, `make(move)`, `unmake(move)`, `is_over()` | Moaaz |
| `search.py` | `best_move(state, time_limit)` | Hazem |
| `evaluate.py` | `evaluate(state, color)` | Marwan |
| `ordering.py` | `order_moves(state, moves)` | Mohammed |
| `gui.py` | `main()` | Abdelrahman |
| `tests/` | test files | Alaa |

A cell is `row * 10 + col` (0 to 99). A move is `(from_cell, to_cell, arrow_cell)`. Square values: `EMPTY, WHITE, BLACK, ARROW = 0, 1, 2, 3`.

## Workflow

1. Clone the repository and create your own branch, for example `hazem-search`.
2. Fill in only your own file. If a part you need is not ready, use a simple fake with the same name.
3. Open a pull request to `main`; another member reviews it before merging.

## Run

```
pip install -r requirements.txt
python gui.py
pytest
```
