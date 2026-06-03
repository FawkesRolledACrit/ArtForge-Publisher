# ArtForge Publisher - Standalone GUI

## Overview

ArtForge Publisher is now available as a standalone Python GUI application that:
- Automatically launches Ollama on startup
- Pulls the required AI model (qwen2.5vl:latest) if not present
- Starts the FastAPI backend
- Provides a PyQt6 GUI for image analysis and content generation

## Features

### Launcher Script (`launcher.py`)
The launcher script handles all the startup tasks:
1. Checks if Ollama is running, starts it if not
2. Pulls the qwen2.5vl:latest model if not present
3. Starts the FastAPI backend
4. Launches the PyQt6 GUI

### PyQt6 GUI (`gui/main.py`)
The GUI provides three main tabs:

#### Upload Tab
- Upload images from your computer
- View list of uploaded images
- Delete images
- Select images for analysis/content generation

#### Analysis Tab
- View AI-generated image analysis
- Edit analysis fields (title, subject, character description, etc.)
- Re-run analysis with Ollama
- Save edited analysis

#### Content Tab
- Generate platform-specific content (ArtStation, X/Twitter, Instagram, Reddit, DeviantArt)
- View and edit generated content
- Content is organized by platform in sub-tabs

## Installation

### Prerequisites
- Python 3.8 or higher
- Ollama installed at `C:\Users\Fawke\AppData\Local\Programs\Ollama\ollama.exe`

### Install Dependencies

#### Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### GUI Dependencies
```bash
pip install -r gui/requirements.txt
```

## Running the Application

### Development Mode

#### Start Backend Separately
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Start GUI Separately
```bash
cd gui
python main.py
```

#### Use Launcher (Recommended)
```bash
python launcher.py
```

The launcher will:
1. Start Ollama if not running
2. Pull the qwen2.5vl model if needed
3. Start the backend
4. Launch the GUI

## Building Standalone Executable

### Build the Executable
```bash
python build.py
```

This will create `dist/ArtForgePublisher.exe` - a single executable that includes:
- Python runtime
- All dependencies
- Backend code
- GUI code
- Launcher functionality

### Distributing the Executable

The executable can be distributed to other users, but they will need:
1. Ollama installed at the same path
2. The qwen2.5vl model (will be pulled automatically on first run)

## Configuration

### Ollama Settings
Edit `backend/app/core/config.py` to change:
- `OLLAMA_ENDPOINT`: Ollama API endpoint (default: http://localhost:11434)
- `OLLAMA_MODEL`: Model to use (default: qwen2.5vl:latest)
- `OLLAMA_TIMEOUT`: Request timeout in seconds (default: 300)

### Launcher Settings
Edit `launcher.py` to change:
- `OLLAMA_PATH`: Path to Ollama executable
- `OLLAMA_MODEL`: Model to pull
- `OLLAMA_HOST`: Ollama API host
- `BACKEND_HOST`: Backend API host

## Troubleshooting

### Ollama Not Starting
- Verify Ollama is installed at the specified path
- Check if another instance of Ollama is already running
- Try starting Ollama manually first

### Model Not Pulling
- Check your internet connection
- Verify Ollama is running
- Try pulling the model manually: `ollama pull qwen2.5vl:latest`

### Backend Not Starting
- Check if port 8000 is already in use
- Verify backend dependencies are installed
- Check backend logs for errors

### GUI Not Starting
- Verify PyQt6 is installed
- Check if backend is running
- Verify the GUI script path in launcher.py

## Architecture

```
ArtForgePublisher/
├── launcher.py          # Main launcher script
├── build.py             # Build script for PyInstaller
├── artforge_publisher.spec  # PyInstaller configuration
├── backend/             # FastAPI backend
│   ├── app/
│   ├── prompts/
│   └── requirements.txt
├── gui/                 # PyQt6 GUI
│   ├── main.py          # Main GUI application
│   └── requirements.txt
└── storage/             # Image and data storage
    ├── images/
    └── thumbnails/
```

## Future Improvements

- [ ] Add settings panel to GUI for configuration
- [ ] Implement content editing and saving
- [ ] Add progress indicators for long-running operations
- [ ] Add image preview in upload tab
- [ ] Implement batch image processing
- [ ] Add export functionality for generated content
- [ ] Create installer with NSIS
- [ ] Add auto-update functionality
