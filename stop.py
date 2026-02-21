#!/usr/bin/env python3
"""
Auth Module v2 - Stop All Services
===================================
Stops Keycloak, Backend, and Frontend.

Usage:
    python stop.py
"""

import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).parent.absolute()
KEYCLOAK_DIR = ROOT_DIR / "keycloak"


def main():
    print("\n" + "=" * 40)
    print("  Stopping Auth Module Services")
    print("=" * 40 + "\n")
    
    # Stop Keycloak
    print("  Stopping Keycloak...")
    subprocess.run("docker-compose down", cwd=KEYCLOAK_DIR, shell=True, capture_output=True)
    
    # Kill processes on ports 8000 and 5173
    print("  Stopping Backend and Frontend...")
    
    if os.name == 'nt':
        # Windows - kill by port
        for port in [8000, 5173]:
            # Find PID using netstat and kill
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True, capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
    else:
        # Unix
        for port in [8000, 5173]:
            subprocess.run(f"lsof -ti:{port} | xargs kill -9 2>/dev/null", shell=True)
    
    print("\n  ✓ All services stopped\n")


if __name__ == "__main__":
    main()
