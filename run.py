#!/usr/bin/env python3
"""
Auth Module v2 - Run Script
============================
Starts all services: Keycloak (Docker), Backend (FastAPI), Frontend (Vite)

Usage:
    python run.py              # Start everything (Keycloak mode)
    python run.py --local      # Start without Keycloak (local auth)
    python run.py --stop       # Stop all services
"""

import os
import sys
import subprocess
import shutil
import time
import signal
from pathlib import Path

ROOT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
KEYCLOAK_DIR = ROOT_DIR / "keycloak"

# Store background processes
processes = []


def print_box(text: str):
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50)


def run_cmd(cmd: str, cwd: Path = None, background: bool = False, env: dict = None):
    """Run a command."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    if background:
        if os.name == 'nt':
            proc = subprocess.Popen(
                cmd, cwd=cwd, shell=True, env=full_env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            proc = subprocess.Popen(
                cmd, cwd=cwd, shell=True, env=full_env,
                preexec_fn=os.setpgrp
            )
        processes.append(proc)
        return proc
    else:
        return subprocess.run(cmd, cwd=cwd, shell=True, env=full_env)


def check_docker():
    """Check if Docker is running."""
    try:
        result = subprocess.run(
            "docker info", shell=True, capture_output=True, timeout=10
        )
        return result.returncode == 0
    except:
        return False


def check_port(port: int) -> bool:
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def wait_for_service(url: str, name: str, timeout: int = 60):
    """Wait for a service to become available."""
    import urllib.request
    print(f"  Waiting for {name}...", end="", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            print(" ✓")
            return True
        except:
            print(".", end="", flush=True)
            time.sleep(2)
    print(" timeout!")
    return False


def install_deps():
    """Install dependencies if needed."""
    # Backend
    if not (BACKEND_DIR / "app").exists():
        print("ERROR: backend/app folder not found")
        sys.exit(1)
    
    print("  Installing backend dependencies...")
    run_cmd("pip install -r requirements.txt -q", cwd=BACKEND_DIR)
    
    # Frontend
    if not (FRONTEND_DIR / "node_modules").exists():
        print("  Installing frontend dependencies...")
        run_cmd("npm install", cwd=FRONTEND_DIR)


def start_keycloak():
    """Start Keycloak via Docker Compose."""
    print_box("Starting Keycloak (Docker)")
    
    if not check_docker():
        print("  ERROR: Docker is not running!")
        print("  Please start Docker Desktop and try again.")
        print("  Or use: python run.py --local")
        sys.exit(1)
    
    run_cmd("docker-compose up -d", cwd=KEYCLOAK_DIR)
    
    # Wait for Keycloak to be ready
    wait_for_service("http://localhost:8080/health/ready", "Keycloak", timeout=90)


def start_backend(auth_mode: str = "keycloak"):
    """Start the FastAPI backend."""
    print_box(f"Starting Backend (AUTH_MODE={auth_mode})")
    
    env = {"AUTH_MODE": auth_mode}
    run_cmd("python -m uvicorn app.main:app --reload --port 8000", 
            cwd=BACKEND_DIR, background=True, env=env)
    
    time.sleep(2)
    wait_for_service("http://localhost:8000/health", "Backend")


def start_frontend():
    """Start the Vite frontend."""
    print_box("Starting Frontend")
    
    run_cmd("npm run dev", cwd=FRONTEND_DIR, background=True)
    
    time.sleep(2)
    wait_for_service("http://localhost:5173", "Frontend")


def stop_all():
    """Stop all services."""
    print_box("Stopping All Services")
    
    # Stop Keycloak
    print("  Stopping Keycloak...")
    run_cmd("docker-compose down", cwd=KEYCLOAK_DIR)
    
    # Kill processes on ports
    if os.name == 'nt':
        # Windows
        for port in [8000, 5173]:
            subprocess.run(
                f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :{port}\') do taskkill /F /PID %a',
                shell=True, capture_output=True
            )
    else:
        # Unix
        for port in [8000, 5173]:
            subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, capture_output=True)
    
    print("  ✓ All services stopped")


def main():
    args = sys.argv[1:]
    
    # Handle stop command
    if "--stop" in args or "stop" in args:
        stop_all()
        return
    
    # Determine auth mode
    local_mode = "--local" in args or "local" in args
    auth_mode = "local" if local_mode else "keycloak"
    
    print_box("Auth Module v2")
    print(f"  Mode: {auth_mode.upper()}")
    
    # Install dependencies
    install_deps()
    
    # Start services
    if not local_mode:
        start_keycloak()
    
    start_backend(auth_mode)
    start_frontend()
    
    # Print summary
    print_box("All Services Running!")
    print()
    print("  Frontend:  http://localhost:5173")
    print("  Backend:   http://localhost:8000")
    print("  API Docs:  http://localhost:8000/docs")
    if not local_mode:
        print("  Keycloak:  http://localhost:8080/admin (admin/admin)")
    print()
    print("  Test Users (Keycloak mode):")
    print("    testuser@example.com / TestPass123!")
    print("    admin@example.com / AdminPass123!")
    print()
    print("  Press Ctrl+C to stop all services")
    print()
    
    # Keep running until Ctrl+C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        stop_all()


if __name__ == "__main__":
    main()
