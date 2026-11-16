"""Game state and rules of the Game of the Amazons. Owner: Moaaz."""

EMPTY, WHITE, BLACK, ARROW = 0, 1, 2, 3
SIZE = 10

# A cell is one integer: cell = row * 10 + col, from 0 to 99.
# A move is a tuple of three cells: (from_cell, to_cell, arrow_cell).


class GameState:
    def __init__(self):
        self.cells = [EMPTY] * (SIZE * SIZE)  # what is on each of the 100 squares
        self.turn = WHITE                     # whose turn it is

    def legal_moves(self):
        """Return a list of every legal move for the player to move."""
        ...

    def make(self, move):
        """Apply move: the amazon slides, the arrow lands, the turn switches."""
        ...

    def unmake(self, move):
        """Undo move exactly, restoring the state before make(move)."""
        ...

    def is_over(self):
        """Return True when the player to move has no legal move (that player loses)."""
        ...
