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
from docling.document_converter import DocumentConverter

class MyEventHandler(FileSystemEventHandler):
    def __init__(self, source_folder, destination_folder):
        super().__init__()
        self.source_folder = source_folder
        self.destination_folder = destination_folder

    def on_created(self, event):
        for filename in os.listdir(self.source_folder):
            source_path = os.path.join(self.source_folder, filename)
            destination_path = os.path.join(self.destination_folder, filename)

            if os.path.isfile(source_path):
                shutil.move(source_path, destination_path)
                print(f"Moved '{filename}' to '{self.destination_folder}'.")

    def on_moved(self, event):
        source = "testDocuments/Malaque III - Approve_Application.pdf"
        converter = DocumentConverter()
        result = converter.convert(source)

        filename = os.path.splitext(os.path.basename(source))[0]
        mdFilename = f"{filename}.md"

        doc = result.document.export_to_markdown()
        with open(mdFilename, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"\nSaved Markdown to {mdFilename}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Directory Chooser + File Monitor")
        self.default_dir = os.path.dirname(os.path.abspath(__file__))
        self.selected_dir = self.default_dir
        self.destination_dir = r"C:\Users\ACER-PC\Downloads\test_project\destination"

        self.observer = None
        self.observer_thread = None
        self.monitoring = False

        # Create UI
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
        selected = QFileDialog.getExistingDirectory(
            self, "Select Directory", self.selected_dir
        )
        if selected:
            self.selected_dir = selected
            self.label.setText(f"Selected Directory: {selected}")
        else:
            self.label.setText("No directory selected.")

    def the_button_was_clicked(self):
        print(f"Current selected directory: {self.selected_dir}")

    def toggle_monitoring(self):
        if not self.monitoring:
            self.start_observer()
        else:
            self.stop_observer()

    def start_observer(self):
        print("Starting file observer...")
        self.monitoring = True
        self.buttonRun.setText("Stop")

        def run_observer():
            event_handler = MyEventHandler(
                source_folder=self.selected_dir,
                destination_folder=self.destination_dir
            )
            self.observer = Observer()
            self.observer.schedule(event_handler, self.selected_dir, recursive=True)
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

    def stop_observer(self):
        print("Stopping file observer...")
        self.monitoring = False
        self.buttonRun.setText("Run")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
