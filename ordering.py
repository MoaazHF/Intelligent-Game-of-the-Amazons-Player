"""Move ordering for Alpha-Beta. Owner: Mohammed."""






from game_state import EMPTY, WHITE, BLACK, ARROW

DIRECTIONS=[(-1,-1),(-1,0),(-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
NEIGHBOURS=[]
for _cell in range(100):
    _r, _c = divmod(_cell,10)
    _nb=[]
    for _dr, _dc in DIRECTIONS:
        _nr, _nc = _r + _dr, _c + _dc
        if 0 <= _nr < 10 and 0 <= _nc < 10:
            _nb.append(_nr * 10 + _nc)
    NEIGHBOURS.append(_nb)

# Centre squares are worth more than edge squares (0 at the edge, up to ~8).
CENTRALITY = []
for _cell in range(100):
    _r, _c = divmod(_cell, 10)
    CENTRALITY.append(min(_r, 9 - _r) + min(_c, 9 - _c))

# Weights (tune these in your experiments).
W_CENTRE = 1.0     # prefer moving toward the centre
W_FREEDOM = 1.0    # prefer landing where the amazon has free neighbours
W_BLOCK = 3.0      # prefer arrows that touch enemy amazons
W_SELF_BLOCK = 3.0 # avoid arrows that touch our own amazons


def move_score(state, move):
    """Cheap guess of how good a move is. Higher = search it earlier."""
    cells = state.cells
    me = state.turn
    enemy = BLACK if me == WHITE else WHITE
    src, dst, arrow = move

    score = W_CENTRE * CENTRALITY[dst]

    # Free neighbours around the landing square (the source square is empty
    # after the move, so count it as free too).
    free = 0
    for n in NEIGHBOURS[dst]:
        if cells[n] == EMPTY or n == src:
            free += 1
    score += W_FREEDOM * free

    # Arrow: good if it boxes in an enemy amazon, bad if it boxes in ours.
    for n in NEIGHBOURS[arrow]:
        if n == dst:
            score -= W_SELF_BLOCK
        elif n == src:
            continue
        elif cells[n] == enemy:
            score += W_BLOCK
        elif cells[n] == me:
            score -= W_SELF_BLOCK

    return score


def order_moves(state, moves):
    """Return the moves sorted with the most promising first."""
    return sorted(moves, key=lambda m: move_score(state, m), reverse=True)



