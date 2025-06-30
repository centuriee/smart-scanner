import shutil
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from docling.document_converter import DocumentConverter

source_folder = "C:\\Users\ACER-PC\Downloads\\test_project\source"
destination_folder = "C:\Users\ACER-PC\Downloads\\test_project\destination"


class MyEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        for filename in os.listdir(source_folder):
            source_path = os.path.join(source_folder, filename)
            destination_path = os.path.join(destination_folder, filename)

            if os.path.isfile(source_path):  # Ensure it's a file, not a subdirectory
                shutil.move(source_path, destination_path)
                print(f"Moved '{filename}' to '{destination_folder}'.")

    def on_moved(self, event):
        source = "testDocuments/Malaque III - Approve_Application.pdf"
        # print("Source: " + source)
        converter = DocumentConverter()
        result = converter.convert(source)

        # name for generated files based on pdf file name
        filename = os.path.splitext(os.path.basename(source))[0]
        jsonFilename = f"{filename}.json"
        mdFilename = f"{filename}.md"

        """
        # JSON
        resultDict = result.document.export_to_dict()

        # write to json file
        with open(jsonFilename, "w", encoding = "utf-8") as f:
            json.dump(resultDict, f, ensure_ascii = False, indent = 4)

        print(f"\nSaved JSON to {jsonFilename}") # success
        """

        # MARKDOWN
        doc = result.document.export_to_markdown()

        # write to doc file
        with open(mdFilename, "w", encoding = "utf-8") as f:
            f.write(doc)

        print(f"\nSaved Markdown to {mdFilename}") # success


if __name__ == "__main__":
    path_to_watch = "C:\\Users\ACER-PC\Downloads\\test_project\source"  # Replace with the actual path
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
