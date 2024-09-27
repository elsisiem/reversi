import unittest
from ai import init_zobrist, compute_hash, find_best_move_original
from game_logic import compute_hash  # Assuming compute_hash is in game_logic.py

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

if __name__ == '__main__':
    unittest.main()
