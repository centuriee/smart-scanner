import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Directory Chooser")
        self.default_dir = os.path.dirname(os.path.abspath(__file__))

        central_widget = QWidget()
        layout = QVBoxLayout()

        self.label = QLabel(f"Default Directory: {self.default_dir}")
        self.buttonDir = QPushButton("Browse for Directory")
        self.buttonDir.clicked.connect(self.choose_directory)

        self.buttonPush = QPushButton("Press Me!")
        self.buttonPush.setCheckable(True)
        self.buttonPush.clicked.connect(self.the_button_was_clicked)

        # Set the central widget of the Window.
        layout.addWidget(self.label)
        layout.addWidget(self.buttonDir)
        layout.addWidget(self.buttonPush)
    
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Store the current directory
        self.selected_dir = self.default_dir
    def choose_directory(self):
        selected = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            self.selected_dir
        )
        if selected:
            self.selected_dir = selected
            self.label.setText(f"Selected Directory: {selected}")
        else:
            self.label.setText("No directory selected.")

    def the_button_was_clicked(self):
        print(f"Current selected directory: {self.selected_dir}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())