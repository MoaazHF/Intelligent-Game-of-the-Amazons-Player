"""Terminal play and the random player. Owner: Alaa.

Usage:  python play.py [white] [black] [--time SECONDS]
        players: human, ai, random   (default: human ai)
A human move is typed as three cells: from to arrow, for example  d1 d7 g7
"""
import argparse
import random

from game_state import GameState, EMPTY, WHITE, BLACK, ARROW, SIZE, parse_cell, move_name
from search import best_move

SYMBOL = {EMPTY: ".", WHITE: "W", BLACK: "B", ARROW: "x"}


def random_move(state, rng=random):
    """Random player: any legal move, uniformly."""
    return rng.choice(state.legal_moves())


def board_text(state):
    rows = []
    for r in range(SIZE):
        line = " ".join(SYMBOL[state.cells[r * SIZE + c]] for c in range(SIZE))
        rows.append(f"{SIZE - r:>2} {line}")
    rows.append("   " + " ".join("abcdefghij"))
    return "\n".join(rows)


def human_move(state):
    legal = set(state.legal_moves())
    while True:
        text = input("Your move (from to arrow): ").split()
        try:
            move = tuple(parse_cell(t) for t in text)
        except (ValueError, IndexError):
            move = ()
        if len(move) == 3 and move in legal:
            return move
        print("Not a legal move. Example: d1 d7 g7")


def main():
    parser = argparse.ArgumentParser(description="Play the Game of the Amazons in the terminal.")
    parser.add_argument("white", nargs="?", default="human", choices=["human", "ai", "random"])
    parser.add_argument("black", nargs="?", default="ai", choices=["human", "ai", "random"])
    parser.add_argument("--time", type=float, default=2.0, help="AI seconds per move")
    args = parser.parse_args()

    choose = {
        "human": human_move,
        "random": random_move,
        "ai": lambda s: best_move(s, args.time),
    }
    players = {WHITE: choose[args.white], BLACK: choose[args.black]}
    state = GameState()
    number = 1
    while not state.is_over():
        print("\n" + board_text(state))
        side = "White" if state.turn == WHITE else "Black"
        move = players[state.turn](state)
        print(f"{number}. {side}: {move_name(move)}")
        state.make(move)
        number += 1
    print("\n" + board_text(state))
    loser = "White" if state.turn == WHITE else "Black"
    print(f"{loser} has no legal move and loses.")


if __name__ == "__main__":
    main()
