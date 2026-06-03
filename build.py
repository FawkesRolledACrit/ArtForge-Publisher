"""Build script for creating the standalone executable."""

import subprocess
import sys
import os

def build_exe():
    """Build the executable using PyInstaller."""
    print("Building ArtForge Publisher executable...")
    
    # Install PyInstaller if not already installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build the executable
    print("Running PyInstaller...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "PyInstaller",
            "artforge_publisher.spec",
            "--clean",
            "--noconfirm"
        ])
        print("\nBuild complete!")
        print("Executable location: dist/ArtForgePublisher.exe")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code: {e.returncode}")
        print("Please check the error messages above.")
        return False
    except Exception as e:
        print(f"\nBuild failed with exception: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = build_exe()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
