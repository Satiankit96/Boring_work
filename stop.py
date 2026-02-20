#!/usr/bin/env python3
"""
Stop All Services Script
=========================
Stops all running backend and frontend services for the Auth Module.

Usage:
    python stop.py         # Stop all services
    python stop.py --check # Check what's running without stopping
"""

import subprocess
import sys
import os


def get_running_processes():
    """Get list of running Python and Node processes."""
    processes = {"python": [], "node": []}
    
    if os.name == 'nt':  # Windows
        try:
            # Get Python processes
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
                capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if line and 'python' in line.lower():
                    parts = line.strip('"').split('","')
                    if len(parts) >= 2:
                        processes["python"].append({"name": parts[0], "pid": parts[1]})
            
            # Get Node processes
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq node.exe", "/FO", "CSV", "/NH"],
                capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if line and 'node' in line.lower():
                    parts = line.strip('"').split('","')
                    if len(parts) >= 2:
                        processes["node"].append({"name": parts[0], "pid": parts[1]})
        except Exception as e:
            print(f"Error getting process list: {e}")
    else:  # Unix/Linux/Mac
        try:
            result = subprocess.run(
                ["pgrep", "-l", "python|node"],
                capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        if 'python' in parts[1].lower():
                            processes["python"].append({"name": parts[1], "pid": parts[0]})
                        elif 'node' in parts[1].lower():
                            processes["node"].append({"name": parts[1], "pid": parts[0]})
        except Exception:
            pass
    
    return processes


def stop_processes():
    """Stop all Python and Node processes."""
    stopped = {"python": 0, "node": 0}
    
    if os.name == 'nt':  # Windows
        try:
            # Stop Python processes
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "python.exe"],
                capture_output=True, text=True
            )
            if "SUCCESS" in result.stdout:
                stopped["python"] = result.stdout.count("SUCCESS")
        except Exception:
            pass
        
        try:
            # Stop Node processes
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "node.exe"],
                capture_output=True, text=True
            )
            if "SUCCESS" in result.stdout:
                stopped["node"] = result.stdout.count("SUCCESS")
        except Exception:
            pass
    else:  # Unix/Linux/Mac
        try:
            subprocess.run(["pkill", "-f", "python"], capture_output=True)
            stopped["python"] = 1
        except Exception:
            pass
        
        try:
            subprocess.run(["pkill", "-f", "node"], capture_output=True)
            stopped["node"] = 1
        except Exception:
            pass
    
    return stopped


def check_ports():
    """Check if backend/frontend ports are in use."""
    ports = {8000: "Backend", 5173: "Frontend"}
    in_use = []
    
    if os.name == 'nt':
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True
            )
            for port, name in ports.items():
                if f":{port}" in result.stdout and "LISTENING" in result.stdout:
                    in_use.append((port, name))
        except Exception:
            pass
    else:
        try:
            for port, name in ports.items():
                result = subprocess.run(
                    ["lsof", "-i", f":{port}"],
                    capture_output=True, text=True
                )
                if result.stdout.strip():
                    in_use.append((port, name))
        except Exception:
            pass
    
    return in_use


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50)


def main():
    check_only = "--check" in sys.argv
    
    if check_only:
        print_header("Service Status Check")
        
        processes = get_running_processes()
        ports = check_ports()
        
        print("\n📋 Running Processes:")
        if processes["python"]:
            print(f"  Python: {len(processes['python'])} process(es)")
            for p in processes["python"]:
                print(f"    - PID {p['pid']}: {p['name']}")
        else:
            print("  Python: None")
        
        if processes["node"]:
            print(f"  Node.js: {len(processes['node'])} process(es)")
            for p in processes["node"]:
                print(f"    - PID {p['pid']}: {p['name']}")
        else:
            print("  Node.js: None")
        
        print("\n🌐 Ports in Use:")
        if ports:
            for port, name in ports:
                print(f"  - Port {port} ({name}): In use")
        else:
            print("  - No auth module ports in use")
        
    else:
        print_header("Stopping All Services")
        
        print("\n🛑 Stopping processes...")
        stopped = stop_processes()
        
        print(f"  ✓ Python processes stopped: {stopped['python']}")
        print(f"  ✓ Node.js processes stopped: {stopped['node']}")
        
        # Give processes time to release ports
        import time
        time.sleep(1)
        
        # Verify ports are free
        ports = check_ports()
        if ports:
            print("\n⚠️  Some ports may still be in use:")
            for port, name in ports:
                print(f"    - Port {port} ({name})")
        else:
            print("\n✅ All services stopped successfully!")
        
        print("\n💡 To restart, run: python run.py all")


if __name__ == "__main__":
    main()
