# UPMin OR Smart Scanner

*developed for the UP Mindanao Office of Research*

**Smart Scanner** is a desktop application that classifies and organizes all documents handled by the Office of Research. This project aims to optimize and streamline the company’s document processing and file organization protocol to enhance overall workflow efficiency.


## Technologies Used

- **Docling** – for document parsing and structure analysis
- **Ollama** – for AI-driven classification (requires qwen3 model)
- **PySide6** – for building the graphical user interface
- **Shutil + Watchdog** – for monitoring folders and handling file movement
- **PyInstaller** – for compiling the project into an executable


## Installation and Dependencies

### 1. Install Ollama and the required model

- Download and install Ollama from [ollama.com](https://ollama.com/).
- After downloading, open a terminal and run the command:

```
ollama pull qwen3
```

> This model is pretty heavy (5.2GB), so it may take a while to download.

### 2. Download the application

- Go to the [Releases](https://github.com/centuriee/smart-scanner/releases) tab and download the latest `.exe` file.

### 3. Run the program!

- Right-click the .exe and **Run as Administrator**

> This ensures required modules are downloaded and created correctly.


## Usage

1. Select the source and destination folders. This is where the program will monitor for new PDF files (source) and move the processed and classified files (destination).

2. Run the program by clicking the `Run` button. The application will begin monitoring the source folder.

3. Documents will automatically be analyzed, classified, and moved to their appropriate folders inside the destination directory. The application supports real-time tracking, so any file added to the source folder will be immediately added to the queue for analysis.

4. When there are no more files in the queue, stop the program by clicking the `Stop` button.


## Modules and Documentation

To learn more about the internal modules and dependencies of the application, check out the [wiki](https://github.com/centuriee/smart-scanner/wiki)!