"""Tests for the game rules. Owner: Alaa."""
import random

from game_state import (GameState, EMPTY, WHITE, BLACK, ARROW, SIZE,
                        cell_name, parse_cell, move_name)
from play import random_move


def board(white=(), black=(), arrows=(), turn=WHITE):
    """A hand-made position on an otherwise empty board."""
    s = GameState()
    s.cells = [EMPTY] * (SIZE * SIZE)
    for c in white:
        s.cells[c] = WHITE
    for c in black:
        s.cells[c] = BLACK
    for c in arrows:
        s.cells[c] = ARROW
    s.turn = turn
    return s


def test_start_position_has_2176_legal_moves():
    assert len(GameState().legal_moves()) == 2176


def test_start_position_pieces():
    s = GameState()
    assert s.cells.count(WHITE) == 4 and s.cells.count(BLACK) == 4
    assert s.cells.count(ARROW) == 0 and s.turn == WHITE


def test_unmake_restores_every_start_move():
    s = GameState()
    before = (s.cells[:], s.turn)
    for move in s.legal_moves():
        s.make(move)
        s.unmake(move)
        assert (s.cells, s.turn) == before, move_name(move)


def test_make_moves_amazon_places_arrow_and_switches_turn():
    s = GameState()
    s.make((60, 50, 40))
    assert s.cells[60] == EMPTY and s.cells[50] == WHITE and s.cells[40] == ARROW
    assert s.turn == BLACK


def test_arrow_can_land_on_the_square_just_left():
    assert (60, 50, 60) in GameState().legal_moves()


def test_amazon_cannot_pass_through_a_piece():
    # White on 60 and Black on 30 share column a; 20 lies behind Black.
    assert not any(f == 60 and t == 20 for f, t, _ in GameState().legal_moves())


def test_arrow_cannot_pass_through_a_piece():
    s = board(white=[0], black=[2])
    assert not any(t == 1 and a == 3 for _, t, a in s.legal_moves())


def test_trapped_player_has_no_moves_and_game_is_over():
    s = board(white=[0], black=[99], arrows=[1, 10, 11])
    assert s.legal_moves() == [] and s.is_over()
    s.turn = BLACK
    assert s.legal_moves() and not s.is_over()


def test_amazon_with_one_free_neighbour_still_has_a_move():
    s = board(white=[0], black=[99], arrows=[1, 10])   # only 11 is free
    assert not s.is_over()
    assert (0, 11, 0) in s.legal_moves()


def test_50_random_games_play_only_legal_moves():
    rng = random.Random(2026)
    for _ in range(50):
        s = GameState()
        played = 0
        while True:
            legal = s.legal_moves()
            assert s.is_over() == (legal == [])
            if not legal:
                break
            move = random_move(s, rng)
            frm, to, arrow = move
            assert move in legal
            assert s.cells[frm] == s.turn and s.cells[to] == EMPTY
            assert s.cells[arrow] == EMPTY or arrow == frm
            mover = s.turn
            s.make(move)
            played += 1
            assert s.cells[to] == mover and s.cells[arrow] == ARROW
        assert played <= 92                       # 92 empty squares = at most 92 arrows
        assert s.cells.count(ARROW) == played
        assert s.cells.count(WHITE) == 4 and s.cells.count(BLACK) == 4


def test_cell_names():
    assert cell_name(0) == "a10" and cell_name(99) == "j1" and cell_name(63) == "d4"
    assert all(parse_cell(cell_name(c)) == c for c in range(SIZE * SIZE))
    assert move_name((93, 33, 36)) == "d1-d7/g7"
