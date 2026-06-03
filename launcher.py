"""Launcher script for ArtForge Publisher.

This script:
1. Starts Ollama if not running
2. Pulls the required model if not present
3. Starts the FastAPI backend
4. Launches the PyQt GUI
"""

import subprocess
import sys
import time
import requests
import os
from pathlib import Path

# Configuration
OLLAMA_PATH = r"C:\Users\Fawke\AppData\Local\Programs\Ollama\ollama.exe"
OLLAMA_MODEL = "qwen2.5vl:latest"
OLLAMA_HOST = "http://localhost:11434"
BACKEND_HOST = "http://localhost:8000"
BACKEND_DIR = Path(__file__).parent / "backend"


def is_ollama_running():
    """Check if Ollama is running."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        if response.status_code == 200:
            # Also check if ollama.exe process is running
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq ollama.exe"],
                    capture_output=True,
                    text=True
                )
                return "ollama.exe" in result.stdout
            except:
                # If process check fails, rely on API check
                return True
        return False
    except:
        return False


def start_ollama():
    """Start Ollama in the background."""
    print("Starting Ollama...")
    try:
        # Start Ollama without hiding the window so it can initialize properly
        subprocess.Popen(
            [OLLAMA_PATH, "serve"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        # Wait for Ollama to start and verify it's actually responding
        print("Waiting for Ollama to start...")
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            try:
                # Verify API is actually responding
                response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
                if response.status_code == 200:
                    print("Ollama started successfully and is responding!")
                    return True
            except:
                pass
        print("Ollama process started but API is not responding")
        return False
    except Exception as e:
        print(f"Failed to start Ollama: {e}")
        return False


def pull_model():
    """Pull the required model if not present."""
    print(f"Checking if {OLLAMA_MODEL} is available...")
    
    # First verify Ollama is actually running
    if not is_ollama_running():
        print("Ollama is not running. Cannot check/pull model.")
        return False
    
    try:
        # Check if model exists
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            
            if OLLAMA_MODEL in model_names:
                print(f"Model {OLLAMA_MODEL} already available")
                return True
        
        # Pull the model
        print(f"Pulling {OLLAMA_MODEL}... (this may take a while)")
        result = subprocess.run(
            [OLLAMA_PATH, "pull", OLLAMA_MODEL],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        if result.returncode == 0:
            print(f"Successfully pulled {OLLAMA_MODEL}")
            return True
        else:
            print(f"Failed to pull model: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error pulling model: {e}")
        return False


def is_backend_running():
    """Check if backend is already running."""
    try:
        response = requests.get(f"{BACKEND_HOST}/api/v1/images", timeout=2)
        return response.status_code == 200
    except:
        return False


def kill_existing_backend():
    """Kill existing backend process if running."""
    try:
        # Find and kill Python processes using port 8000
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True
        )
        
        for line in result.stdout.split('\n'):
            if ':8000' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                        print(f"Killed existing backend process: {pid}")
                        time.sleep(1)
                    except:
                        pass
    except Exception as e:
        print(f"Failed to kill existing backend: {e}")


def start_backend():
    """Start the FastAPI backend."""
    print("Starting backend...")
    try:
        # Check if backend is already running
        if is_backend_running():
            print("Backend is already running. Killing existing process...")
            kill_existing_backend()
            time.sleep(2)  # Wait for port to be released
        
        print(f"Backend directory: {BACKEND_DIR}")
        print(f"Python executable: {sys.executable}")
        print(f"Command: {sys.executable} -m uvicorn app.main:app --host 0.0.0.0 --port", "8000")
        
        # Verify Ollama is running before starting backend
        if not is_ollama_running():
            print("ERROR: Ollama is not running. Backend requires Ollama to function.")
            print("Please ensure Ollama is started before running the launcher.")
            return False
        
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=BACKEND_DIR
        )
        print(f"Backend process started with PID: {process.pid}")
        
        # Wait for backend to start
        print("Waiting for backend to start...")
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            # Check if process is still running
            if process.poll() is not None:
                print(f"ERROR: Backend process exited with code {process.returncode}")
                print("Backend failed to start. Check the error above.")
                return False
            
            try:
                print(f"Attempt {i+1}/30: Checking {BACKEND_HOST}/api/v1/images")
                response = requests.get(f"{BACKEND_HOST}/api/v1/images", timeout=2)
                print(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    print("Backend started successfully!")
                    return True
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {e}")
            except requests.exceptions.Timeout as e:
                print(f"Timeout error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")
        print("Backend failed to start within timeout")
        return False
    except Exception as e:
        print(f"Failed to start backend: {e}")
        return False


def launch_gui():
    """Launch the PyQt GUI."""
    print("Launching GUI...")
    try:
        gui_path = Path(__file__).parent / "gui" / "main.py"
        if gui_path.exists():
            # Launch GUI and capture output to file
            log_file = Path(__file__).parent / "gui_error.log"
            with open(log_file, 'w') as f:
                process = subprocess.Popen(
                    [sys.executable, str(gui_path)],
                    stdout=f,
                    stderr=subprocess.STDOUT
                )
            print(f"GUI launched with PID: {process.pid}")
            print(f"Check {log_file} for any errors")
            return True
        else:
            print("GUI not found. Please create the GUI first.")
            return False
    except Exception as e:
        print(f"Failed to launch GUI: {e}")
        return False


def main():
    """Main launcher function."""
    print("=" * 50)
    print("ArtForge Publisher Launcher")
    print("=" * 50)
    
    # Step 1: Start Ollama
    if not is_ollama_running():
        if not start_ollama():
            print("Failed to start Ollama. Exiting.")
            sys.exit(1)
    else:
        print("Ollama is already running")
    
    # Step 2: Pull model
    if not pull_model():
        print("Failed to pull model. Exiting.")
        sys.exit(1)
    
    # Step 3: Start backend
    if not start_backend():
        print("Failed to start backend. Exiting.")
        sys.exit(1)
    
    # Step 4: Launch GUI
    if not launch_gui():
        print("Failed to launch GUI. Exiting.")
        sys.exit(1)
    
    print("\nAll services started successfully!")
    print("Press Ctrl+C to stop all services")


if __name__ == "__main__":
    try:
        main()
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
