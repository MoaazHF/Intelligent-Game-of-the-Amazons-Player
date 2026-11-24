

import argparse
import csv
import os
import random
import time

import matplotlib
matplotlib.use("Agg")  # save charts to files, no window needed
import matplotlib.pyplot as plt

import search
from game_state import GameState, WHITE, BLACK
from search import best_move, search_fixed_depth

RESULTS_DIR = "results"
SEED = 361

# Experiment settings (lower them if something runs too slowly).
BRANCH_RANGE = (15, 40)      # test positions have this many legal moves
EXP1_DEPTHS = (1, 2, 3)      # Minimax vs Alpha-Beta
EXP2_DEPTHS = (2, 3)         # ordering on / off
EXP3_TIME_LIMITS = (0.1, 0.25, 0.5, 1.0, 2.0)
AI_TIME_LIMIT = 0.3          # seconds per AI move in games (exp 4 and 5)

# Experiment 5: (name, territory weight, mobility weight).
# Change "both" to the real weights Marwan uses in evaluate.py.
WEIGHT_SETS = [("territory only", 1, 0), ("mobility only", 0, 1), ("both", 1, 1)]


# ----------------------------------------------------------------- helpers

def save_csv(name, header, rows):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, name)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("saved", path)


def save_chart(fig, name):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, name)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print("saved", path)


def avg(values):
    values = list(values)
    return sum(values) / len(values) if values else 0


def make_positions(n, seed=SEED):
    """Fixed set of test positions: random playouts from the start position,
    stopped when the number of legal moves falls inside BRANCH_RANGE.
    Same seed = same positions, so every experiment uses the same data."""
    lo, hi = BRANCH_RANGE
    rng = random.Random(seed)
    positions = []
    attempts = 0
    while len(positions) < n and attempts < n * 50:
        attempts += 1
        state = GameState()
        for _ in range(92):  # a game cannot last longer than 92 turns
            if state.is_over():
                break
            moves = state.legal_moves()
            if lo <= len(moves) <= hi:
                positions.append(state)
                break
            state.make(rng.choice(moves))
    if len(positions) < n:
        print("warning: only found", len(positions), "positions")
    return positions


def timed_fixed(state, depth, algorithm, use_ordering):
    t0 = time.perf_counter()
    move, value, nodes = search_fixed_depth(
        state, depth, algorithm=algorithm, use_ordering=use_ordering)
    return move, value, nodes, time.perf_counter() - t0


# ----------------------------------------------------------- players/games

def random_player(rng):
    return lambda state: rng.choice(state.legal_moves())


def greedy_player():
    """Depth-1 greedy: plays the move with the best evaluation right away."""
    return lambda state: search_fixed_depth(state, 1, use_ordering=False)[0]


def ai_player(evaluate_fn=None):
    return lambda state: best_move(state, AI_TIME_LIMIT, evaluate_fn=evaluate_fn)


def play_game(white_fn, black_fn, game_id, records):
    """Play one game. Returns the winning colour. Appends every move to
    records as (game_id, move_number, colour, from, to, arrow)."""
    state = GameState()
    players = {WHITE: white_fn, BLACK: black_fn}
    n = 0
    while not state.is_over():
        colour = state.turn
        move = players[colour](state)
        if move is None:
            break
        records.append((game_id, n, colour) + tuple(move))
        state.make(move)
        n += 1
    # the player to move has no legal move and loses
    return BLACK if state.turn == WHITE else WHITE


def win_rate(ai_fn, opponent_fn, games, label, records):
    """AI plays `games` games against the opponent, alternating colours."""
    wins = 0
    for g in range(games):
        ai_is_white = (g % 2 == 0)
        white, black = (ai_fn, opponent_fn) if ai_is_white else (opponent_fn, ai_fn)
        winner = play_game(white, black, f"{label}-{g}", records)
        if winner == (WHITE if ai_is_white else BLACK):
            wins += 1
        print(f"  {label}: game {g + 1}/{games}, AI wins so far {wins}")
    return wins / games


GAME_HEADER = ["game_id", "move_number", "colour", "from_cell", "to_cell", "arrow_cell"]


# --------------------------------------------------------------- experiments

def exp1_minimax_vs_alphabeta(positions):
    print("\nExperiment 1: Minimax vs Alpha-Beta")
    rows = []
    for pi, state in enumerate(positions):
        for d in EXP1_DEPTHS:
            mm = timed_fixed(state, d, "minimax", False)
            ab = timed_fixed(state, d, "alphabeta", False)
            rows.append([pi, d, mm[2], ab[2], round(mm[3], 4), round(ab[3], 4),
                         mm[0] == ab[0], mm[1] == ab[1]])
            print(f"  position {pi}, depth {d}: nodes {mm[2]} vs {ab[2]}, "
                  f"same move {mm[0] == ab[0]}")
    save_csv("exp1_minimax_vs_alphabeta.csv",
             ["position", "depth", "minimax_nodes", "alphabeta_nodes",
              "minimax_time_s", "alphabeta_time_s", "same_move", "same_value"], rows)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    xs = list(range(len(EXP1_DEPTHS)))
    for ax, i_mm, i_ab, title, ylabel in (
            (ax1, 2, 3, "Nodes searched", "nodes (log scale)"),
            (ax2, 4, 5, "Time", "seconds (log scale)")):
        mm = [avg(r[i_mm] for r in rows if r[1] == d) for d in EXP1_DEPTHS]
        ab = [avg(r[i_ab] for r in rows if r[1] == d) for d in EXP1_DEPTHS]
        ax.bar([x - 0.2 for x in xs], mm, 0.4, label="Minimax")
        ax.bar([x + 0.2 for x in xs], ab, 0.4, label="Alpha-Beta")
        ax.set_xticks(xs)
        ax.set_xticklabels(EXP1_DEPTHS)
        ax.set_xlabel("depth")
        ax.set_ylabel(ylabel)
        ax.set_yscale("log")
        ax.set_title(title)
        ax.legend()
    same = sum(1 for r in rows if r[6])
    fig.suptitle(f"Minimax vs Alpha-Beta (same move in {same}/{len(rows)} searches)")
    save_chart(fig, "exp1_minimax_vs_alphabeta.png")


def exp2_move_ordering(positions):
    print("\nExperiment 2: Alpha-Beta with and without move ordering")
    # Make sure search.py really uses ordering.py (it silently falls back
    # to "no ordering" if ordering.py cannot be imported).
    if getattr(search._default_order, "__module__", "") != "ordering":
        print("  ERROR: search.py is not using ordering.order_moves. "
              "Merge ordering.py first, otherwise this experiment is meaningless.")
        return
    rows = []
    for pi, state in enumerate(positions):
        for d in EXP2_DEPTHS:
            off = timed_fixed(state, d, "alphabeta", False)
            on = timed_fixed(state, d, "alphabeta", True)
            rows.append([pi, d, off[2], on[2], round(off[3], 4), round(on[3], 4),
                         off[1] == on[1]])
            print(f"  position {pi}, depth {d}: nodes {off[2]} -> {on[2]}")
    save_csv("exp2_move_ordering.csv",
             ["position", "depth", "nodes_no_ordering", "nodes_with_ordering",
              "time_no_ordering_s", "time_with_ordering_s", "same_value"], rows)

    fig, ax = plt.subplots(figsize=(6, 4))
    xs = list(range(len(EXP2_DEPTHS)))
    off = [avg(r[2] for r in rows if r[1] == d) for d in EXP2_DEPTHS]
    on = [avg(r[3] for r in rows if r[1] == d) for d in EXP2_DEPTHS]
    ax.bar([x - 0.2 for x in xs], off, 0.4, label="no ordering")
    ax.bar([x + 0.2 for x in xs], on, 0.4, label="with ordering")
    ax.set_xticks(xs)
    ax.set_xticklabels(EXP2_DEPTHS)
    ax.set_xlabel("depth")
    ax.set_ylabel("average nodes searched")
    ax.set_title("Alpha-Beta: effect of move ordering")
    ax.legend()
    save_chart(fig, "exp2_move_ordering.png")


def exp3_iterative_deepening(positions):
    print("\nExperiment 3: depth reached per time limit")
    sets = {"start position": [GameState()], "late-game positions": positions}
    rows = []
    for name, group in sets.items():
        for tl in EXP3_TIME_LIMITS:
            for pi, state in enumerate(group):
                stats = {}
                best_move(state, tl, stats=stats)
                rows.append([name, pi, tl, stats["depth"], stats["nodes"]])
                print(f"  {name} {pi}, {tl}s: depth {stats['depth']}")
    save_csv("exp3_iterative_deepening.csv",
             ["position_set", "position", "time_limit_s", "depth_reached", "nodes"], rows)

    fig, ax = plt.subplots(figsize=(6, 4))
    for name in sets:
        ys = [avg(r[3] for r in rows if r[0] == name and r[2] == tl)
              for tl in EXP3_TIME_LIMITS]
        ax.plot(EXP3_TIME_LIMITS, ys, marker="o", label=name)
    ax.set_xlabel("time limit per move (s)")
    ax.set_ylabel("average depth reached")
    ax.set_title("Iterative deepening")
    ax.legend()
    save_chart(fig, "exp3_iterative_deepening.png")


def exp4_win_rate(games):
    print("\nExperiment 4: win rate against random and greedy players")
    records = []
    rng = random.Random(SEED)
    results = {
        "vs random": win_rate(ai_player(), random_player(rng), games, "vs-random", records),
        "vs depth-1 greedy": win_rate(ai_player(), greedy_player(), games, "vs-greedy", records),
    }
    save_csv("exp4_win_rate.csv", ["opponent", "games", "ai_win_rate"],
             [[k, games, v] for k, v in results.items()])
    save_csv("games_exp4.csv", GAME_HEADER, records)

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(list(results), list(results.values()))
    ax.set_ylim(0, 1)
    ax.set_ylabel("AI win rate")
    ax.set_title(f"AI win rate over {games} games each")
    save_chart(fig, "exp4_win_rate.png")


def make_evaluate(w_territory, w_mobility):
    """Build an evaluation function with the given weights.
    Adapt this to how evaluate.py is written (ask Marwan)."""
    import evaluate as ev
    if hasattr(ev, "W1") and hasattr(ev, "W2"):
        def f(state, colour):
            old = (ev.W1, ev.W2)
            ev.W1, ev.W2 = w_territory, w_mobility
            try:
                return ev.evaluate(state, colour)
            finally:
                ev.W1, ev.W2 = old
        return f
    if hasattr(ev, "territory") and hasattr(ev, "mobility"):
        return lambda state, colour: (w_territory * ev.territory(state, colour)
                                      + w_mobility * ev.mobility(state, colour))
    raise RuntimeError("evaluate.py has no W1/W2 and no territory()/mobility(): "
                       "adapt make_evaluate() in experiments.py to it.")


def exp5_weights(games):
    print("\nExperiment 5: evaluation weights")
    records = []
    results = {}
    for name, wt, wm in WEIGHT_SETS:
        ai = ai_player(make_evaluate(wt, wm))
        results[name] = win_rate(ai, greedy_player(), games, name.replace(" ", "-"), records)
    save_csv("exp5_weights.csv", ["weights", "games", "win_rate_vs_greedy"],
             [[k, games, v] for k, v in results.items()])
    save_csv("games_exp5.csv", GAME_HEADER, records)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(list(results), list(results.values()))
    ax.set_ylim(0, 1)
    ax.set_ylabel("win rate vs depth-1 greedy")
    ax.set_title(f"Evaluation weights ({games} games each)")
    save_chart(fig, "exp5_weights.png")


# ---------------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("experiments", nargs="*", type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument("--games", type=int, default=10, help="games per matchup (exp 4, 5)")
    parser.add_argument("--positions", type=int, default=5, help="test positions (exp 1, 2, 3)")
    args = parser.parse_args()

    positions = []
    if set(args.experiments) & {1, 2, 3}:
        positions = make_positions(args.positions)
        print("test positions:", [len(p.legal_moves()) for p in positions], "legal moves each")

    if 1 in args.experiments:
        exp1_minimax_vs_alphabeta(positions)
    if 2 in args.experiments:
        exp2_move_ordering(positions)
    if 3 in args.experiments:
        exp3_iterative_deepening(positions)
    if 4 in args.experiments:
        exp4_win_rate(args.games)
    if 5 in args.experiments:
        exp5_weights(args.games)


if __name__ == "__main__":
    main()
