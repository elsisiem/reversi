def initialize_board():
    """
    Initializes the Reversi board with the standard starting position.

    Returns:
        board (list of lists): An 8x8 grid initialized for the start of a Reversi game.
    """
    board = [[0]*8 for _ in range(8)]
    board[3][3], board[4][4] = 2, 2  # White starts in the center
    board[3][4], board[4][3] = 1, 1  # Black starts in the center
    return board

def print_board(board):
    """
    Prints the board to the console for debugging purposes.

    Args:
        board (list of lists): The Reversi game board to print.
    """
    print("  " + " ".join(str(i) for i in range(8)))
    for i, row in enumerate(board):
        print(i, ' '.join({0: '.', 1: 'B', 2: 'W'}[x] for x in row))

def valid_moves(board, player):
    """
    Determines all valid moves for the given player.

    Args:
        board (list of lists): The current state of the game board.
        player (int): The player number (1 for black, 2 for white).

    Returns:
        list of tuples: A list of valid (row, col) moves for the player.
    """
    valid = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == 0:  # Look only at empty spaces
                if can_flip(board, r, c, player):
                    valid.append((r, c))
    return valid

def can_flip(board, row, col, player):
    """
    Checks if placing a disc at the given position will flip at least one opponent's disc.

    Args:
        board (list of lists): The current game board.
        row (int): Row index for the potential move.
        col (int): Column index for the potential move.
        player (int): The player making the move.

    Returns:
        bool: True if at least one disc can be flipped, False otherwise.
    """
    opponent = 2 if player == 1 else 1
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    can_flip_any = False
    for dr, dc in directions:
        r, c = row + dr, col + dc
        found_opponent = False
        while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == opponent:
            r += dr
            c += dc
            found_opponent = True
        if found_opponent and 0 <= r < 8 and 0 <= c < 8 and board[r][c] == player:
            if check_path(board, row+dr, col+dc, dr, dc, player):
                can_flip_any = True
    return can_flip_any

def check_path(board, start_r, start_c, dr, dc, player):
    """
    Helper function to check along a direction from a starting point to see if it ends at the current player's disc,
    meaning the path is valid for a flip.

    Args:
        board (list of lists): The game board.
        start_r (int): Starting row index.
        start_c (int): Starting column index.
        dr (int): Row direction increment.
        dc (int): Column direction increment.
        player (int): The player number.

    Returns:
        bool: True if path is valid for a flip, False otherwise.
    """
    r, c = start_r, start_c
    while 0 <= r < 8 and 0 <= c < 8 and board[r][c] != player:
        r += dr
        c += dc
    return r >= 0 and r < 8 and c >= 0 and c < 8 and board[r][c] == player

def make_move(board, row, col, player, zobrist_keys=None, current_hash=None):
    """
    Executes a move by placing a disc at the specified location, flipping the opponent's discs accordingly,
    and updates the Zobrist hash if zobrist_keys and current_hash are provided.

    Args:
        board (list of lists): The current game board.
        row (int): The row to place the disc.
        col (int): The column to place the disc.
        player (int): The player making the move.
        zobrist_keys (dict, optional): Zobrist hashing keys.
        current_hash (int, optional): Current Zobrist hash of the board.

    Returns:
        tuple: The updated game board and the new hash if applicable.
    """
    board[row][col] = player
    if zobrist_keys is not None and current_hash is not None:
        current_hash ^= zobrist_keys[(row, col)][player]

    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in directions:
        if can_flip_path(board, row, col, dr, dc, player):
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8 and board[r][c] != player:
                board[r][c] = player
                if zobrist_keys is not None and current_hash is not None:
                    opponent = 3 - player
                    current_hash ^= zobrist_keys[(r, c)][opponent]
                    current_hash ^= zobrist_keys[(r, c)][player]
                r += dr
                c += dc
    return board, current_hash if zobrist_keys is not None else board


def can_flip_path(board, row, col, dr, dc, player):
    """
    Determines if there is a valid path to flip discs in a given direction from the specified start point.

    Args:
        board (list of lists): The current game board.
        row (int): Start row index.
        col (int): Start column index.
        dr (int): Direction increment for rows.
        dc (int): Direction increment for columns.
        player (int): The player number.

    Returns:
        bool: True if there is a valid path for flipping discs, False otherwise.
    """
    r, c = row + dr, col + dc
    found_opponent = False
    while 0 <= r < 8 and 0 <= c < 8 and board[r][c] != 0 and board[r][c] != player:
        if board[r][c] != player:
            found_opponent = True
        r += dr
        c += dc
    return found_opponent and r >= 0 and r < 8 and c >= 0 and c < 8 and board[r][c] == player

def flip_discs(board, row, col, dr, dc, player):
    """
    Flips discs in a given direction from the specified start point.

    Args:
        board (list of lists): The current game board.
        row (int): Start row index.
        col (int): Start column index.
        dr (int): Direction increment for rows.
        dc (int): Direction increment for columns.
        player (int): The player number.
    """
    r, c = row + dr, col + dc
    while 0 <= r < 8 and 0 <= c < 8 and board[r][c] != player:
        board[r][c] = player
        r += dr
        c += dc
