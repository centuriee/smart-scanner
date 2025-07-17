import os
from watchdog.events import FileSystemEventHandler

file_stack = []  # Re-import or move to a shared location if needed
stack_lock = None  # Will be passed in __init__

class MyEventHandler(FileSystemEventHandler):
    def __init__(self, source_folder, main_window, stack, lock):
        super().__init__()
        self.source_folder = source_folder
        self.main_window = main_window
        self.allowed_extensions = {'.pdf', '.img'}
        self.file_stack = stack
        self.stack_lock = lock

    def is_valid_file(self, filepath):
        _, ext = os.path.splitext(filepath)
        return ext.lower() in self.allowed_extensions

    def on_created(self, event):
        if not event.is_directory and self.is_valid_file(event.src_path):
            with self.stack_lock:
                self.file_stack.insert(0, event.src_path)
                self.main_window.append_to_terminal(
                    f"New file detected: <i>{os.path.splitext(os.path.basename(event.src_path))[0]}</i>. Added to queue."
                )
        else:
            print("file not supported")

    def on_moved(self, event):
        if not event.is_directory and self.is_valid_file(event.dest_path):
            with self.stack_lock:
                self.file_stack.insert(0, event.dest_path)
                self.main_window.append_to_terminal(
                    f"New file detected: <i>{os.path.splitext(os.path.basename(event.dest_path))[0]}</i>. Added to queue."
                )
        else:
            print("file not supported")
