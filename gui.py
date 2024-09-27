import sys
import copy
import game_logic
from PyQt5.QtGui import QIcon, QPixmap, QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox, QMessageBox, QCheckBox, QSizePolicy
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal

from game_logic import make_move, initialize_board, valid_moves
from ai import find_best_move, find_best_move_original, init_zobrist, compute_hash
from simulator_greedy import find_greedy_move

class AiWorker(QThread):
    moveComputed = pyqtSignal(tuple)  # Emit a tuple for the move

    def __init__(self, board, player, ai_function, zobrist_keys=None, current_hash=None, depth=None):
        super().__init__()
        self.board = board.copy()  # Make a copy to work with locally
        self.player = player
        self.ai_function = ai_function
        self.zobrist_keys = zobrist_keys
        self.current_hash = current_hash
        self.depth = depth

    def run(self):
        move = self.ai_function(*self.get_args())
        if move:
            self.moveComputed.emit(move)  # Ensure 'move' is a tuple (row, col)
        else:
            self.moveComputed.emit(())  # Emit an empty tuple when no move is found


    def get_args(self):
        if self.ai_function.__name__ == "find_greedy_move":
            return (self.board, self.player)
        elif self.ai_function.__name__ == "find_best_move":
            return (self.board, self.player, self.zobrist_keys, self.current_hash, self.depth)
        else:  # assume find_best_move_original
            return (self.board, self.player, self.depth, self.zobrist_keys, self.current_hash)

class ReversiGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.zobrist_keys = init_zobrist()  # Initialize Zobrist keys at the beginning
        self.game_board = initialize_board()
        self.undo_stack = []
        self.redo_stack = []
        self.current_player = 1  # Define the starting player
        self.current_hash = compute_hash(self.game_board, self.zobrist_keys)  # Compute initial hash
        self.show_legal_moves = True  
        self.ai_depth_original = 5  # Default depth for original Minimax
        self.ai_depth_iterative = 5  # Default depth for iterative deepening        self.ai_move_function = find_best_move_original  # Assign the Minimax move function by default
        self.game_started = False  # Add this line to initialize game_started
        self.human_player = 1  # Default human as Black (1)
        self.ai_player = 2  # Default AI player as black, assuming 1 is black, 2 is white
        self.last_move = None  # Initialize the last_move attribute
        self.initUI()
        self.setupAiWorker()

        self.change_ai(self.ai_selector.currentIndex())


    def setupAiWorker(self):
        self.ai_worker = AiWorker(self.game_board, self.current_player, find_best_move, self.zobrist_keys, self.current_hash, depth=5)
        self.ai_worker.moveComputed.connect(self.update_game_state)  # Connect signal to slot

    def update_game_state(self, move):
        if move:  # This will be False if move is an empty tuple
            if move in valid_moves(self.game_board, self.current_player):
                self.make_move(move[0], move[1])
        else:
            # Handle the situation when no move is possible (e.g., display a message or pass the turn)
            self.show_temporary_message("No valid moves available.", 2000)
            self.switch_player()

    def initUI(self):
        self.setWindowTitle('Reversi Game')
        self.setFixedSize(1150, 880)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        overall_layout = QHBoxLayout(self.central_widget)
        overall_layout.setContentsMargins(0, 0, 0, 10)  # Remove any default margins
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 10)
        
        QFontDatabase.addApplicationFont('Fonts/space.otf')
        self.custom_font = QFont("PlayfulTime", 10)
        font_id = QFontDatabase.addApplicationFont('Fonts/RockBoulder.ttf')
        if font_id == -1:
            print("Failed to load font")
        else:
            families = QFontDatabase.applicationFontFamilies(font_id)
            print("Loaded font families:", families)
            self.custom_font = QFont(families[0], 10)

        # Layout structure
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # Game board setup
        self.setupGameBoard()
        self.central_widget.layout().addLayout(self.grid_layout, 75)

        # Side panel setup
        self.setupSidePanel()
        self.central_widget.layout().addLayout(self.side_panel, 25)

        # Score panel setup
        self.setupScoreDisplay()
        self.side_panel.addWidget(self.score_widget)

        self.central_widget.setLayout(overall_layout)
        self.update_board()

    def setupGameBoard(self):
        # Main game board layout
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        # Column and row labels for the board
        for j in range(8):
            top_label = QLabel(chr(65 + j))  # ASCII A to H
            top_label.setAlignment(Qt.AlignCenter | Qt.AlignBottom)  # Align center and bottom
            top_label.setFont(self.custom_font)
            self.grid_layout.addWidget(top_label, 0, j + 1)

        # Add row headers (numbers)
        for i in range(8):
            left_label = QLabel(str(i + 1))
            left_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Align right and vertically center
            left_label.setFont(self.custom_font)
            self.grid_layout.addWidget(left_label, i + 1, 0)

        # Add row headers (numbers) on the right
        for i in range(8):
            right_label = QLabel(str(i + 1))
            right_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            right_label.setFont(self.custom_font)
            self.grid_layout.addWidget(right_label, i + 1, 9)

        # Add column headers (letters) at the bottom
        for j in range(8):
            bottom_label = QLabel(chr(65 + j))  # ASCII A to H
            bottom_label.setAlignment(Qt.AlignCenter | Qt.AlignTop)
            bottom_label.setFont(self.custom_font)
            self.grid_layout.addWidget(bottom_label, 9, j + 1)


        # Buttons for the board
        self.buttons = []
        for i in range(8):  # 8 rows
            row_buttons = []
            for j in range(8):  # 8 columns
                button = QPushButton()
                button.setFixedSize(QSize(90, 90))
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                button.setFont(self.custom_font)
                button.setEnabled(False)  # Disable the button initially
                button.clicked.connect(lambda ch, i=i, j=j: self.make_move(i, j))
                self.grid_layout.addWidget(button, i + 1, j + 1)
                row_buttons.append(button)
            self.buttons.append(row_buttons)
        
        bottom_spacer = QLabel("")
        self.grid_layout.addWidget(bottom_spacer, 10, 0, 1, 10)  # Span the whole bottom row

        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)


    def setupSidePanel(self):
        self.side_panel = QVBoxLayout()
        self.side_panel.setSpacing(5)  # Reduce spacing between widgets
        self.side_panel.setContentsMargins(0, 0, 30, 0)  # (left, top, right, bottom)

        def create_label(text):
            label = QLabel(text)
            label.setFont(self.custom_font)  # Bold and size 12 font
            return label
        
        # Status message
        self.label_status = QLabel("Welcome to Reversi!")
        self.label_status.setFont(self.custom_font)
        self.label_status.setAlignment(Qt.AlignCenter)
        self.side_panel.addWidget(self.label_status)

        # Game information
        info_label = QLabel("Game Information:")
        info_label.setContentsMargins(0, 0, 0, 0)  # Remove
        info_label.setFont(self.custom_font)
        self.side_panel.addWidget(info_label)
        
        self.info_text = QLabel("Reversi is a strategy board game that involves capturing your opponent's discs by outmaneuvering them. The game starts with four discs (two black and two white) placed in the center of the board. Players take turns placing their discs on the board, flipping their opponent's discs when they are outflanked by their own color. The objective is to have the majority of discs at the end of the game.")
        self.info_text.setContentsMargins(0, 0, 0, 0)  # Remove margins around the text
        self.info_text.setWordWrap(True)
        self.info_text.setFont(self.custom_font)
        self.side_panel.addWidget(self.info_text)

        self.side_panel.addWidget(create_label("Select Starting Piece:"))

        # Starting piece selector
        self.piece_selector = QComboBox()
        self.piece_selector.addItems(['Black', 'White'])
        self.piece_selector.setFont(self.custom_font)
        self.piece_selector.currentIndexChanged.connect(self.change_starting_piece)
        self.side_panel.addWidget(self.piece_selector)

        self.side_panel.addWidget(create_label("Select AI Strategy:"))

        # AI strategy selector
        self.ai_selector = QComboBox()
        self.ai_selector.addItems(['Greedy', 'Minimax', 'Minimax with Iterative Deepening'])
        self.ai_selector.setFont(self.custom_font)
        self.ai_selector.currentIndexChanged.connect(self.change_ai)
        self.side_panel.addWidget(self.ai_selector)


        #self.side_panel.addWidget(create_label("Select Difficulty:"))
        self.difficulty_label = QLabel("Select Difficulty:")
        self.difficulty_label.setFont(self.custom_font)
        self.side_panel.addWidget(self.difficulty_label)

        # Difficulty selection dropdown
        self.difficulty_selector = QComboBox()
        self.difficulty_selector.addItems(['Easy', 'Medium', 'Hard'])
        self.difficulty_selector.setFont(self.custom_font)
        self.difficulty_selector.currentIndexChanged.connect(self.change_difficulty)
        self.side_panel.addWidget(self.difficulty_selector)

        # Legal moves checkbox
        self.legal_moves_checkbox = QCheckBox("Show Legal Moves")
        self.legal_moves_checkbox.setChecked(True)
        self.legal_moves_checkbox.stateChanged.connect(self.toggle_legal_moves)
        self.legal_moves_checkbox.setFont(self.custom_font)  # Match the font style and size
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.legal_moves_checkbox)  # Align to the right
        self.side_panel.addLayout(checkbox_layout)  # Add this layout to the side panel

        # Hints checkbox
        self.greedy_hints_checkbox = QCheckBox("Show Greedy Hints")
        self.greedy_hints_checkbox.setChecked(False)  # Default to not showing hints
        self.greedy_hints_checkbox.setFont(self.custom_font)  # Consistent font size
        self.greedy_hints_checkbox.stateChanged.connect(self.update_board)  # Refresh board when toggled
        self.side_panel.addWidget(self.greedy_hints_checkbox)

        # Add a checkbox for showing the last move
        self.show_last_move_checkbox = QCheckBox("Show Last Move")
        self.show_last_move_checkbox.setChecked(False)  # Default to not showing the last move
        self.show_last_move_checkbox.stateChanged.connect(self.update_board)  # Refresh board when toggled
        self.show_last_move_checkbox.setFont(self.custom_font)  # Ensure font consistency
        self.side_panel.addWidget(self.show_last_move_checkbox)

        # Start game button
        self.start_game_button = QPushButton("Start Game")
        self.start_game_button.setFont(self.custom_font)
        self.start_game_button.clicked.connect(self.start_game)
        self.side_panel.addWidget(self.start_game_button)
        # Add stretch to push everything up and the score to the bottom
        # self.side_panel.addStretch(1)


        # Undo and Redo buttons
        undo_button = QPushButton("Undo")
        undo_button.setObjectName("undoButton")
        undo_button.setFont(self.custom_font)
        undo_button.clicked.connect(self.undo_move)
        undo_button.setEnabled(False)  # Initially disabled
        self.side_panel.addWidget(undo_button)

        redo_button = QPushButton("Redo")
        redo_button.setObjectName("redoButton")
        redo_button.setFont(self.custom_font)
        redo_button.clicked.connect(self.redo_move)
        redo_button.setEnabled(False)  # Initially disabled
        self.side_panel.addWidget(redo_button)

        self.restart_game_button = QPushButton("Restart Game")
        self.restart_game_button.setFont(self.custom_font)
        self.restart_game_button.clicked.connect(self.restart_game)
        self.side_panel.addWidget(self.restart_game_button)

        # Turn information
        self.label_turn = QLabel("Turn: Black")
        self.label_turn.setFont(self.custom_font)
        self.label_turn.setAlignment(Qt.AlignCenter)
        self.side_panel.addWidget(self.label_turn)



    def restart_game(self):
        # Reset game state
        self.game_board = initialize_board()
        self.current_hash = compute_hash(self.game_board, self.zobrist_keys)
        self.current_player = 1  # Assuming 1 is Black
        self.ai_player = 2  # Assuming 2 is White
        self.show_legal_moves = True
        self.legal_moves_checkbox.setChecked(True)

        # Reset dropdowns to default values
        self.ai_selector.setCurrentIndex(self.ai_selector.findText("Greedy"))
        self.piece_selector.setCurrentIndex(self.piece_selector.findText("Black"))
        self.difficulty_selector.setCurrentIndex(self.difficulty_selector.findText("Easy"))

        # Re-enable UI elements
        self.ai_selector.setEnabled(True)
        self.piece_selector.setEnabled(True)
        self.start_game_button.setEnabled(True)
        #self.difficulty_selector.setEnabled(True)
        self.game_started = False  # Reset the game start status
        self.enable_game_controls(False)  # Disable all game controls
        self.update_board()

    def setupScoreDisplay(self):
        self.score_layout = QHBoxLayout()

        # Create the label for the black score
        self.black_score_icon = QLabel()
        self.black_score_icon.setPixmap(QPixmap('Media/black_disk.png').scaled(20, 20, Qt.KeepAspectRatio))
        self.black_score_label = QLabel("Black: 2")
        self.black_score_label.setFont(self.custom_font)

        # Create the label for the white score
        self.white_score_icon = QLabel()
        self.white_score_icon.setPixmap(QPixmap('Media/white_disk.png').scaled(20, 20, Qt.KeepAspectRatio))
        self.white_score_label = QLabel("White: 2")
        self.white_score_label.setFont(self.custom_font)

        # Add widgets to the layout
        self.score_layout.addWidget(self.black_score_icon)
        self.score_layout.addWidget(self.black_score_label)
        self.score_layout.addStretch()  # This will center the score labels
        self.score_layout.addWidget(self.white_score_icon)
        self.score_layout.addWidget(self.white_score_label)

        # Create a wrapper widget for layout
        self.score_widget = QWidget()
        self.score_widget.setLayout(self.score_layout)

    def undo_move(self):
        if self.undo_stack:
            self.redo_stack.append((copy.deepcopy(self.game_board), self.current_hash, self.current_player))
            self.game_board, self.current_hash, self.current_player = self.undo_stack.pop()
            self.last_move = self.undo_stack[-1][0] if self.undo_stack else None
            self.update_board()

    def redo_move(self):
        if self.redo_stack:
            self.undo_stack.append((copy.deepcopy(self.game_board), self.current_hash, self.current_player))
            self.game_board, self.current_hash, self.current_player = self.redo_stack.pop()
            self.last_move = self.redo_stack[-1][0] if self.redo_stack else None
            self.update_board()

    def change_ai(self, index):
        ai_choice = self.ai_selector.currentText()
        if ai_choice == "Greedy":
            self.difficulty_selector.setEnabled(False)  # Disable the dropdown
            self.difficulty_label.setEnabled(False)  # Disable the label
            self.ai_move_function = find_greedy_move  # Use the function directly without self.
        elif ai_choice == "Minimax":
            self.difficulty_selector.setEnabled(True)  # Disable the dropdown
            self.difficulty_label.setEnabled(True)  # Disable the label
            self.ai_move_function = find_best_move_original  # Use the function directly without self.
        elif ai_choice == "Minimax with Iterative Deepening":
            self.difficulty_label.setEnabled(True)  # Disable the label
            self.difficulty_selector.setEnabled(True)  # Disable the dropdown
            self.ai_move_function = find_best_move  # Use the function directly without self.
        # Refresh AI move logic if the game has started and it's AI's turn
        if self.game_started and self.current_player == self.ai_player:
            QTimer.singleShot(500, self.perform_ai_move)

    def change_starting_piece(self, index):
        starting_piece = self.piece_selector.currentText()
        if starting_piece == "White":
            self.human_player = 2  # Human is White
            self.ai_player = 1     # AI is Black
            self.current_player = 1  # AI starts as Black
        else:
            self.human_player = 1  # Human is Black
            self.ai_player = 2     # AI is White
            self.current_player = 1  # Human starts as Black

        # Update the board and possibly trigger AI move if it's AI's turn
        self.update_board()

        if self.current_player == self.ai_player:
            QTimer.singleShot(500, self.perform_ai_move)  # Trigger AI move immediately

        # Update the display to show legal moves for the current player
        self.update_board()

    def update_game_start(self):
        # Prepare or reset the game board, depending on your implementation
        self.game_board = initialize_board()
        self.current_hash = compute_hash(self.game_board, self.zobrist_keys)

        # Determine who starts based on the player's choice of color
        starting_piece = self.piece_selector.currentText()
        if starting_piece == "White":
            self.current_player = 1  # AI as Black
            self.human_player = 2
            self.ai_player = 1
        else:
            self.current_player = 1  # Human as Black
            self.human_player = 1
            self.ai_player = 2

        # If AI is supposed to start, make its move
        if self.current_player == self.ai_player:
            QTimer.singleShot(500, self.perform_ai_move)

        self.update_board()

    def enable_game_controls(self, enable):
        for row_buttons in self.buttons:
            for button in row_buttons:
                button.setEnabled(enable)

    def start_game(self):
        # Disable configuration controls after starting the game
        self.game_started = True  # Flag to indicate the game has started
        self.last_move = None  # Reset the last move at the start of the game
        self.update_game_start()
        self.enable_game_controls(True)  # Enable all game controls

        self.ai_selector.setDisabled(True)
        self.piece_selector.setDisabled(True)
        self.start_game_button.setDisabled(True)
        self.difficulty_selector.setDisabled(True)

        self.ai_strategy = self.ai_selector.currentText()

        # Set the game board, initialize scores, and reset any necessary variables
        self.game_board = initialize_board()
        self.current_hash = compute_hash(self.game_board, self.zobrist_keys)

        # If the current player is the AI player, trigger the AI to make a move
        if self.current_player == self.ai_player:
            QTimer.singleShot(500, self.perform_ai_move) 

    def toggle_legal_moves(self, state):
        self.show_legal_moves = state == Qt.Checked
        self.update_board()

    def change_difficulty(self, index):
        depth_limits_original = {0: 5, 1: 6, 2: 6}
        depth_limits_iterative = {0: 8, 1: 11 , 2: 15}
        time_limits = {0: 2.0, 1: 5.0, 2: 10.0}  # Example time limits in seconds for each difficulty

        # Set depths according to the AI strategy
        self.ai_depth_original = depth_limits_original[index]
        self.ai_depth_iterative = depth_limits_iterative[index]
        self.ai_time_limit = time_limits[index]  # Time limit based on difficulty

        # Display the current setting
        print(f"Difficulty set to {self.difficulty_selector.currentText()}, Original Depth: {self.ai_depth_original}, Iterative Depth: {self.ai_depth_iterative}, Time Limit: {self.ai_time_limit}s")

    def make_move(self, row, col):
        print(f"Making move at ({row}, {col}) with player {self.current_player}")
        #print(f"Zobrist Keys: {self.zobrist_keys}")
        print(f"Current Hash: {self.current_hash}")    
        valid_moves_list = valid_moves(self.game_board, self.current_player)
        if (row, col) in valid_moves_list:
            # Pass zobrist_keys and current_hash to the game_logic's make_move function
            self.undo_stack.append((copy.deepcopy(self.game_board), self.current_hash, self.current_player))
            self.redo_stack.clear()  # Clear the redo stack whenever a new move is made
            self.game_board, self.current_hash = game_logic.make_move(self.game_board, row, col, self.current_player, self.zobrist_keys, self.current_hash)
            self.last_move = (row, col)

            self.update_board()
            if not self.check_game_end():
                self.switch_player()
            else:
                black_count = sum(row.count(1) for row in self.game_board)
                white_count = sum(row.count(2) for row in self.game_board)
                winner = "Black" if black_count > white_count else "White"
                QMessageBox.information(self, "Game Over", f"{winner} wins!")
        else:
            self.show_temporary_message("Invalid move. Try again.", 2000)

    def perform_ai_move(self):
        if not self.game_started or self.current_player != self.ai_player:
            return

        if self.ai_strategy == "Greedy":
            ai_function = find_greedy_move
            worker_args = {
                'board': self.game_board.copy(),
                'player': self.current_player,
                'ai_function': ai_function
            }
        elif self.ai_strategy == "Minimax with Iterative Deepening":
            ai_function = find_best_move
            worker_args = {
                'board': self.game_board.copy(),
                'player': self.current_player,
                'ai_function': ai_function,
                'zobrist_keys': self.zobrist_keys,
                'current_hash': self.current_hash,
                'depth': self.ai_depth_iterative
            }
        else:  # Default to original Minimax
            ai_function = find_best_move_original
            worker_args = {
                'board': self.game_board.copy(),
                'player': self.current_player,
                'ai_function': ai_function,
                'zobrist_keys': self.zobrist_keys,
                'current_hash': self.current_hash,
                'depth': self.ai_depth_original
            }

        self.ai_worker = AiWorker(**worker_args)
        self.ai_worker.moveComputed.connect(self.ai_move_received)
        self.ai_worker.start()

    def ai_move_received(self, move):
        print("Received move from AI:", move)
        if move and isinstance(move, tuple) and (move[0], move[1]) in valid_moves(self.game_board, self.current_player):
            self.make_move(move[0], move[1])

    def switch_player(self):
        self.current_player = 3 - self.current_player  # Switches between 1 (Black) and 2 (White)
        self.label_turn.setText(f"Turn: {'Black' if self.current_player == 1 else 'White'}")

        # Refresh the UI and possibly trigger AI move
        if self.game_started:
            self.update_board()
            if self.current_player == self.ai_player and not self.check_game_end():
                QTimer.singleShot(500, self.perform_ai_move)  # Trigger AI move if it's AI's turn

    def check_game_end(self):
        black_count = sum(row.count(1) for row in self.game_board)
        white_count = sum(row.count(2) for row in self.game_board)
        if black_count == 0 or white_count == 0 or black_count + white_count == 64:
            #self.show_temporary_message(f"Game over. {'Black' if black_count > white_count else 'White'} wins.", 5000)
            return True
        return False

    def simulate_move(self, temp_board, row, col, player):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        to_flip = []

        for dr, dc in directions:
            r, c = row + dr, col + dc
            flip = []
            while 0 <= r < len(temp_board) and 0 <= c < len(temp_board[0]) and temp_board[r][c] == 3 - player:
                flip.append((r, c))
                r += dr
                c += dc
            if 0 <= r < len(temp_board) and 0 <= c < len(temp_board[0]) and temp_board[r][c] == player and flip:
                to_flip.extend(flip)

        if to_flip:
            temp_board[row][col] = player  # Actually apply the move
            for r, c in to_flip:
                temp_board[r][c] = player
            return len(to_flip)
        return 0  # Return the number of pieces flipped

    def calculate_greedy_gain(self, row, col):
        # Clone the current board
        temp_board = [list(r) for r in self.game_board]
        # Assume player is the current player
        player = self.current_player
        # Calculate potential gains by simulating the move
        return self.simulate_move(temp_board, row, col, player)

    def update_board(self):
        black_count = sum(row.count(1) for row in self.game_board)
        white_count = sum(row.count(2) for row in self.game_board)
        self.black_score_label.setText(f"Black: {black_count}")
        self.white_score_label.setText(f"White: {white_count}")
        black_disc_icon = QIcon('Media/black_disk.png')
        white_disc_icon = QIcon('Media/white_disk.png')
        grey_circle_icon = QIcon('Media/grey_disk.png')  # Load the grey circle icon
        size = QSize(64, 64)
        undo_button = self.findChild(QPushButton, "undoButton")  # Make sure button names are set correctly in setupSidePanel
        redo_button = self.findChild(QPushButton, "redoButton")

        if undo_button and redo_button:
            undo_button.setEnabled(bool(self.undo_stack))
            redo_button.setEnabled(bool(self.redo_stack))

        last_move = self.last_move if hasattr(self, 'last_move') else None  # Track the last move

        for i in range(8):
            for j in range(8):
                self.buttons[i][j].setIconSize(size)
                if self.game_board[i][j] == 1:
                    self.buttons[i][j].setIcon(black_disc_icon)
                elif self.game_board[i][j] == 2:
                    self.buttons[i][j].setIcon(white_disc_icon)
                else:
                    self.buttons[i][j].setIcon(QIcon())

                # Highlight the last move if the checkbox is checked
                if self.show_last_move_checkbox.isChecked() and self.last_move == (i, j):
                    self.buttons[i][j].setStyleSheet("background-color: rgba(0, 255, 0, 0.3);")  # Semi-transparent green
                else:
                    self.buttons[i][j].setStyleSheet("")

                # Show valid moves for the human player with a grey circle
                if self.current_player == self.human_player and self.show_legal_moves and (i, j) in valid_moves(self.game_board, self.current_player):
                    # Show legal moves for the current player
                    self.buttons[i][j].setIcon(grey_circle_icon)
                    self.buttons[i][j].setIconSize(QSize(45, 45))
                else:
                    if self.game_board[i][j] == 0:
                        self.buttons[i][j].setIcon(QIcon())

                if self.current_player == self.human_player and self.greedy_hints_checkbox.isChecked() and (i, j) in valid_moves(self.game_board, self.current_player):
                    potential_gain = self.calculate_greedy_gain(i, j)
                    self.buttons[i][j].setText(str(potential_gain))  # Show potential gain on the button
                    
                else:
                    self.buttons[i][j].setText("")
             
    def show_temporary_message(self, message, duration):
        self.label_status.setText(message)
        QTimer.singleShot(duration, self.clear_status_message)

    def clear_status_message(self):
        self.label_status.setText("")