import sys
from PyQt5.QtWidgets import QApplication
from gui import ReversiGUI

def main():
    """
    Main function to start the Reversi game application.
    """
    app = QApplication(sys.argv)  # Create an application object for PyQt
    ex = ReversiGUI()             # Create an instance of the ReversiGUI class
    ex.show()                     # Show the main window
    sys.exit(app.exec_())         # Start the main loop of the application

if __name__ == '__main__':
    main()
