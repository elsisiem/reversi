import random
import unittest

import ai
from ai import init_zobrist, compute_hash, find_best_move_original, minimax, evaluate_board, convert_board
from game_logic import initialize_board, make_move, valid_moves


def plain_minimax(board, depth, maximizing_player, player):
    """Reference search with no pruning and no table, same leaf scoring as ai.minimax."""
    moves = valid_moves(board, player)
    if depth == 0 or not moves:
        return evaluate_board(convert_board(board), player if maximizing_player else 3 - player)
    values = []
    for row, col in moves:
        child, _ = make_move([r[:] for r in board], row, col, player)
        values.append(plain_minimax(child, depth - 1, not maximizing_player, 3 - player))
    return max(values) if maximizing_player else min(values)


def midgame_board(seed, plies):
    """Plays `plies` random legal moves from the start position. Returns (board, side to move)."""
    rng = random.Random(seed)
    board, player = initialize_board(), 1
    for _ in range(plies):
        moves = valid_moves(board, player)
        if not moves:
            player = 3 - player
            moves = valid_moves(board, player)
            if not moves:
                break
        row, col = rng.choice(moves)
        board, _ = make_move([r[:] for r in board], row, col, player)
        player = 3 - player
    return board, player


class TestMinimaxStateManagement(unittest.TestCase):
    def test_board_integrity_after_minimax(self):
        original_board = [[0] * 8 for _ in range(8)]  # An empty board
        original_board[3][3], original_board[3][4] = 1, 2  # Starting position
        original_board[4][3], original_board[4][4] = 2, 1
        board_copy = [row[:] for row in original_board]  # Make a deep copy of the original board

        zobrist_keys = init_zobrist()  # Initialize Zobrist keys
        current_hash = compute_hash(board_copy, zobrist_keys)  # Compute initial board hash

        find_best_move_original(board_copy, 1, 3, zobrist_keys, current_hash)  # Perform Minimax search
        self.assertEqual(original_board, board_copy, "Board was modified by Minimax")

    def test_minimax_does_not_modify_its_input(self):
        board, player = midgame_board(seed=3, plies=12)
        snapshot = [row[:] for row in board]
        ai.transposition_table.clear()
        minimax(board, 3, float('-inf'), float('inf'), True, player, ai.zobrist_keys, None)
        self.assertEqual(snapshot, board)


class TestSearchCorrectness(unittest.TestCase):
    def setUp(self):
        ai.transposition_table.clear()

    def test_alpha_beta_with_table_matches_plain_minimax(self):
        for seed, plies in [(1, 8), (2, 24)]:
            board, player = midgame_board(seed, plies)
            for depth in (1, 2, 3):  # the table stays warm across depths, as in iterative deepening
                for maximizing in (True, False):
                    expected = plain_minimax(board, depth, maximizing, player)
                    actual = minimax([r[:] for r in board], depth, float('-inf'), float('inf'),
                                     maximizing, player, ai.zobrist_keys, None)
                    self.assertAlmostEqual(expected, actual, msg=f"seed={seed} depth={depth} max={maximizing}")

    def test_shallow_table_entry_is_not_reused_for_deeper_search(self):
        board, player = midgame_board(seed=4, plies=10)
        key = (compute_hash(board, ai.zobrist_keys), player, True)
        bogus = 12345.0
        ai.transposition_table[key] = (0, bogus, ai.TT_EXACT)  # searched at depth 0 only
        value = minimax([r[:] for r in board], 3, float('-inf'), float('inf'), True, player, ai.zobrist_keys, None)
        self.assertNotEqual(bogus, value)
        stored_depth, stored_value, _ = ai.transposition_table[key]
        self.assertEqual(3, stored_depth)
        self.assertEqual(value, stored_value)


if __name__ == '__main__':
    unittest.main()
