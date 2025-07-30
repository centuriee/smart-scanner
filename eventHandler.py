import os
from watchdog.events import FileSystemEventHandler

file_stack = [] # note: This could be moved to a shared module if needed
stack_lock = None # will be passed into the handler to ensure thread-safe access

class MyEventHandler(FileSystemEventHandler):
    def __init__(self, source_folder, main_window, stack, lock):
        super().__init__()
        self.source_folder = source_folder          # folder being monitored
        self.main_window = main_window              # reference to the GUI's main window (for terminal printing)
        self.allowed_extensions = {'.pdf', '.img'}  # supported file types
        self.file_stack = stack                     # reference to the shared file stack
        self.stack_lock = lock                      # lock to prevent race conditions on the stack

    def is_valid_file(self, filepath):
        _, ext = os.path.splitext(filepath) # check if the file has a supported extension
        return ext.lower() in self.allowed_extensions

    # this function is triggered when a file is created in the source folder
    def on_created(self, event):
        if not event.is_directory and self.is_valid_file(event.src_path):
            with self.stack_lock:
                self.file_stack.insert(0, event.src_path)
                self.main_window.append_to_terminal(
                    f"New file detected: <i>{os.path.splitext(os.path.basename(event.src_path))[0]}</i>. Added to queue."
                )
        else:
            print("file not supported")

    # triggered when a file is moved/renamed within the source folder
    def on_moved(self, event):
        if not event.is_directory and self.is_valid_file(event.dest_path):
            with self.stack_lock:
                self.file_stack.insert(0, event.dest_path)
                self.main_window.append_to_terminal(
                    f"New file detected: <i>{os.path.splitext(os.path.basename(event.dest_path))[0]}</i>. Added to queue."
                )
        else:
            print("file not supported")
