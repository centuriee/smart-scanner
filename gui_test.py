import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Directory Processor")

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layouts
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        # === TERMINAL WRAPPER ===
        self.terminalWrapper = QVBoxLayout()
        self.terminal_label = QLabel("terminal")
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminalWrapper.addWidget(self.terminal_label)
        self.terminalWrapper.addWidget(self.terminal)

        # === QUEUE WRAPPER ===
        self.queueWrapper = QVBoxLayout()
        self.queue_label = QLabel("queue")
        self.queue = QTextEdit()
        self.queue.setFixedWidth(200)
        self.queue.setReadOnly(True)
        self.queueWrapper.addWidget(self.queue_label)
        self.queueWrapper.addWidget(self.queue)

        top_layout = QHBoxLayout()
        top_layout.addLayout(self.terminalWrapper, 3)
        top_layout.addLayout(self.queueWrapper, 1)

        self.sourceWrapper = QVBoxLayout()
        self.source_label = QLabel("selected directory: ")
        self.source_button = QPushButton("Browse for source")
        self.source_button.clicked.connect(self.browse_source)
        self.sourceWrapper.addWidget(self.source_label)
        self.sourceWrapper.addWidget(self.source_button)

        # -- Destination Directory Section --
        self.destinationWrapper = QVBoxLayout()
        self.dest_label = QLabel("selected directory: ")
        self.dest_button = QPushButton("Browse for destination")
        self.dest_button.clicked.connect(self.browse_destination)
        self.destinationWrapper.addWidget(self.dest_label)
        self.destinationWrapper.addWidget(self.dest_button)

        # -- Run Button --
        self.run_button = QPushButton("run")
        self.run_button.setFixedSize(60, 40)
        self.run_button.clicked.connect(self.run_process)

        # Combine into horizontal bottom layout
        bottom_layout = QHBoxLayout()
        bottom_layout.addLayout(self.sourceWrapper)
        bottom_layout.addLayout(self.destinationWrapper)
        bottom_layout.addWidget(self.run_button)

        # Assemble all into main layout
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        central_widget.setLayout(main_layout)

    def browse_source(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if directory:
            self.source_label.setText(f"selected directory: {directory}")

    def browse_destination(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
        if directory:
            self.dest_label.setText(f"selected directory: {directory}")

    def run_process(self):
        self.terminal.append("Running process...")
        # Placeholder for logic

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(700, 400)
    window.show()
    sys.exit(app.exec())
