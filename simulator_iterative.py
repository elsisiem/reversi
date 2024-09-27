from game_logic import valid_moves, make_move, initialize_board, print_board
from ai import find_best_move, init_zobrist, compute_hash

zobrist_keys = init_zobrist()

def play_game(ai1, ai2, board, zobrist_keys, verbose=True):
    results = {'Shallow Wins': 0, 'Deep Wins': 0, 'Draws': 0}
    num_games = 10

    for i in range(num_games):
        current_player = 1
        current_hash = compute_hash(board, zobrist_keys)
        move_count = 0

        while valid_moves(board, 1) or valid_moves(board, 2):
            ai = ai1 if current_player == 1 else ai2
            move = ai(board, current_player, zobrist_keys, current_hash)
            if move:
                board, current_hash = make_move(board, move[0], move[1], current_player, zobrist_keys, current_hash)
                if verbose:
                    print(f"Game {i+1}: Player {current_player} moves at {move}")
                    print_board(board)  # Print the board after each move
                current_player = 3 - current_player
                move_count += 1
            else:
                if verbose:
                    print(f"Player {current_player} passes")
                current_player = 3 - current_player  # Switch player if no valid move

            if move_count > 60:  # Safety to prevent infinite loops
                break

        winner = determine_winner(board)
        if winner == 1:
            results['Shallow Wins'] += 1
        elif winner == 2:
            results['Deep Wins'] += 1
        else:
            results['Draws'] += 1

        # Print score for each player
        black_discs = sum(row.count(1) for row in board)
        white_discs = sum(row.count(2) for row in board)
        print(f"Game {i+1}: Score - Black: {black_discs}, White: {white_discs}")

    print("\nFinal Results after {} games:".format(num_games))
    print(results)

def determine_winner(board):
    """Determines the winner based on disc count."""
    black_discs = sum(row.count(1) for row in board)
    white_discs = sum(row.count(2) for row in board)

    if black_discs > white_discs:
        return 1  # Black wins
    elif white_discs > black_discs:
        return 2  # White wins
    else:
        return 0  # Draw

def test_deepening_different_depths():
    board = initialize_board()

    ai_deepening_shallow = lambda board, player, zobrist_keys, current_hash: find_best_move(board, player, zobrist_keys, current_hash, max_depth=3)
    ai_deepening_deep = lambda board, player, zobrist_keys, current_hash: find_best_move(board, player, zobrist_keys, current_hash, max_depth=7)

    play_game(ai_deepening_shallow, ai_deepening_deep, board, zobrist_keys)

# Call the test function
test_deepening_different_depths()
