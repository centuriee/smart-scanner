import sys
from PySide6.QtWidgets import QApplication
from mainWindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600) # set initial window size to 800x600px
    window.setMinimumSize(600, 450)
    window.show()
    sys.exit(app.exec())