import sys
import os
import shutil
import time
import threading
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit
)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from scripts.documentParser import parseDocument
from scripts.fileFunctions import getFilename, getSource, writeToMarkdown, writeToJSON
from scripts.aiFunctions import analyzeDocument

file_stack = []  # LIFO stack
stack_lock = threading.Lock()  # Ensure thread-safe access to the stack

class MyEventHandler(FileSystemEventHandler):
    def __init__(self, source_folder):
        super().__init__()
        self.source_folder = source_folder

    def on_created(self, event):
        if not event.is_directory:
            with stack_lock:
                file_stack.insert(0, event.src_path)
                print(f"File created -> added to bottom of stack: {event.src_path}")

    def on_moved(self, event):
        if not event.is_directory:
            with stack_lock:
                file_stack.insert(0, event.dest_path)
                print(f"File moved -> added to bottom of stack: {event.dest_path}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Directory Chooser + File Monitor")
        self.defaultDir = os.path.dirname(os.path.abspath(__file__))
        self.selectedSrc = self.defaultDir
        self.selectedDir = self.defaultDir

        self.observer = None
        self.observer_thread = None
        self.mover_thread = None
        self.monitoring = False

        # UI Setup
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        # terminal
        self.terminalWrapper = QVBoxLayout()
        self.terminal_label = QLabel("terminal")
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminalWrapper.addWidget(self.terminal_label)
        self.terminalWrapper.addWidget(self.terminal)

        # queue
        self.queueWrapper = QVBoxLayout()
        self.queue_label = QLabel("queue")
        self.queue = QTextEdit()
        self.queue.setFixedWidth(200)
        self.queue.setReadOnly(True)
        self.queueWrapper.addWidget(self.queue_label)
        self.queueWrapper.addWidget(self.queue)

        topLayout = QHBoxLayout()
        topLayout.addLayout(self.terminalWrapper, 3)
        topLayout.addLayout(self.queueWrapper, 1)

        self.sourceWrapper = QVBoxLayout()
        self.labelsrc = QLabel(f"Default Source Directory: {self.defaultDir}")
        self.labelsrc.setWordWrap(True)
        self.buttonSrc = QPushButton("Browse for Source")
        self.buttonSrc.clicked.connect(self.choose_src)
        self.sourceWrapper.addWidget(self.labelsrc)
        self.sourceWrapper.addWidget(self.buttonSrc)

        self.destinationWrapper = QVBoxLayout()
        self.labeldst = QLabel(f"Default Destination Directory: {self.defaultDir}")
        self.labeldst.setWordWrap(True)
        self.buttonDst = QPushButton("Browse for Destination")
        self.buttonDst.clicked.connect(self.choose_dst)
        self.destinationWrapper.addWidget(self.labeldst)
        self.destinationWrapper.addWidget(self.buttonDst)

        self.buttonRun = QPushButton("Run")
        self.buttonRun.setFixedSize(60, 40)
        self.buttonRun.clicked.connect(self.toggle_monitoring)

        bottomLayout = QHBoxLayout()
        bottomLayout.addLayout(self.sourceWrapper)
        bottomLayout.addLayout(self.destinationWrapper)
        bottomLayout.addWidget(self.buttonRun)

        layout = QVBoxLayout()
        layout.addLayout(topLayout)
        layout.addLayout(bottomLayout)

        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    def choose_src(self):
        selected = QFileDialog.getExistingDirectory(self, "Select Directory", self.selectedSrc)
        if selected:
            self.selectedSrc = selected
            self.labelsrc.setText(f"Selected Directory: {selected}")
        else:
            self.labelsrc.setText("No directory selected.")

    def choose_dst(self):
        selected = QFileDialog.getExistingDirectory(self, "Select Directory", self.selectedDir)
        if selected:
            self.selectedDir = selected
            self.labeldst.setText(f"Selected Directory: {selected}")
        else:
            self.labeldst.setText("No directory selected.")

    def toggle_monitoring(self):
        if not self.monitoring:
            self.start_observer()
        else:
            self.stop_observer()

    def start_observer(self):
        print("Starting observer and stack mover...")
        self.monitoring = True
        self.buttonRun.setText("Stop")

        # Scan the directory ONCE
        for filename in os.listdir(self.selectedSrc):
            full_path = os.path.join(self.selectedSrc, filename)
            if os.path.isfile(full_path):
                with stack_lock:
                    file_stack.append(full_path)  # Add to top of stack
                    print(f"Initial scan added: {full_path}")

        # Start watchdog observer
        def run_observer():
            event_handler = MyEventHandler(self.selectedSrc)
            self.observer = Observer()
            self.observer.schedule(event_handler, self.selectedSrc, recursive=False)
            self.observer.start()
            print(f"Watching folder: {self.selectedSrc}")
            try:
                while self.monitoring:
                    time.sleep(1)
            finally:
                self.observer.stop()
                self.observer.join()
                print("Observer stopped.")

        
        self.observer_thread = threading.Thread(target=run_observer, daemon=True)
        self.observer_thread.start()

        # Start a thread to move files from stack
        def move_files():
            while self.monitoring:
                if file_stack:
                    with stack_lock:
                        filepath = file_stack.pop()  # Top of the stack

                    if os.path.exists(filepath):
                        try:
                            # PROCESSING
                            filename = getFilename(filepath, 0)
                            print(f"Processing {filename}...\n")
                            doc = parseDocument(filepath)

                            # for checking purposes, uncomment if not needed
                            mdFilename = getFilename(filepath, 2)
                            writeToMarkdown(doc, mdFilename)

                            documentMetadata = analyzeDocument(doc, filename)
                            jsonFilename = getFilename(filepath, 1)
                            json_path = os.path.join(os.path.dirname(filepath), jsonFilename)
                            writeToJSON(documentMetadata, json_path)

                            print(f"Processed {filename}")

                            # READ TYPE FROM JSON
                            with open(json_path, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)

                            classification = json_data.get("classification", {})
                            doc_type = classification.get("type", "Uncategorized")  # fallback if missing

                            # CREATE FOLDER IF NEEDED
                            type_folder_path = os.path.join(self.selectedDir, doc_type)
                            os.makedirs(type_folder_path, exist_ok=True)

                            # MOVE ORIGINAL FILE
                            filename = os.path.basename(filepath)
                            destination_path = os.path.join(type_folder_path, filename)
                            shutil.move(filepath, destination_path)
                            print(f"Moved file to destination: {destination_path}")

                            # MOVE JSON FILE
                            json_destination_path = os.path.join(type_folder_path, jsonFilename)
                            shutil.move(json_path, json_destination_path)
                            print(f"Generated JSON file at destination")

                        except Exception as e:
                            print(f"Error processing {filename}: {e}")
                else:
                    time.sleep(1)  # avoid busy waiting

        self.mover_thread = threading.Thread(target=move_files, daemon=True)
        self.mover_thread.start()

    def stop_observer(self):
        print("Stopping file observer...")
        self.monitoring = False
        self.buttonRun.setText("Run")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(750, 500)
    window.show()
    sys.exit(app.exec())
