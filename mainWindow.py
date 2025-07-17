import os
import re
import time
import threading
from datetime import datetime
from PySide6 import QtGui
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QTextEdit
)

from watchdog.observers import Observer

from scripts.documentParser import parseDocument
from scripts.fileFunctions import (
    getFilename, writeToMarkdown, writeToJSON, loadConfig,
    saveSource, saveDestination, sanitizeFilename, renameFile,
    moveDocument, moveJSON
)
from scripts.aiFunctions import analyzeDocument
from eventHandler import MyEventHandler

file_stack = []
stack_lock = threading.Lock()

class MainWindow(QMainWindow):
    
    clearQueueSignal = Signal()
    appendQueueSignal = Signal(str)

    def __init__(self):
        super().__init__()
        self.clearQueueSignal.connect(self.clear_queue)
        self.appendQueueSignal.connect(self.append_to_queue)
        self.setWindowTitle("Directory Chooser + File Monitor")
        config = loadConfig()
        self.selectedSrc = config.get("source_path")
        self.selectedDir = config.get("destination_path")
        self.observer = None
        self.observer_thread = None
        self.mover_thread = None
        self.monitoring = False

        # UI Setup
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        # terminal
        self.terminalWrapper = QVBoxLayout()
        self.terminal_label = QLabel("Terminal")
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminalWrapper.addWidget(self.terminal_label)
        self.terminalWrapper.addWidget(self.terminal)

        # queue
        self.queueWrapper = QVBoxLayout()
        self.queue_label = QLabel("Queue")
        self.queue = QTextEdit()
        self.queue.setFixedWidth(200)
        self.queue.setReadOnly(True)
        self.queueWrapper.addWidget(self.queue_label)
        self.queueWrapper.addWidget(self.queue)

        topLayout = QHBoxLayout()
        topLayout.addLayout(self.terminalWrapper, 3)
        topLayout.addLayout(self.queueWrapper, 1)

        self.sourceWrapper = QVBoxLayout()
        self.labelsrc = QLabel(f"Source Folder: {self.selectedSrc}")
        self.labelsrc.setWordWrap(True)
        self.buttonSrc = QPushButton("Browse for Source")
        self.buttonSrc.clicked.connect(self.choose_src)
        self.sourceWrapper.addWidget(self.labelsrc)
        self.sourceWrapper.addWidget(self.buttonSrc)

        self.destinationWrapper = QVBoxLayout()
        self.labeldst = QLabel(f"Destination Folder: {self.selectedDir}")
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

    def is_valid_file(self, filepath):
        _, ext = os.path.splitext(filepath)
        return ext.lower() in {'.pdf', '.img'}

    def choose_src(self):
        selected = QFileDialog.getExistingDirectory(self, "Select Directory", self.selectedSrc)
        if selected:
            self.selectedSrc = selected
            self.labelsrc.setText(f"Source Folder: {selected}")
            self.append_to_terminal(f"Source directory set and saved to {selected}")
            saveSource(self.selectedSrc)
        else:
            self.labelsrc.setText("No directory selected.")
            self.append_to_terminal(f"Source directory set to none")

    def choose_dst(self):
        selected = QFileDialog.getExistingDirectory(self, "Select Directory", self.selectedDir)
        if selected:
            self.selectedDir = selected
            self.labeldst.setText(f"Destination Folder: {selected}")
            self.append_to_terminal(f"Destination directory set and saved to {selected}")
            saveDestination(self.selectedDir)
        else:
            self.labeldst.setText("No directory selected.")
            self.append_to_terminal(f"Destination directory set to none")

    def toggle_monitoring(self):
        if not self.monitoring:
            self.append_to_terminal("<b>File monitoring starting.</b>")
            self.start_observer()
        else:
            self.append_to_terminal("<b>File monitoring stopped. Queued files will continue parsing.</b>")
            self.stop_observer()

    def append_to_terminal(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.terminal.append(f"<b></b>[{timestamp}] {text}")
        self.terminal.moveCursor(QtGui.QTextCursor.End)

    def append_to_queue(self, text: str):
        self.queue.append(text)

    def clear_queue(self):
        self.queue.clear()

    def start_observer(self):
        print("Starting observer and stack mover...")
        self.monitoring = True
        self.buttonRun.setText("Stop")

        # Scan the directory ONCE
        for filename in os.listdir(self.selectedSrc):
            full_path = os.path.join(self.selectedSrc, filename)
            if os.path.isfile(full_path):
                if self.is_valid_file(full_path):
                    with stack_lock:
                        file_stack.append(full_path)  # Add to top of stack
                        self.append_to_terminal(f"Initial file detected: {os.path.splitext(os.path.basename(full_path))[0]}. Added to queue.")
                else: print("file not supported")
            

        # Start watchdog observer
        def run_observer():
            event_handler = MyEventHandler(self.selectedSrc, self, file_stack, stack_lock)
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

        
        self.observer_thread = threading.Thread(target = run_observer, daemon = True)
        self.observer_thread.start()

        # Start a thread to move files from stack
        def move_files():
            queue_was_empty = False # flag for empty queue
            while self.monitoring:
                self.clearQueueSignal.emit()
                if file_stack:
                    queue_was_empty = False
                    with stack_lock:
                        count = 0
                        for item in reversed(file_stack):
                            match = re.search(r'([^\\/]+\.pdf)$', item)
                            if match:
                                filename = match.group(1)
                                if count == 0:
                                    self.appendQueueSignal.emit(f">> {filename}\n")
                                else:
                                    self.appendQueueSignal.emit(f"[{count}] {filename}\n")
                                count += 1
                        filepath = file_stack.pop()  # Top of the stack
                    time.sleep(1) # for no crash

                    if os.path.exists(filepath):
                        try:
                            # PROCESSING
                            filename = getFilename(filepath, 0)
                            print(f"Processing {filename}\n")
                            self.append_to_terminal(f"<b>Processing {filename}.</b>")

                            time.sleep(1) # giving the program a quick rest

                            print(f"Parsing {filename}")
                            self.append_to_terminal("Starting parsing...")
                            doc = parseDocument(filepath) # parsing document
                            print(f"{filename} parsed")
                            self.append_to_terminal(f"{filename} successfully parsed.")
                            time.sleep(1) # giving the program a quick rest

                            # for checking purposes, uncomment if not needed
                            # mdFilename = getFilename(filepath, 2)
                            # writeToMarkdown(doc, mdFilename)

                            print(f"Analyzing {filename}")
                            self.append_to_terminal("Starting document analysis...")
                            documentMetadata = analyzeDocument(doc, filename)
                            self.append_to_terminal(f"Metadata successfully extracted, document classified as <b>{documentMetadata.classification.type.upper()}</b>.")
                            jsonFilename = getFilename(filepath, 1)
                            json_path = os.path.join(os.path.dirname(filepath), jsonFilename)
                            writeToJSON(documentMetadata, json_path)

                            print(f"Processed {filename}")

                            new_filename, classification, original_filename, author, subject, year = renameFile(json_path, filepath)
                            self.append_to_terminal(f"{original_filename} has been renamed to <b>{new_filename}</b>.")

                            destination_path = moveDocument(filepath, new_filename, classification.get("type", "Uncategorized"), self.selectedDir)

                            time.sleep(1) # giving the program a quick rest

                            moveJSON(json_path, author, subject, year, classification.get("type", "Uncategorized"), self.selectedDir)

                            self.append_to_terminal(f"{new_filename} and its associated JSON file has been moved to {os.path.dirname(destination_path)}.")
                            self.append_to_terminal(f"<b>{new_filename} is finished processing.</b>")

                        except Exception as e:
                            print(f"Error processing {filename}: {e}")
                            self.append_to_terminal(f"<b>Error processing {filename}: {e}</b>")
                else:
                    # checker so that empty queue does not get printed forever and ever
                    if not queue_was_empty:
                        self.append_to_terminal("<b>Queue is empty, there are no files to process.</b>")
                        queue_was_empty = True
                    time.sleep(2)  # avoid busy waiting

        self.mover_thread = threading.Thread(target=move_files, daemon=True)
        self.mover_thread.start()

    def stop_observer(self):
        print("Stopping file observer...")
        self.monitoring = False
        self.buttonRun.setText("Run")