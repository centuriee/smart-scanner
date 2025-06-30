import shutil
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

source_folder = r"C:\Users\ACER-PC\Downloads\test_project\source"
destination_folder = r"C:\Users\AC" \
                     r"ER-PC\Downloads\test_project\destination"


class MyEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        for filename in os.listdir(source_folder):
            source_path = os.path.join(source_folder, filename)
            destination_path = os.path.join(destination_folder, filename)

            if os.path.isfile(source_path):  # Ensure it's a file, not a subdirectory
                shutil.move(source_path, destination_path)
                print(f"Moved '{filename}' to '{destination_folder}'.")

    def on_moved(self, event):
        for filename in os.listdir(source_folder):
            source_path = os.path.join(source_folder, filename)
            destination_path = os.path.join(destination_folder, filename)

            if os.path.isfile(source_path):  # Ensure it's a file, not a subdirectory
                shutil.move(source_path, destination_path)
                print(f"Moved '{filename}' to '{destination_folder}'.")


if __name__ == "__main__":
    path_to_watch = r"C:\Users\ACER-PC\Downloads\test_project\source"  # Replace with the actual path
    event_handler = MyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
