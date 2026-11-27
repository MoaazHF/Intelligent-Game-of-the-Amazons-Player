"""Evaluation checked on hand-made positions. Owner: Marwan."""
import random

import pytest

import evaluate as ev
from game_state import GameState, EMPTY, WHITE, BLACK, ARROW, SIZE


def board(white=(), black=(), arrows=()):
    s = GameState()
    s.cells = [EMPTY] * (SIZE * SIZE)
    for c in white:
        s.cells[c] = WHITE
    for c in black:
        s.cells[c] = BLACK
    for c in arrows:
        s.cells[c] = ARROW
    return s


def test_mobility_of_a_corner_amazon_on_an_empty_board():
    s = board(white=[0])
    assert ev._mobility_for_color(s.cells, [(0, 0)]) == 27   # 9 right + 9 down + 9 diagonal


def test_queen_distances_from_a_corner():
    s = board(white=[0])
    dist = ev._queen_bfs_distances(s.cells, [(0, 0)])
    assert dist[0][0] == 0
    assert dist[9][9] == 1          # one diagonal move
    assert dist[1][9] == 2          # not on a queen line from a10


def test_start_position_is_balanced():
    s = GameState()
    assert ev.evaluate(s, WHITE) == 0 and ev.evaluate(s, BLACK) == 0


def test_trapped_white_amazon():
    # White a10 walled in by arrows; Black j1 reaches all 95 empty squares.
    # Black mobility: 9 up + 9 left + 7 on the diagonal (stops before the arrow on 11).
    s = board(white=[0], black=[99], arrows=[1, 10, 11])
    assert ev._mobility_for_color(s.cells, [(9, 9)]) == 25
    expected = ev.W1 * -95 + ev.W2 * (0 - 25)
    assert ev.evaluate(s, WHITE) == pytest.approx(expected)
    assert ev.evaluate(s, BLACK) == pytest.approx(-expected)


def test_score_for_one_side_is_minus_the_score_for_the_other():
    rng = random.Random(7)
    s = GameState()
    for _ in range(20):
        s.make(rng.choice(s.legal_moves()))
        assert ev.evaluate(s, WHITE) == pytest.approx(-ev.evaluate(s, BLACK))
