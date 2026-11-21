import time


try:
    from evaluate import evaluate as _default_evaluate
except ImportError:
    def _default_evaluate(state, color):
        return 0

try:
    from ordering import order_moves as _default_order
except ImportError:
    def _default_order(state, moves):
        return moves

INF = float("inf")
WIN_SCORE = 1_000_000  


class _Timeout(Exception):
    """Raised inside the search when the time limit is reached."""


class _Searcher:
    def __init__(self, root_color, evaluate_fn, order_fn,
                 deadline=None, use_ordering=True):
        self.root = root_color
        self.evaluate = evaluate_fn
        self.order = order_fn
        self.deadline = deadline
        self.use_ordering = use_ordering
        self.nodes = 0
        self.partial_best = None

    
    def _tick(self):
        self.nodes += 1
        if self.deadline is not None and time.perf_counter() >= self.deadline:
            raise _Timeout

    def _terminal(self, state, depth):
        """The player to move has no legal move and loses.
        Adding `depth` (moves still unsearched) prefers faster wins and
        slower losses."""
        if state.turn == self.root:
            return -(WIN_SCORE + depth)
        return WIN_SCORE + depth

    def _leaf(self, state):
        return self.evaluate(state, self.root)

    
    def minimax(self, state, depth):
        self._tick()
        if depth == 0:
            if state.is_over():
                return self._terminal(state, depth)
            return self._leaf(state)

        moves = state.legal_moves()
        if not moves:
            return self._terminal(state, depth)

        if state.turn == self.root:
            best = -INF
            for m in moves:
                state.make(m)
                try:
                    v = self.minimax(state, depth - 1)
                finally:
                    state.unmake(m)
                if v > best:
                    best = v
            return best
        best = INF
        for m in moves:
            state.make(m)
            try:
                v = self.minimax(state, depth - 1)
            finally:
                state.unmake(m)
            if v < best:
                best = v
        return best

    # -- Alpha-Beta --
    def alphabeta(self, state, depth, alpha, beta):
        self._tick()
        if depth == 0:
            if state.is_over():
                return self._terminal(state, depth)
            return self._leaf(state)

        moves = state.legal_moves()
        if not moves:
            return self._terminal(state, depth)
        if self.use_ordering:
            moves = self.order(state, moves)

        if state.turn == self.root:
            best = -INF
            for m in moves:
                state.make(m)
                try:
                    v = self.alphabeta(state, depth - 1, alpha, beta)
                finally:
                    state.unmake(m)
                if v > best:
                    best = v
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        best = INF
        for m in moves:
            state.make(m)
            try:
                v = self.alphabeta(state, depth - 1, alpha, beta)
            finally:
                state.unmake(m)
            if v < best:
                best = v
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best

    # -- the root (MAX) level, shared by both algorithms --
    def search_root(self, state, moves, depth, prune):
        """Search `moves` (already ordered) to `depth`.
        Returns (best_move, best_value). On a tie the first move wins, so
        Minimax and Alpha-Beta choose the same move."""
        alpha, beta = -INF, INF
        best_move, best_val = None, -INF
        for m in moves:
            state.make(m)
            try:
                if prune:
                    v = self.alphabeta(state, depth - 1, alpha, beta)
                else:
                    v = self.minimax(state, depth - 1)
            finally:
                state.unmake(m)
            if v > best_val:
                best_val, best_move = v, m
                self.partial_best = m
            if prune and v > alpha:
                alpha = v
        return best_move, best_val


def _root_moves(state, order_fn, use_ordering):
    moves = list(state.legal_moves())
    if use_ordering and moves:
        moves = list(order_fn(state, moves))
    return moves


# Fixed-depth search (used by the experiments and the tests)

def search_fixed_depth(state, depth, algorithm="alphabeta", use_ordering=True,
                       evaluate_fn=None, order_fn=None):
    """Search to exactly `depth` plies (1 ply = one full turn: move + arrow).

    algorithm: "minimax" or "alphabeta".
    Returns (move, value, nodes_searched). Move is None if there are no moves.
    """
    evaluate_fn = evaluate_fn or _default_evaluate
    order_fn = order_fn or _default_order
    moves = _root_moves(state, order_fn, use_ordering)
    if not moves:
        return None, None, 0
    s = _Searcher(state.turn, evaluate_fn, order_fn, None, use_ordering)
    move, value = s.search_root(state, moves, depth, algorithm == "alphabeta")
    return move, value, s.nodes


# Main entry point: iterative deepening + Alpha-Beta under a time limit

def best_move(state, time_limit, max_depth=None, use_ordering=True,
              stats=None, evaluate_fn=None, order_fn=None):
    """Return the AI's move for state.turn within `time_limit` seconds.

    Searches depth 1, 2, 3, ... with Alpha-Beta. When time runs out, the
    unfinished depth is dropped and the best move of the last finished depth
    is played, so a move is always ready.

    Optional arguments (the team interface only needs state and time_limit):
      max_depth     stop after this depth even if time is left
      use_ordering  turn move ordering on/off (for the experiments)
      stats         a dict; filled with 'depth', 'nodes', 'value', 'time'
    """
    start = time.perf_counter()
    evaluate_fn = evaluate_fn or _default_evaluate
    order_fn = order_fn or _default_order

    moves = _root_moves(state, order_fn, use_ordering)
    if not moves:
        return None

    deadline = start + time_limit if time_limit is not None else None
    searcher = _Searcher(state.turn, evaluate_fn, order_fn, deadline,
                         use_ordering)

    best = moves[0]
    best_val = None
    depth_done = 0

    if len(moves) > 1:
        depth = 1
        while max_depth is None or depth <= max_depth:
            searcher.partial_best = None
            try:
                move, val = searcher.search_root(state, moves, depth, True)
            except _Timeout:
                if depth_done == 0 and searcher.partial_best is not None:
                    best = searcher.partial_best
                break
            best, best_val, depth_done = move, val, depth
            moves.remove(move)
            moves.insert(0, move)
            if abs(val) >= WIN_SCORE:
                break
            depth += 1

    if stats is not None:
        stats["depth"] = depth_done
        stats["nodes"] = searcher.nodes
        stats["value"] = best_val
        stats["time"] = time.perf_counter() - start
    return best
