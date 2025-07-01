import sys
import os
import shutil
import time
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QPushButton, QLabel, QFileDialog
)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
        self.default_dir = os.path.dirname(os.path.abspath(__file__))
        self.selected_dir = self.default_dir
        self.destination_dir = r"C:\Users\ACER-PC\Downloads\test_project\destination"

        self.observer = None
        self.observer_thread = None
        self.mover_thread = None
        self.monitoring = False

        # UI Setup
        central_widget = QWidget()
        layout = QVBoxLayout()

        self.label = QLabel(f"Default Directory: {self.default_dir}")
        self.buttonDir = QPushButton("Browse for Directory")
        self.buttonDir.clicked.connect(self.choose_directory)

        self.buttonRun = QPushButton("Run")
        self.buttonRun.clicked.connect(self.toggle_monitoring)

        layout.addWidget(self.label)
        layout.addWidget(self.buttonDir)
        layout.addWidget(self.buttonRun)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def choose_directory(self):
        selected = QFileDialog.getExistingDirectory(self, "Select Directory", self.selected_dir)
        if selected:
            self.selected_dir = selected
            self.label.setText(f"Selected Directory: {selected}")
        else:
            self.label.setText("No directory selected.")

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
        for filename in os.listdir(self.selected_dir):
            full_path = os.path.join(self.selected_dir, filename)
            if os.path.isfile(full_path):
                with stack_lock:
                    file_stack.append(full_path)  # Add to top of stack
                    print(f"Initial scan added: {full_path}")

        # Start watchdog observer
        def run_observer():
            event_handler = MyEventHandler(self.selected_dir)
            self.observer = Observer()
            self.observer.schedule(event_handler, self.selected_dir, recursive=False)
            self.observer.start()
            print(f"Watching folder: {self.selected_dir}")
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
                        filename = os.path.basename(filepath)
                        destination_path = os.path.join(self.destination_dir, filename)
                        try:
                            shutil.move(filepath, destination_path)
                            print(f"Moved: {filename} → {self.destination_dir}")
                        except Exception as e:
                            print(f"Error moving {filename}: {e}")
                else:
                    time.sleep(1)  # Avoid busy waiting

        self.mover_thread = threading.Thread(target=move_files, daemon=True)
        self.mover_thread.start()

    def stop_observer(self):
        print("Stopping file observer...")
        self.monitoring = False
        self.buttonRun.setText("Run")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
