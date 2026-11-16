"""Tests for the game rules. Owner: Alaa."""
from game_state import GameState


def test_start_position_has_2176_legal_moves():
    assert len(GameState().legal_moves()) == 2176
