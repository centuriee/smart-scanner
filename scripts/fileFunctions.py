import os
import sys
import json


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config.json")

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
    with open(filename, "w", encoding = "utf-8") as f:
        f.write(text)

    print(f"\nSaved Markdown to {filename}") # success

def writeToJSON(data, filename, source_path):
    dir_path = os.path.dirname(source_path)  # get directory of the source file
    full_path = os.path.join(dir_path, filename)  # full path for saving JSON

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data.model_dump(), f, ensure_ascii=False, indent=4)

    print(f"\nSaved JSON to {full_path}") 

def getDefaultPath():
    return os.getcwd()  # Use current directory as default

def loadConfig():
    if not os.path.exists(CONFIG_PATH):
        saveConfig(getDefaultPath(), getDefaultPath())
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading config: {e}")
        # Reset to defaults
        saveConfig(getDefaultPath(), getDefaultPath())
        return {"source": getDefaultPath(), "destination": getDefaultPath()}
    
def saveConfig(source, destination):
    config = {
        "source_path": source.replace("\\", "/"),
        "destination_path": destination.replace("\\", "/")
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def saveSource(source_path):
    config = loadConfig()
    config["source_path"] = source_path
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

def saveDestination(destination_path):
    config = loadConfig()
    config["destination_path"] = destination_path
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)