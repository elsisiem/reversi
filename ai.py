import random
import numpy as np
from game_logic import valid_moves, make_move, can_flip
from time import time
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# Constants
BOARD_SIZE = 8
PLAYER1 = 1
PLAYER2 = 2
EMPTY = 0

# Initialize Zobrist table for hashing
def init_zobrist():
    zobrist_keys = {}
    pieces = [PLAYER1, PLAYER2]  # Define piece types
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            zobrist_keys[(row, col)] = {piece: random.getrandbits(64) for piece in pieces}
    return zobrist_keys

# Zobrist hashing for a board
def compute_hash(board, zobrist_keys):
    if not isinstance(board, list) or not all(isinstance(row, list) for row in board):
        raise ValueError(f"Invalid board structure: {board}")
    h = 0
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board[row][col]
            if piece != EMPTY:
                h ^= zobrist_keys[(row, col)][piece]
    return h

# Transposition table
transposition_table = {}


opening_book = {
    ((0, 0), (0, 7), (7, 0), (7, 7)): [(2, 4), (3, 5), (4, 2), (5, 3)],
}

def score_move_for_ordering(board, move, player, zobrist_keys, current_hash):
    temp_board = [row[:] for row in board]
    new_board, updated_hash = make_move(temp_board, move[0], move[1], player, zobrist_keys, current_hash)
    corner_positions = [(0, 0), (0, 7), (7, 0), (7, 7)]
    score = 0
    if move in corner_positions:
        score += 100
    if any(new_board[0][i] == player or new_board[7][i] == player for i in range(8)):
        score += 30
    opponent_mobility = len(valid_moves(new_board, 3 - player))
    score -= opponent_mobility
    return score


def convert_board(board):
    """ Helper function to convert a list board to a tuple board for caching purposes """
    return tuple(tuple(row) for row in board)

@lru_cache(maxsize=None)
def evaluate_board(board_tuple, player):
    board = [list(row) for row in board_tuple]
    game_phase = determine_game_phase(board)
    opponent = 3 - player
    mobility = len(valid_moves(board, player)) - len(valid_moves(board, opponent))
    edge_control = edge_stability(board, player) - edge_stability(board, opponent)
    stability = calculate_stability(board, player) - calculate_stability(board, opponent)
    corners_captured = count_corners(board, player) - count_corners(board, opponent)
    disc_difference = np.sum(np.array(board) == player) - np.sum(np.array(board) == opponent)
    weights = adjust_weights_based_on_board(game_phase)

    heuristic_value = (weights['mobility'] * mobility +
                       weights['potential_mobility'] * weights.get('potential_mobility', 0) +
                       weights['parity'] * calculate_parity(board) +
                       weights['stability'] * stability +
                       weights['corners'] * corners_captured +
                       weights['edges'] * edge_control +
                       weights['disc_difference'] * disc_difference)
    return heuristic_value

def adjust_weights_based_on_board(game_phase):
    if game_phase == 'early':
        return {'mobility': 0.5, 'potential_mobility': 0.2, 'parity': 0.1, 'stability': 0.1, 'corners': 3, 'edges': 2, 'disc_difference': 0.1}
    elif game_phase == 'mid':
        return {'mobility': 0.3, 'potential_mobility': 0.1, 'parity': 0.2, 'stability': 0.3, 'corners': 4, 'edges': 2, 'disc_difference': 0.5}
    else:
        return {'mobility': 0.1, 'potential_mobility': 0.1, 'parity': 0.5, 'stability': 0.5, 'corners': 5, 'edges': 3, 'disc_difference': 1}

def determine_game_phase(board):
    empty_count = np.sum(np.array(board) == 0)
    if empty_count > 40:
        return 'early'
    elif empty_count > 20:
        return 'mid'
    else:
        return 'end'

def edge_stability(board, player):
    stable_edges = 0
    edges = [0, 7]
    for i in edges:
        for j in range(8):
            if board[i][j] == player and not can_be_flipped(board, i, j, player):
                stable_edges += 1
            if board[j][i] == player and not can_be_flipped(board, j, i, player):
                stable_edges += 1
    return stable_edges

def calculate_potential_mobility(board, opponent):
    potential_moves = valid_moves(board, opponent)
    return len(potential_moves)

def calculate_parity(board):
    empty_count = sum(1 for row in board for cell in row if cell == 0)
    return 1 if empty_count % 2 == 0 else -1

def count_corners(board, player):
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    return sum(1 for r, c in corners if board[r][c] == player)

def calculate_stability(board, player):
    stable_discs = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not can_be_flipped(board, r, c, player):
                stable_discs += 1
    return stable_discs

def can_be_flipped(board, row, col, player):
    opponent = 2 if player == 1 else 1
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == opponent:
            r += dr
            c += dc
        if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == player:
            return True
    return False

def calculate_corner_adjacency(board, player):
    """
    Calculates a penalty for having discs adjacent to an open corner, which could allow the opponent to capture the corner.
    """
    opponent = 3 - player
    adjacency_penalty = 0
    corner_adjacencies = [(0, 1), (1, 0), (1, 1),
                          (0, 6), (1, 7), (1, 6),
                          (6, 0), (7, 1), (6, 1),
                          (7, 6), (6, 7), (6, 6)]
    for r, c in corner_adjacencies:
        if board[r][c] == player:
            if (r in [0, 7] and board[7-r][c] == 0) or (c in [0, 7] and board[r][7-c] == 0):
                adjacency_penalty -= 1
    return adjacency_penalty

def count_frontier_discs(board, player):
    """
    Counts the number of frontier discs, which are discs adjacent to at least one empty square.
    """
    frontier = 0
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                for dr, dc in directions:
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == 0:
                        frontier += 1
                        break
    return frontier


def minimax(board, depth, alpha, beta, maximizing_player, player, zobrist_keys, current_hash):
    if current_hash is None:
        current_hash = compute_hash(board, zobrist_keys)

    if current_hash in transposition_table:
        return transposition_table[current_hash]

    if depth == 0 or not valid_moves(board, player):
        board_tuple = convert_board(board)
        score = evaluate_board(board_tuple, player)
        transposition_table[current_hash] = score
        return score

    best_value = float('-inf') if maximizing_player else float('inf')
    for move in valid_moves(board, player):
        new_board, new_hash = make_move(board.copy(), move[0], move[1], player, zobrist_keys, current_hash)
        value = minimax(new_board, depth - 1, alpha, beta, not maximizing_player, 3 - player, zobrist_keys, new_hash)
        if maximizing_player:
            best_value = max(best_value, value)
            alpha = max(alpha, value)
        else:
            best_value = min(best_value, value)
            beta = min(beta, value)
        if beta <= alpha:
            break

    transposition_table[current_hash] = best_value
    return best_value

# Initialize Zobrist keys
zobrist_keys = init_zobrist()

def find_best_move_original(board, player, depth, zobrist_keys, current_hash):
    best_moves = []
    best_score = float('-inf')
    alpha, beta = float('-inf'), float('inf')  # Initialize alpha and beta for the entire search

    moves = valid_moves(board, player)
    if not moves:
        return None  # No valid moves available

    # Sort moves based on some heuristic for potentially better pruning
    moves = sorted(moves, key=lambda move: score_move_for_ordering(board, move, player, zobrist_keys, current_hash), reverse=True)

    for move in moves:
        new_board, new_hash = make_move([row[:] for row in board], move[0], move[1], player, zobrist_keys, current_hash)
        score = minimax(new_board, depth - 1, alpha, beta, False, 3 - player, zobrist_keys, new_hash)  # False assumes minimizing for the opponent
        
        if score > best_score:
            best_score = score
            best_moves = [move]
            alpha = max(alpha, score)  # Update alpha after finding a new best move
            if alpha >= beta:
                break  # Beta cut-off
        elif score == best_score:
            best_moves.append(move)

    return best_moves[0] if best_moves else None

def find_best_move(board, player, zobrist_keys, current_hash, max_depth=5):
    best_move = None
    best_score = float('-inf')

    for depth in range(1, max_depth + 1):
        current_alpha, current_beta = float('-inf'), float('inf')
        local_best_score = float('-inf')
        local_best_move = None

        moves = valid_moves(board, player)
        moves = sorted(moves, key=lambda move: score_move_for_ordering(board, move, player, zobrist_keys, current_hash), reverse=True)

        for move in moves:
            new_board, new_hash = make_move([row[:] for row in board], move[0], move[1], player, zobrist_keys, current_hash)
            score = minimax(new_board, depth, current_alpha, current_beta, False, 3 - player, zobrist_keys, new_hash)
            #print(f"Evaluating move {move} at depth {depth} with score {score}")

            if score > local_best_score:
                local_best_score = score
                local_best_move = move
                if current_alpha < score:
                    current_alpha = score
                #print(f"New best move at depth {depth}: {local_best_move} with score {local_best_score}")

        if local_best_score > best_score:
            best_score = local_best_score
            best_move = local_best_move
            #print(f"Updating global best move to: {best_move} with score {best_score} at depth {depth}")

        if best_score == float('inf'):
            break

    return best_move if best_move else None
