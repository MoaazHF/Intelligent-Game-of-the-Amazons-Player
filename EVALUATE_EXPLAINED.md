# `evaluate.py` — Complete Visual & Algorithmic Guide

**Owner:** Marwan  
**Module Purpose:** Heuristic Evaluation Function (Multi-Source BFS Territory + Mobility)  
**Interface Function Called by Search (`search.py`):** `evaluate(state, color)`

---

## 1. The Big Picture: Why `evaluate.py` Exists

In the **Game of the Amazons**, the 10x10 board has **2,176 legal moves on the very first turn**. Because the game tree is far too massive for Hazem's Minimax/Alpha-Beta search (`search.py`) to search all the way to the end of the game, the search must stop after looking `d` turns into the future (for example, depth 2 or 3).

When the search stops at depth `d`, the game is still going on. The AI needs a way to look at that imagined mid-game board and ask: **"Am I winning or losing on this board, and by how much?"**

That is the job of `evaluate(state, color)`:
* **Input:** A board snapshot (`state`) and the AI's piece color (`color`, either `WHITE` or `BLACK`).
* **Output:** A single floating-point number (score).
  * **Positive score (e.g., `+14.6`):** Good for `color` (the AI controls more board space and has more freedom to move).
  * **Zero (`0.0`):** Completely even game (such as the symmetric starting board).
  * **Negative score (e.g., `-9.4`):** Bad for `color` (the opponent is trapping the AI).

---

## 2. High-Level Execution Flow

Whenever `evaluate(state, color)` is called, the data flows through our 4 functions in this exact sequence:

```text
                  evaluate(state, color, w1=1.0, w2=0.2)
                                    |
        +---------------------------+---------------------------+
        |                                                       |
        v                                                       v
1. _find_amazons(cells, color)                   1. _find_amazons(cells, opponent)
   Finds [(r,c), ...] for our 4 Queens              Finds [(r,c), ...] for enemy's 4 Queens
        |                                                       |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           |                           v
2. _mobility_for_color(...)         |            3. _queen_bfs_distances(...)
   Counts 1-move Queen slides       |               Builds 10x10 grid of minimum moves
   for my_amazons & opp_amazons     |               needed to reach every empty square
        |                           |                           |
        v                           |                           v
   TOTAL_mobility =                 |               territory = (Squares I reach faster)
   my_mobility - opp_mobility       |                         - (Squares enemy reaches faster)
        |                           |                           |
        +---------------------------+---------------------------+
                                    |
                                    v
              Final Score = (w1 * territory) + (w2 * TOTAL_mobility)
```

---

## 3. Global Constants & Imports

```python
from collections import deque
from game_state import EMPTY, WHITE, BLACK, ARROW

Directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
INF = 999999
```

### What Each Term Means:
* **`deque` (Double-Ended Queue):** Imported from Python's `collections` library. Unlike a normal Python list where removing the first item (`pop(0)`) is slow (`O(N)`) because every other item has to shift left, `deque.popleft()` is instant (`O(1)`). We use it as our First-In, First-Out (FIFO) queue for Breadth-First Search (BFS).
* **`EMPTY (0)`, `WHITE (1)`, `BLACK (2)`, `ARROW (3)`:** The agreed team constants from `game_state.py` that represent what is inside each cell of `state.cells[r][c]`.
* **`Directions`:** The 8 compass directions a Queen (Amazon) can slide along on a 2D grid. Each tuple is `(direction_r, direction_c)`:

```text
          (-1, -1)   (-1, 0)   (-1, +1)
              \         |         /
               \        |        /
     (0, -1) <--  [ QUEEN (r,c) ]  --> (0, +1)
               /        |        \
              /         |         \
          (+1, -1)   (+1, 0)   (+1, +1)
```

* **`INF = 999999`:** Stands for **Infinity**. When we build our distance map in BFS, every square starts at `999999` to mean *"Unvisited / Unreachable"*. If a square is completely walled off by arrows so no Queen can ever enter it, its distance stays `999999`.

---

## 4. Sub-Function 1: `_find_amazons(cells, color)`

```python
def _find_amazons(cells, color):
    Positions = []
    size = len(cells)
    for r in range(size):
        for c in range(size):
            if cells[r][c] == color:
                Positions.append((r, c))
    return Positions
```

### Visualization & Purpose
Think of this function as a **radar scan** across the entire 10x10 board. Before we can measure how many moves a player has or run BFS from their pieces, we need to know the exact `(row, column)` coordinates where their 4 Amazons are currently standing.

### Variable Breakdown
* **`cells`**: The 2D list (`10x10`) representing the board.
* **`color`**: The player we are scanning for (`WHITE` or `BLACK`).
* **`Positions`**: An empty list `[]` that collects the `(r, c)` coordinates of every Amazon matching `color`.
* **`size`**: `len(cells)`, which is `10` on a standard board (or `4` on a 4x4 test board). Using `len(cells)` instead of hardcoding `10` allows our code to work on any test board size.
* **`r` and `c`**: Loop variables scanning every row (`0` to `size - 1`) and every column (`0` to `size - 1`).

---

## 5. Sub-Function 2: `_mobility_for_color(cells, amazon_positions)`

```python
def _mobility_for_color(cells, amazon_positions):
    size = len(cells)
    moves_count = 0
    for start_r, start_c in amazon_positions:
        for direction_r, direction_c in Directions:
            row = start_r + direction_r
            column = start_c + direction_c

            while 0 <= row < size and 0 <= column < size and cells[row][column] == EMPTY:
                moves_count = moves_count + 1
                row += direction_r
                column += direction_c
    return moves_count
```

### Visualization (The "Laser Pointer" Analogy)
**Important Concept:** This function **never moves the Amazon on the board** (it never changes `cells`).
Instead, imagine standing on each Amazon's square `(start_r, start_c)` and shining a **laser pointer** down each of the 8 Queen directions one by one:
* Every `EMPTY` square the laser beam passes through is **1 legal destination** that Queen could slide to right now (`moves_count += 1`).
* As soon as the laser beam hits the board edge, another Queen, or a flaming `ARROW`, the beam stops (`while` loop ends), and we aim the laser in the next direction.

```text
Example of scanning Right (0, +1) from a White Queen (W):
[ W ] --> [ . ] --> [ . ] --> [ . ] --> [ X (Arrow) ]
          +1        +2        +3        STOP! (Blocked by Arrow)
```

### Variable Breakdown
* **`amazon_positions`**: The list of 4 `(start_r, start_c)` tuples returned by `_find_amazons`.
* **`moves_count`**: Integer counter tracking the total number of squares all 4 Queens of this color can immediately reach in 1 slide.
* **`start_r, start_c`**: The starting square of the current Queen being inspected.
* **`direction_r, direction_c`**: The step offset for the current ray (e.g., `(-1, 0)` to scan straight up).
* **`row, column`**: The moving "scanner cursor" that starts 1 step away from the Queen (`start_r + direction_r`) and steps forward (`row += direction_r`) inside the `while` loop.
* **`0 <= row < size and 0 <= column < size`**: Keeps the scanner inside the board boundaries so Python never crashes with an `IndexError`.
* **`cells[row][column] == EMPTY`**: Ensures the square is free. In Amazons, Queens cannot jump over pieces or arrows.

---

## 6. Sub-Function 3: `_queen_bfs_distances(cells, amazon_positions)`

```python
def _queen_bfs_distances(cells, amazon_positions):
    size = len(cells)
    dist = [[INF for _ in range(size)] for _ in range(size)]

    queue = deque()

    for row, column in amazon_positions:
        dist[row][column] = 0
        queue.append((row, column))

    while queue:
        current_r, current_c = queue.popleft()
        next_distance = dist[current_r][current_c] + 1
        
        for direction_r, direction_c in Directions:
            row = current_r + direction_r
            column = current_c + direction_c

            while 0 <= row < size and 0 <= column < size and cells[row][column] == EMPTY:
                if dist[row][column] == INF:
                    dist[row][column] = next_distance
                    queue.append((row, column))
                row += direction_r 
                column += direction_c

    return dist
```

### Visualization (Ripples in a Pond — Multi-Source Queen BFS)
This function builds a **distance map (`dist`) for ONE side at a time**. It answers the question: *"For every square on the board, what is the minimum number of Queen moves needed for ANY of my 4 Amazons to reach it?"*

Why is it called **Multi-Source BFS**?
* In normal BFS, you start from 1 starting node. Here, a player has **4 Amazons**, and any of them can move to claim territory. So we put **all 4 Amazons into the `queue` at the very beginning with distance `0`**.
* **Wave 1 (`next_distance = 1`):** We pop each of the 4 starting Amazon positions (`dist = 0`) and slide along all 8 directions. Every empty square reachable in **1 straight Queen slide** (whether 1 square away or 9 squares away!) gets `dist = 1` and is added to the back of the `queue`.
* **Wave 2 (`next_distance = 2`):** Once all distance-`0` squares are processed, the `queue` naturally pops the distance-`1` squares. From each distance-`1` square, we slide along all 8 directions again. Any **unvisited** (`dist == INF`) empty square we reach gets `dist = 2` and joins the queue.
* This continues until every reachable empty square on the board is stamped with its minimum Queen-move distance (`1`, `2`, `3`, etc.). Any square trapped behind a wall of arrows is never reached and stays `INF` (`999999`).

### Crucial Exam/TA Question: Why is `if dist[row][column] == INF:` inside the `while` loop instead of stopping the `while` loop?
Suppose Square A is already visited (`dist = 1`), and Square B right behind it is unvisited (`dist = INF`).
Because Square A is still an **`EMPTY` square on the board**, a Queen sliding along that line can **slide right through Square A** to land on Square B!
* If `dist[row][column]` is already `< INF`, we don't overwrite its distance and we don't re-add it to the queue, **but** we still execute `row += direction_r` and `column += direction_c` so the ray continues sliding past it until it hits a real obstacle (`WHITE`, `BLACK`, `ARROW`, or board edge).

---

## 7. Main Interface Function: `evaluate(state, color, w1=1.0, w2=0.2)`

```python
def evaluate(state, color, w1=1.0, w2=0.2):
    if color == WHITE:
        opponent = BLACK
    else:
        opponent = WHITE

    cells = state.cells
    size = len(cells)

    my_amazons = _find_amazons(cells, color)
    opp_amazons = _find_amazons(cells, opponent)
    my_mobility = _mobility_for_color(cells, my_amazons)
    opp_mobility = _mobility_for_color(cells, opp_amazons)
    TOTAL_mobility = my_mobility - opp_mobility

    my_dist = _queen_bfs_distances(cells, my_amazons)
    opp_dist = _queen_bfs_distances(cells, opp_amazons)
    territory = 0
    for row in range(size):
        for column in range(size):
            if cells[row][column] == EMPTY:
                if my_dist[row][column] < opp_dist[row][column]:
                    territory = territory + 1
                elif opp_dist[row][column] < my_dist[row][column]:
                    territory = territory - 1

    return w1 * territory + w2 * TOTAL_mobility
```

### Step-by-Step Visualization of `evaluate`:
1. **Identify Perspective (`color` vs `opponent`):** Hazem's `search.py` tells us which color the AI is playing (`color`). We set `opponent` to the other color so our final score is always positive when `color` is winning.
2. **Calculate Net Mobility (`TOTAL_mobility`):**
   `TOTAL_mobility = my_mobility - opp_mobility`
   If my 4 Queens have 35 immediate moves and the opponent's 4 Queens have 20 immediate moves, `TOTAL_mobility = +15`.
3. **Compare the Two BFS Maps to Count `territory`:**
   We call `_queen_bfs_distances` twice: once for `my_amazons` (creating the `my_dist` grid) and once for `opp_amazons` (creating the `opp_dist` grid). Then we compare them square-by-square across every `EMPTY` cell:
   * **`my_dist[row][column] < opp_dist[row][column]`:** My Queen can reach this empty square in fewer moves than the opponent (e.g., I reach it in `1` move, opponent needs `2` moves, or opponent is blocked at `INF`). I own this square -> `territory += 1`.
   * **`opp_dist[row][column] < my_dist[row][column]`:** The opponent reaches this empty square in fewer moves -> `territory -= 1`.
   * **Tie (`my_dist == opp_dist`):** Either both players reach it in the same number of moves (contested square) or neither player can reach it (`INF == INF`). Neither side gets points (`+0`).
4. **Combine with Weights (`w1` and `w2`):**
   `Score = (w1 * territory) + (w2 * TOTAL_mobility)`
   * **Why is `w1 = 1.0` larger than `w2 = 0.2`?** Because Territory is the primary winning condition in Amazons (controlling more squares guarantees you outlast the opponent in the endgame), while Mobility (`0.2`) acts as an early/mid-game helper that stops the AI from letting its Queens get boxed in before the board is partitioned.

---

## 8. Worked Hand-Made 4x4 Example (For Testing & Report Diagram)

Consider this 4x4 board where **Black (`B`) at `(0, 3)` is walled into the top-right corner** by 3 Arrows (`X`), and **White (`W`) is at `(2, 1)`**:

### 1. The Board (`state.cells`)

| Row / Col | Col 0 | Col 1 | Col 2 | Col 3 |
| :---: | :---: | :---: | :---: | :---: |
| **Row 0** | `.` | `.` | `X` | **`B`** |
| **Row 1** | `.` | `.` | `X` | `X` |
| **Row 2** | `.` | **`W`** | `.` | `.` |
| **Row 3** | `.` | `.` | `.` | `.` |

### 2. White's BFS Distance Grid (`my_dist`)
White (`W` at `2,1`) reaches 9 empty squares in `1` Queen move, and reaches the remaining 2 corners `(0,0)` and `(3,3)` in `2` Queen moves:

| `my_dist` (White) | Col 0 | Col 1 | Col 2 | Col 3 |
| :---: | :---: | :---: | :---: | :---: |
| **Row 0** | `2` | `1` | `INF` | `INF` |
| **Row 1** | `1` | `1` | `INF` | `INF` |
| **Row 2** | `1` | **`0`** | `1` | `1` |
| **Row 3** | `1` | `1` | `1` | `2` |

### 3. Black's BFS Distance Grid (`opp_dist`)
Black (`B` at `0,3`) is surrounded by Arrows at `(0,2)`, `(1,2)`, and `(1,3)`. It cannot move anywhere, so every empty square has distance `INF`:

| `opp_dist` (Black) | Col 0 | Col 1 | Col 2 | Col 3 |
| :---: | :---: | :---: | :---: | :---: |
| **Row 0** | `INF` | `INF` | `INF` | **`0`** |
| **Row 1** | `INF` | `INF` | `INF` | `INF` |
| **Row 2** | `INF` | `INF` | `INF` | `INF` |
| **Row 3** | `INF` | `INF` | `INF` | `INF` |

### 4. Final Calculation on This Board (`color = WHITE`)
* **`my_mobility`** = `9` squares (all the `1`s in `my_dist`), **`opp_mobility`** = `0` squares -> **`TOTAL_mobility` = `9`**.
* **`territory`** = White has `< INF` on all `11` empty squares -> **`territory` = `11`**.
* **`evaluate(state, WHITE)`** = `(1.0 * 11) + (0.2 * 9) = 11.0 + 1.8 = 12.8`.
