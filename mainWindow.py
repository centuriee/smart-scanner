# standard lib imports
import os
import re
import time
import threading
from datetime import datetime

# PySide6 imports for GUI
from PySide6 import QtGui
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QTextEdit
)

# watchdog for file monitoring
from watchdog.observers import Observer

# custom modules
from scripts.documentParser import parseDocument
from scripts.fileFunctions import (
    getFilename, writeToMarkdown, writeToJSON, loadConfig,
    saveSource, saveDestination, sanitizeFilename, renameFile,
    moveDocument, moveJSON
)
from scripts.aiFunctions import analyzeDocument
from eventHandler import MyEventHandler

# shared stack and lock for thread-safe file queue
file_stack = []
stack_lock = threading.Lock()

# main application window
class MainWindow(QMainWindow):
    
    # signals for thread-safe queue GUI updates
    clearQueueSignal = Signal()
    appendQueueSignal = Signal(str)

    def __init__(self):
        super().__init__()
        self.clearQueueSignal.connect(self.clear_queue)
        self.appendQueueSignal.connect(self.append_to_queue)

        # window title
        self.setWindowTitle("UPMIN OR Smart Scanner")

        # loading configs from %AppData%
        config = loadConfig()
        self.selectedSrc = config.get("source_path")
        self.selectedDir = config.get("destination_path")

        # variables for watchdog and bg threads
        self.observer = None
        self.observer_thread = None
        self.mover_thread = None
        self.monitoring = False

        # UI SETUP
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

        # top layer of app: terminal 3/4, queue 1/4
        topLayout = QHBoxLayout()
        topLayout.addLayout(self.terminalWrapper, 3)
        topLayout.addLayout(self.queueWrapper, 1)

        # source folder selection
        self.sourceWrapper = QVBoxLayout()
        self.labelsrc = QLabel(f"Source Folder: {self.selectedSrc}")
        self.labelsrc.setWordWrap(True)
        self.buttonSrc = QPushButton("Browse for Source")
        self.buttonSrc.clicked.connect(self.choose_src)
        self.sourceWrapper.addWidget(self.labelsrc)
        self.sourceWrapper.addWidget(self.buttonSrc)

        # destination folder selection
        self.destinationWrapper = QVBoxLayout()
        self.labeldst = QLabel(f"Destination Folder: {self.selectedDir}")
        self.labeldst.setWordWrap(True)
        self.buttonDst = QPushButton("Browse for Destination")
        self.buttonDst.clicked.connect(self.choose_dst)
        self.destinationWrapper.addWidget(self.labeldst)
        self.destinationWrapper.addWidget(self.buttonDst)

        # run/stop button
        self.buttonRun = QPushButton("Run")
        self.buttonRun.setFixedSize(60, 40)
        self.buttonRun.clicked.connect(self.toggle_monitoring)

        # bottom layer of app
        bottomLayout = QHBoxLayout()
        bottomLayout.addLayout(self.sourceWrapper)
        bottomLayout.addLayout(self.destinationWrapper)
        bottomLayout.addWidget(self.buttonRun)

        # putting together top and bottom layouts
        layout = QVBoxLayout()
        layout.addLayout(topLayout)
        layout.addLayout(bottomLayout)

        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    # HELPER: check if file is a supported doc, e.g. .pdf (change soon)
    def is_valid_file(self, filepath):
        _, ext = os.path.splitext(filepath)
        return ext.lower() in {'.pdf'}

    # source folder picker method
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

    # destination folder picker method
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

    # toggles off watchdog file monitoring
    def toggle_monitoring(self):
        if not self.monitoring:
            self.append_to_terminal("<b>File monitoring starting.</b>")
            self.start_observer()
        else:
            self.append_to_terminal("<b>File monitoring stopped. File currently processed will continue processing.</b>")
            self.stop_observer()

    # adding text to pseudoterminal panel with timestamp
    def append_to_terminal(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.terminal.append(f"<b></b><i></i>[{timestamp}] {text}")
        self.terminal.moveCursor(QtGui.QTextCursor.End)

    # adding text to queue panel
    def append_to_queue(self, text: str):
        self.queue.append(text)

    # delete content in queue panel
    def clear_queue(self):
        self.queue.clear()

    # start watchdog observer and queue processor thread
    def start_observer(self):
        print("Starting observer and stack mover...")
        self.monitoring = True
        self.buttonRun.setText("Stop")

        # scan directory and add preexisting files to queue
        for filename in os.listdir(self.selectedSrc):
            full_path = os.path.join(self.selectedSrc, filename)
            if os.path.isfile(full_path) and self.is_valid_file(full_path):
                with stack_lock:
                    if full_path not in file_stack:
                        file_stack.append(full_path)
                        self.append_to_terminal(f"Initial file detected: <i>{os.path.splitext(os.path.basename(full_path))[0]}</i>. Added to queue.")
                    else:
                        print(f"{full_path} already in queue. Skipping.")
            else:
                print(f"{full_path} not supported or is not a file.")
        
        print(file_stack)

        # watchdog folder monitoring
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

        # MAIN: queue processing
        def move_files():
            queue_was_empty = False # flag for empty queue
            while self.monitoring:
                self.clearQueueSignal.emit() # used thread-safe function
                if file_stack:
                    queue_was_empty = False
                    with stack_lock:
                        # appending file names to queue panel
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
                        filepath = file_stack.pop() # top of the stack
                    time.sleep(1) # for no crash

                    if os.path.exists(filepath):
                        try:
                            # PROCESSING
                            filename = getFilename(filepath, 0)
                            print(f"Processing {filename}")
                            self.append_to_terminal(f"<b>Processing <i>{filename}</i>.</b>")
                            time.sleep(1)

                            print(f"Parsing {filename}")
                            self.append_to_terminal("Starting parsing...")
                            doc = parseDocument(filepath) # parsing document using Docling

                            print(f"{filename} parsed")
                            self.append_to_terminal(f"{filename} successfully parsed.")
                            time.sleep(1)

                            # for checking purposes, uncomment if not needed
                            """
                            mdFilename = getFilename(filepath, 2)
                            writeToMarkdown(doc, mdFilename)
                            """

                            print(f"Analyzing {filename}")
                            self.append_to_terminal("Starting document analysis...")
                            documentMetadata = analyzeDocument(doc, filename) # Ollama analysis

                            print(f"done, file is {documentMetadata.classification.type.upper()}")
                            self.append_to_terminal(f"Metadata successfully extracted, document classified as <b><i>{documentMetadata.classification.type.upper()}</i></b>.")
                            jsonFilename = getFilename(filepath, 1)
                            json_path = os.path.join(os.path.dirname(filepath), jsonFilename)
                            writeToJSON(documentMetadata, json_path) # making JSON file

                            print(f"Processed {filename}")

                            new_filename, classification, original_filename, author, subject, year = renameFile(json_path, filepath)
                            self.append_to_terminal(f"<i>{original_filename}</i> has been renamed to <b><i>{new_filename}</i></b>.")

                            destination_path = moveDocument(filepath, new_filename, classification.get("type", "Uncategorized"), self.selectedDir)

                            time.sleep(1)

                            moveJSON(json_path, author, subject, year, classification.get("type", "Uncategorized"), self.selectedDir)

                            self.append_to_terminal(f"<i>{new_filename}</i> and its associated JSON file has been moved to {os.path.dirname(destination_path)}.")
                            self.append_to_terminal(f"<b><i>{new_filename}</i> is finished processing.</b>")
                            self.clearQueueSignal.emit()

                        except Exception as e:
                            print(f"Error processing {filename}: {e}")
                            self.append_to_terminal(f"<b>Error processing {filename}: {e}</b>")
                            self.clearQueueSignal.emit()
                            self.stop_observer()
                else:
                    # checker so that empty queue does not get printed forever and ever
                    if not queue_was_empty:
                        self.append_to_terminal("<b>Queue is empty, there are no files to process.</b>")
                        queue_was_empty = True
                    time.sleep(2) # avoid busy waiting

        self.mover_thread = threading.Thread(target = move_files, daemon = True)
        self.mover_thread.start()

    # stops watchdog and bg thread
    def stop_observer(self):
        print("Stopping file observer...")
        self.monitoring = False
        self.buttonRun.setText("Run")