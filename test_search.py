import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import search

BRANCH = 6
TREE_DEPTH = 8 


class FakeState:
    def __init__(self, seed=0):
        self.path = ()
        self.turn = "W"
        self.seed = seed

    def legal_moves(self):
        return list(range(BRANCH)) if len(self.path) < TREE_DEPTH else []

    def make(self, m):
        self.path += (m,)
        self.turn = "B" if self.turn == "W" else "W"

    def unmake(self, m):
        assert self.path and self.path[-1] == m
        self.path = self.path[:-1]
        self.turn = "B" if self.turn == "W" else "W"

    def is_over(self):
        return not self.legal_moves()


def fake_eval(state, color):
    v = random.Random(hash((state.seed, state.path)) & 0xFFFFFFFF).randint(-100, 100)
    return v if color == "W" else -v


def fake_order(state, moves):
    return sorted(moves, key=lambda m: -fake_eval(_after(state, m), state.turn))


def _after(state, m):
    state.make(m)
    try:
        c = FakeState(state.seed)
        c.path, c.turn = state.path, state.turn
        return c
    finally:
        state.unmake(m)


def test_alphabeta_same_value_and_move_as_minimax():
    for seed in range(10):
        for depth in (1, 2, 3):
            s = FakeState(seed)
            mm = search.search_fixed_depth(s, depth, "minimax", False, fake_eval)
            ab = search.search_fixed_depth(s, depth, "alphabeta", False, fake_eval)
            assert mm[0] == ab[0] and mm[1] == ab[1]


def test_alphabeta_with_ordering_same_value():
    for seed in range(10):
        s = FakeState(seed)
        mm = search.search_fixed_depth(s, 3, "minimax", False, fake_eval)
        ab = search.search_fixed_depth(s, 3, "alphabeta", True, fake_eval, fake_order)
        assert mm[1] == ab[1]


def test_alphabeta_searches_fewer_nodes():
    s = FakeState(1)
    mm = search.search_fixed_depth(s, 3, "minimax", False, fake_eval)
    ab = search.search_fixed_depth(s, 3, "alphabeta", False, fake_eval)
    assert ab[2] < mm[2]


def test_ordering_reduces_nodes():
    s = FakeState(2)
    plain = search.search_fixed_depth(s, 3, "alphabeta", False, fake_eval)
    ordered = search.search_fixed_depth(s, 3, "alphabeta", True, fake_eval, fake_order)
    assert ordered[2] < plain[2]


def test_state_restored_after_search():
    s = FakeState(3)
    search.best_move(s, 0.2, max_depth=3, evaluate_fn=fake_eval)
    assert s.path == () and s.turn == "W"


def test_time_limit_respected_and_state_restored():
    def slow_eval(state, color):
        time.sleep(0.0005)
        return fake_eval(state, color)

    s = FakeState(4)
    t0 = time.perf_counter()
    mv = search.best_move(s, 0.3, evaluate_fn=slow_eval)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.6
    assert mv in range(BRANCH)
    assert s.path == () and s.turn == "W"


def test_deeper_with_more_time():
    s = FakeState(5)
    a, b = {}, {}
    search.best_move(s, 0.05, evaluate_fn=fake_eval, stats=a)
    search.best_move(s, 0.5, evaluate_fn=fake_eval, stats=b)
    assert b["depth"] >= a["depth"] >= 1


def test_no_moves_returns_none():
    s = FakeState()
    s.path = (0,) * TREE_DEPTH
    assert search.best_move(s, 0.1, evaluate_fn=fake_eval) is None


def test_finds_forced_win():
    """Position where the opponent has no reply after move 3: must pick it."""

    class WinState(FakeState):
        def legal_moves(self):
            if self.path == (3,):
                return []
            return list(range(BRANCH)) if len(self.path) < 4 else []

    s = WinState()
    assert search.best_move(s, 1.0, evaluate_fn=lambda st, c: 0) == 3
