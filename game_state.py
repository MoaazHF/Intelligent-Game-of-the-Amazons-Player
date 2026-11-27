"""Moaaz"""

EMPTY, WHITE, BLACK, ARROW = 0, 1, 2, 3
SIZE = 10

# A cell is one integer: cell = row * 10 + col, from 0 to 99.
# A move is a tuple of three cells: (from_cell, to_cell, arrow_cell).

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# RAYS[cell] = one list per direction: the cells met walking from `cell`
# to the board edge. Built once, so move generation never checks bounds.
RAYS = []
for _cell in range(SIZE * SIZE):
    _r, _c = divmod(_cell, SIZE)
    _rays = []
    for _dr, _dc in DIRECTIONS:
        _ray = []
        _rr, _cc = _r + _dr, _c + _dc
        while 0 <= _rr < SIZE and 0 <= _cc < SIZE:
            _ray.append(_rr * SIZE + _cc)
            _rr, _cc = _rr + _dr, _cc + _dc
        if _ray:
            _rays.append(_ray)
    RAYS.append(_rays)

# Standard start: row 0 is the top. Black on rows 0 and 3, White on rows 6 and 9.
WHITE_START = [60, 93, 96, 69]
BLACK_START = [30, 3, 6, 39]


def cell_name(cell):
    """Board name of a cell: columns a-j left to right, rows 10-1 top to bottom (cell 0 = a10)."""
    r, c = divmod(cell, SIZE)
    return "abcdefghij"[c] + str(SIZE - r)


def parse_cell(name):
    """Inverse of cell_name: 'a10' -> 0, 'j1' -> 99. Raises ValueError on bad input."""
    name = name.strip().lower()
    c = "abcdefghij".find(name[:1])
    r = SIZE - int(name[1:])
    if c < 0 or not 0 <= r < SIZE:
        raise ValueError(f"not a cell: {name!r}")
    return r * SIZE + c


def move_name(move):
    """Standard Amazons notation: 'd1-d7/g7' (from-to/arrow)."""
    frm, to, arrow = move
    return f"{cell_name(frm)}-{cell_name(to)}/{cell_name(arrow)}"


class GameState:
    def __init__(self):
        self.cells = [EMPTY] * (SIZE * SIZE)  # what is on each of the 100 squares
        self.turn = WHITE                     # whose turn it is
        for cell in WHITE_START:
            self.cells[cell] = WHITE
        for cell in BLACK_START:
            self.cells[cell] = BLACK

    def _reachable(self, start):
        """Every empty cell a queen move from `start` can reach."""
        cells = self.cells
        out = []
        for ray in RAYS[start]:
            for cell in ray:
                if cells[cell] != EMPTY:
                    break
                out.append(cell)
        return out

    def legal_moves(self):
        """Return a list of every legal move for the player to move."""
        cells = self.cells
        me = self.turn
        moves = []
        for frm in range(SIZE * SIZE):
            if cells[frm] != me:
                continue
            cells[frm] = EMPTY  # the amazon left: the arrow may fly through or land on its old square
            for to in self._reachable(frm):
                for arrow in self._reachable(to):
                    moves.append((frm, to, arrow))
            cells[frm] = me
        return moves

    def make(self, move):
        """Apply move: the amazon slides, the arrow lands, the turn switches."""
        frm, to, arrow = move
        self.cells[to] = self.cells[frm]
        self.cells[frm] = EMPTY
        self.cells[arrow] = ARROW
        self.turn = BLACK if self.turn == WHITE else WHITE

    def unmake(self, move):
        """Undo move exactly, restoring the state before make(move)."""
        frm, to, arrow = move
        self.cells[arrow] = EMPTY  # first: the arrow may sit on `frm`
        self.cells[frm] = self.cells[to]
        self.cells[to] = EMPTY
        self.turn = BLACK if self.turn == WHITE else WHITE

    def is_over(self):
        """Return True when the player to move has no legal move (that player loses)."""
        # An amazon with one empty neighbour can step there and shoot back to
        # where it stood, so the player has a move. No empty neighbour = stuck.
        cells = self.cells
        for frm in range(SIZE * SIZE):
            if cells[frm] == self.turn:
                for ray in RAYS[frm]:
                    if cells[ray[0]] == EMPTY:
                        return False
        return True


if __name__ == "__main__":
    s = GameState()
    before = (list(s.cells), s.turn)
    moves = s.legal_moves()
    assert len(moves) == 2176
    for m in moves:  # every move must undo perfectly, including arrow shot back to `frm`
        s.make(m)
        s.unmake(m)
        assert (s.cells, s.turn) == before, m
    assert not s.is_over()
    # Trap: one white amazon in the corner, walled in by arrows.
    s.cells = [EMPTY] * (SIZE * SIZE)
    s.cells[0] = WHITE
    s.cells[1] = s.cells[10] = s.cells[11] = ARROW
    assert s.is_over() and s.legal_moves() == []
    print("ok")
