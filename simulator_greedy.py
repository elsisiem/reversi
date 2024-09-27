from game_logic import valid_moves, make_move, initialize_board, print_board
from ai import find_best_move, find_best_move_original, init_zobrist, compute_hash 
#from ai_with_hashing import find_best_move, find_best_move_original

zobrist_keys = init_zobrist()


def find_greedy_move(board, player):
    """ This function finds the best move based purely on maximizing the immediate number of discs flipped. """
    valid_moves_list = valid_moves(board, player)
    best_move = None
    max_flips = -1
    for move in valid_moves_list:
        temp_board = [row[:] for row in board]
        temp_board, _ = make_move(temp_board, move[0], move[1], player, zobrist_keys, 0)  # Passing a dummy hash value
        num_flips = count_flips(board, temp_board, player)
        if num_flips > max_flips:
            max_flips = num_flips
            best_move = move
    return best_move

def count_flips(original_board, new_board, player):
    """
    Counts the number of pieces flipped between the original and new board states.
    """
    flips = 0
    for r in range(8):
        for c in range(8):
            if original_board[r][c] != new_board[r][c] and new_board[r][c] == player:
                flips += 1
    return flips

def play_game(ai1, ai2, verbose=True):
    """ Simulates a game between two AIs, returning the winner and optionally printing each move's details. 
    ai1 and ai2 are functions that take a board and a player number and return a move. 
    'verbose' controls the amount of detail printed about the game. """
    board = initialize_board()
    current_player = 1
    move_count = 0
    current_hash = compute_hash(board, zobrist_keys)  # Compute initial hash

    if verbose:
        #print("Starting a new game between Minimax and Greedy AI.")

        while valid_moves(board, current_player):
            player_name = "Minimax" if current_player == 1 else "Greedy"
            move = ai1(board, current_player) if current_player == 1 else ai2(board, current_player)
            board, current_hash = make_move(board, move[0], move[1], current_player, zobrist_keys, current_hash)

            #if verbose:
                #print(f"Move {move_count+1} by {player_name}: Placed at {move}.")
                #print_board(board)  # Assuming print_board prints the board to the console.

            current_player = 3 - current_player
            move_count += 1

            if move_count > 60:  # Safety check to prevent infinite loops
                if verbose:
                    print("Ending game due to high move count.")
                break

    black_discs = sum(row.count(1) for row in board)
    white_discs = sum(row.count(2) for row in board)
    winner = "draw"
    if black_discs > white_discs:
        winner = "Minimax"
    elif white_discs > black_discs:
        winner = "Greedy"

    if verbose:
        print(f"Game over. Winner: {winner} (Black: {black_discs}, White: {white_discs})")

    return 1 if winner == "Minimax" else 2 if winner == "Greedy" else 0

def main():
    #ai_minimax = lambda board, player: find_best_move(board, player, zobrist_keys, compute_hash(board, zobrist_keys), max_depth = 10)
    ai_minimax = lambda board, player: find_best_move_original(board, player, 6, zobrist_keys, compute_hash(board, zobrist_keys))
    ai_greedy = lambda board, player: lambda board, player: find_best_move(board, player, zobrist_keys, compute_hash(board, zobrist_keys), max_depth = 10)

    results = {'Minimax Wins': 0, 'Greedy Wins': 0, 'Draws': 0}
    num_games = 10

    for i in range(num_games):
        print(f"Game {i+1}:")
        result = play_game(ai_minimax, ai_greedy, verbose=True)
        if result == 1:
            results['Minimax Wins'] += 1
        elif result == 2:
            results['Greedy Wins'] += 1
        else:
            results['Draws'] += 1

    print("\nFinal Results after {} games:".format(num_games))
    print(results)

if __name__ == "__main__":
    main()
