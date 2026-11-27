"""tkinter window: human vs AI, AI vs AI, human vs human. Owner: Abdelrahman."""
import queue
import random
import threading
import tkinter as tk
from tkinter import ttk

from game_state import GameState, WHITE, BLACK, ARROW, SIZE, move_name
from search import best_move

SQ = 56                      # square size in pixels
MARGIN = 24                  # room for the coordinates
LIGHT, DARK = "#e8dcc4", "#b8a07e"
DEST, SHOT, LAST = "#2e7d32", "#e07b00", "#c62828"
PLAYERS = ("Human", "AI", "Random")


def copy_state(state):
    """The AI searches a copy, so the board on screen never changes during a search."""
    s = GameState()
    s.cells = state.cells[:]
    s.turn = state.turn
    return s


class AmazonsApp:
    def __init__(self, root):
        self.root = root
        root.title("Game of the Amazons")
        self.results = queue.Queue()   # finished AI moves from the worker thread
        self.game_id = 0               # lets results from an abandoned game be ignored
        self._build_widgets()
        self.new_game()
        self._poll()

    # ------------------------------------------------------------ layout
    def _build_widgets(self):
        size = SIZE * SQ + 2 * MARGIN
        self.canvas = tk.Canvas(self.root, width=size, height=size, highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=8, pady=8)
        self.canvas.bind("<Button-1>", self.on_click)

        side = ttk.Frame(self.root)
        side.grid(row=0, column=1, sticky="n", padx=8, pady=8)
        self.player = {}
        for row, (colour, label) in enumerate(((WHITE, "White"), (BLACK, "Black"))):
            ttk.Label(side, text=label).grid(row=row, column=0, sticky="w")
            var = tk.StringVar(value="Human" if colour == WHITE else "AI")
            ttk.Combobox(side, textvariable=var, values=PLAYERS, state="readonly",
                         width=8).grid(row=row, column=1, pady=2)
            self.player[colour] = var

        ttk.Label(side, text="AI time (s)").grid(row=2, column=0, sticky="w")
        self.time_limit = tk.DoubleVar(value=2.0)
        ttk.Spinbox(side, from_=0.1, to=30, increment=0.5, textvariable=self.time_limit,
                    width=7).grid(row=2, column=1, pady=2)
        ttk.Label(side, text="Max depth (0 = none)").grid(row=3, column=0, sticky="w")
        self.max_depth = tk.IntVar(value=0)
        ttk.Spinbox(side, from_=0, to=10, textvariable=self.max_depth,
                    width=7).grid(row=3, column=1, pady=2)

        ttk.Button(side, text="New game", command=self.new_game).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(8, 2))
        self.status = ttk.Label(side, text="", wraplength=220)
        self.status.grid(row=5, column=0, columnspan=2, sticky="w", pady=8)

        ttk.Label(side, text="Moves").grid(row=6, column=0, sticky="w")
        self.log = tk.Listbox(side, height=18, width=34)
        self.log.grid(row=7, column=0, columnspan=2)

    # ------------------------------------------------------------ game flow
    def new_game(self):
        self.game_id += 1
        self.state = GameState()
        self.moves = []              # legal moves of the player to move
        self.sel_from = self.sel_to = None
        self.last = None
        self.thinking = False
        self.log.delete(0, tk.END)
        self.next_turn()

    def next_turn(self):
        self.sel_from = self.sel_to = None
        self.draw()
        side = "White" if self.state.turn == WHITE else "Black"
        if self.state.is_over():
            winner = "Black" if self.state.turn == WHITE else "White"
            self.status.config(text=f"Game over: {side} has no legal move. {winner} wins.")
            self.draw_result(side, winner)
            return
        self.moves = self.state.legal_moves()
        kind = self.player[self.state.turn].get()
        if kind == "Human":
            self.status.config(text=f"{side} to move: click an amazon.")
        elif kind == "Random":
            self.status.config(text=f"{side} (random) to move.")
            game_id = self.game_id
            self.root.after(300, lambda: game_id == self.game_id and
                            self.play(random.choice(self.moves)))
        else:
            self.status.config(text=f"{side} (AI) is thinking...")
            self.thinking = True
            args = (copy_state(self.state), self.time_limit.get(),
                    self.max_depth.get() or None, self.game_id)
            threading.Thread(target=self._think, args=args, daemon=True).start()

    def _think(self, state, time_limit, max_depth, game_id):
        stats = {}
        move = best_move(state, time_limit, max_depth=max_depth, stats=stats)
        self.results.put((game_id, move, stats))

    def _poll(self):
        """tkinter is not thread-safe: the worker only queues its result, the main loop applies it."""
        try:
            while True:
                game_id, move, stats = self.results.get_nowait()
                if game_id == self.game_id and move is not None:
                    self.thinking = False
                    self.play(move, f"depth {stats['depth']}, {stats['nodes']} nodes")
        except queue.Empty:
            pass
        self.root.after(50, self._poll)

    def play(self, move, note=""):
        side = "W" if self.state.turn == WHITE else "B"
        text = f"{self.log.size() + 1}. {side} {move_name(move)}"
        self.log.insert(tk.END, text + (f"  ({note})" if note else ""))
        self.log.see(tk.END)
        self.state.make(move)
        self.last = move
        self.next_turn()

    # ------------------------------------------------------------ input
    def on_click(self, event):
        if self.thinking or self.state.is_over() or self.player[self.state.turn].get() != "Human":
            return
        col, row = (event.x - MARGIN) // SQ, (event.y - MARGIN) // SQ
        if not (0 <= col < SIZE and 0 <= row < SIZE):
            return
        cell = row * SIZE + col
        if self.sel_to is not None and cell in self.targets():
            self.play((self.sel_from, self.sel_to, cell))
            return
        if self.sel_from is not None and cell in self.targets(self.sel_from):
            self.sel_to = cell                  # amazon placed, now choose the arrow
        elif self.state.cells[cell] == self.state.turn:
            self.sel_from, self.sel_to = cell, None
        else:
            self.sel_from = self.sel_to = None
        self.draw()

    def targets(self, frm=None):
        """Squares to highlight, read from the legal move list, so the GUI never repeats the rules."""
        if frm is not None:
            return {t for f, t, _ in self.moves if f == frm}
        return {a for f, t, a in self.moves if f == self.sel_from and t == self.sel_to}

    # ------------------------------------------------------------ drawing
    def draw(self):
        c = self.canvas
        c.delete("all")
        if self.sel_to is not None:
            marks, colour = self.targets(), SHOT
        elif self.sel_from is not None:
            marks, colour = self.targets(self.sel_from), DEST
        else:
            marks, colour = set(), None
        for cell in range(SIZE * SIZE):
            r, k = divmod(cell, SIZE)
            x, y = MARGIN + k * SQ, MARGIN + r * SQ
            c.create_rectangle(x, y, x + SQ, y + SQ, outline="",
                               fill=LIGHT if (r + k) % 2 == 0 else DARK)
            if self.last and cell in self.last:
                c.create_rectangle(x + 1, y + 1, x + SQ - 1, y + SQ - 1, outline=LAST, width=2)
            if cell in marks:
                c.create_rectangle(x + 4, y + 4, x + SQ - 4, y + SQ - 4, outline=colour, width=3)
            piece = self.state.cells[cell]
            if cell == self.sel_to:
                piece = self.state.turn          # preview: the amazon on its new square
            elif cell == self.sel_from and self.sel_to is not None:
                piece = None                     # ... and gone from the old one
            if piece in (WHITE, BLACK):
                p = 9
                c.create_oval(x + p, y + p, x + SQ - p, y + SQ - p, width=2,
                              fill="white" if piece == WHITE else "black",
                              outline="#1e88e5" if cell in (self.sel_from, self.sel_to) else "#333")
            elif piece == ARROW:
                self.draw_sword(x, y)
        for i in range(SIZE):
            c.create_text(MARGIN + i * SQ + SQ // 2, MARGIN // 2, text="abcdefghij"[i])
            c.create_text(MARGIN // 2, MARGIN + i * SQ + SQ // 2, text=str(SIZE - i))

    def draw_result(self, loser, winner):
        """Banner across the board. A single human player is told directly that they won or lost."""
        humans = [c for c in (WHITE, BLACK) if self.player[c].get() == "Human"]
        title = f"{winner} wins"
        if len(humans) == 1:
            title = "You lose" if self.state.turn == humans[0] else "You win"
        mid, w = MARGIN + SIZE * SQ // 2, SIZE * SQ
        self.canvas.create_rectangle(MARGIN, mid - 55, MARGIN + w, mid + 55,
                                     fill="#263238", outline="")
        self.canvas.create_text(mid, mid - 15, text=title, fill="white", font=("Helvetica", 28, "bold"))
        self.canvas.create_text(mid, mid + 25, fill="white", font=("Helvetica", 13),
                                text=f"{loser} has no legal move.  Press New game to play again.")

    def draw_sword(self, x, y):
        """A blocked square: a sword lying diagonally, tip at the top right."""
        c = self.canvas
        tip = (x + SQ - 9, y + 9)
        guard = (x + 21, y + SQ - 21)
        pommel = (x + 11, y + SQ - 11)
        c.create_line(*tip, *guard, width=8, fill="#37474f", capstyle="round")    # blade edge
        c.create_line(*tip, *guard, width=5, fill="#cfd8dc", capstyle="round")    # blade
        c.create_line(guard[0] - 8, guard[1] - 8, guard[0] + 8, guard[1] + 8,
                      width=4, fill="#b8860b", capstyle="round")                  # cross-guard
        c.create_line(*guard, *pommel, width=4, fill="#5d4037")                   # grip
        c.create_oval(pommel[0] - 3, pommel[1] - 3, pommel[0] + 3, pommel[1] + 3,
                      fill="#b8860b", outline="")                                 # pommel


def main():
    """Open the game window."""
    root = tk.Tk()
    AmazonsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
