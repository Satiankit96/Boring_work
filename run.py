#!/usr/bin/env python3
"""
Auth Module - Setup and Run Script
===================================
This script sets up and runs the entire Auth Module application.
It handles:
1. Backend Python environment setup and dependency installation
2. Database initialization
3. Frontend dependency installation
4. Starting both backend and frontend servers

Usage:
    python run.py setup     # First-time setup (install dependencies)
    python run.py backend   # Run backend only
    python run.py frontend  # Run frontend only
    python run.py all       # Run both (default)
    python run.py check     # Check if everything is ready
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = BACKEND_DIR / "data"


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_step(text: str):
    """Print a step indicator."""
    print(f"➜ {text}")


def print_success(text: str):
    """Print a success message."""
    print(f"✓ {text}")


def print_error(text: str):
    """Print an error message."""
    print(f"✗ {text}")


def run_command(cmd: list, cwd: Path = None, check: bool = True) -> bool:
    """Run a command and return success status."""
    try:
        subprocess.run(cmd, cwd=cwd, check=check, shell=True if os.name == 'nt' else False)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        print_error(f"Command not found: {cmd[0]}")
        return False


def check_python():
    """Check if Python 3.10+ is available."""
    print_step("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print_error(f"Python 3.10+ required, found {version.major}.{version.minor}")
        return False


def check_node():
    """Check if Node.js is available."""
    print_step("Checking Node.js...")
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        print_success(f"Node.js {version} detected")
        return True
    except FileNotFoundError:
        print_error("Node.js not found. Please install Node.js 18+")
        return False


def check_npm():
    """Check if npm is available."""
    print_step("Checking npm...")
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, shell=True if os.name == 'nt' else False)
        version = result.stdout.strip()
        print_success(f"npm {version} detected")
        return True
    except FileNotFoundError:
        print_error("npm not found. Please install Node.js/npm")
        return False


def setup_backend():
    """Set up the backend Python environment."""
    print_header("Setting up Backend")
    
    # Create data directory for SQLite
    print_step("Creating data directory...")
    DATA_DIR.mkdir(exist_ok=True)
    print_success("Data directory ready")
    
    # Install Python dependencies
    print_step("Installing Python dependencies...")
    if run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=BACKEND_DIR):
        print_success("Python dependencies installed")
        return True
    else:
        print_error("Failed to install Python dependencies")
        return False


def setup_frontend():
    """Set up the frontend Node.js environment."""
    print_header("Setting up Frontend")
    
    print_step("Installing Node.js dependencies...")
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    if run_command([npm_cmd, "install"], cwd=FRONTEND_DIR):
        print_success("Node.js dependencies installed")
        return True
    else:
        print_error("Failed to install Node.js dependencies")
        return False


def run_backend():
    """Run the backend server."""
    print_header("Starting Backend Server")
    print_step("Starting FastAPI server on http://localhost:8000")
    print("Press Ctrl+C to stop\n")
    
    os.chdir(BACKEND_DIR)
    subprocess.run([sys.executable, "server.py"])


def run_frontend():
    """Run the frontend development server."""
    if not check_node():
        print_error("Cannot start frontend without Node.js")
        print("\n💡 Install Node.js from: https://nodejs.org/")
        print("   Then restart your terminal and run: python run.py all")
        print("\n📌 Backend is still available at: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        return False
    
    print_header("Starting Frontend Server")
    print_step("Starting Vite dev server on http://localhost:5173")
    print("Press Ctrl+C to stop\n")
    
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    subprocess.run([npm_cmd, "run", "dev"], cwd=FRONTEND_DIR, shell=True if os.name == 'nt' else False)
    return True


def run_all():
    """Run both backend and frontend in separate processes."""
    import threading
    
    print_header("Starting Full Application")
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:5173")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop both servers\n")
    
    # Start backend in a thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Give backend time to start
    import time
    time.sleep(2)
    
    # Check if Node.js is available
    if not check_node():
        print_error("Node.js not found - Frontend will not start")
        print("\n💡 Install Node.js from: https://nodejs.org/")
        print("   Then restart your terminal and run: python run.py all")
        print("\n📌 Backend is running at: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop the backend...\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        return
    
    # Run frontend in main thread (so Ctrl+C works)
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\nShutting down...")


def check_status():
    """Check if all dependencies are ready."""
    print_header("System Check")
    
    all_good = True
    
    # Check Python
    if not check_python():
        all_good = False
    
    # Check Node.js
    if not check_node():
        all_good = False
    
    # Check npm
    if not check_npm():
        all_good = False
    
    # Check backend dependencies
    print_step("Checking backend dependencies...")
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print_success("Backend dependencies installed")
    except ImportError as e:
        print_error(f"Missing backend dependency: {e.name}")
        all_good = False
    
    # Check frontend node_modules
    print_step("Checking frontend dependencies...")
    if (FRONTEND_DIR / "node_modules").exists():
        print_success("Frontend dependencies installed")
    else:
        print_error("Frontend dependencies not installed (run: python run.py setup)")
        all_good = False
    
    # Summary
    print()
    if all_good:
        print_success("All checks passed! Run 'python run.py all' to start.")
    else:
        print_error("Some checks failed. Run 'python run.py setup' first.")
    
    return all_good


def print_usage():
    """Print usage information."""
    print(__doc__)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        command = "all"
    else:
        command = sys.argv[1].lower()
    
    if command == "setup":
        if not check_python():
            sys.exit(1)
        if not check_node():
            sys.exit(1)
        if not check_npm():
            sys.exit(1)
        
        if setup_backend() and setup_frontend():
            print_header("Setup Complete!")
            print("Run 'python run.py all' to start the application.")
            print("\nEndpoints:")
            print("  • Frontend: http://localhost:5173")
            print("  • Backend:  http://localhost:8000")
            print("  • API Docs: http://localhost:8000/docs")
        else:
            sys.exit(1)
    
    elif command == "backend":
        run_backend()
    
    elif command == "frontend":
        run_frontend()
    
    elif command == "all":
        run_all()
    
    elif command == "check":
        if not check_status():
            sys.exit(1)
    
    elif command in ["help", "-h", "--help"]:
        print_usage()
    
    else:
        print_error(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
