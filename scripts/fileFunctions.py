import os
import sys
import json

def getSource(parentFolder):
    source = parentFolder + input("Enter PDF name with extension (should be in testDocuments folder): ")

    # error handling
    if os.path.exists(source):
        print("File exists. Converting file...\n")
    else:
        print("File does not exist. Exiting program.\n")
        sys.exit(1)
    
    return source


def getFilename(source, index):
    filename = os.path.splitext(os.path.basename(source))[0]

    if index == 0:
        return filename
    elif index == 1:
        return f"{filename}.json"
    elif index == 2:
        return f"{filename}.md"
    
def writeToMarkdown(text, filename):
    path = f"testDocuments/markdownFiles/{filename}"
    with open(path, "w", encoding = "utf-8") as f:
        f.write(text)

    print(f"\nSaved Markdown to {path}") # success

def writeToJSON(data, filename):
    with open(filename, "w", encoding = "utf-8") as f:
        json.dump(data.model_dump(), f, ensure_ascii = False, indent = 4)

    print(f"\nSaved JSON to {filename}") # success