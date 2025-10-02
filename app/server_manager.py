#!/usr/bin/env python3
"""
Server Management Script for Instagram Downloader API.
Provides commands for starting, stopping, restarting, and checking server status.
"""

import subprocess
import sys
import os
import signal
import time
import json
from pathlib import Path
from typing import Optional, List

class ServerManager:
    """Manages the Instagram Downloader API server."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.pid_file = self.project_root / "server.pid"
        self.log_file = self.project_root / "logs" / "app.log"
        self.port = 8000
        
    def _get_server_pid(self) -> Optional[int]:
        """Get the server process ID if running."""
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process is still running
                try:
                    os.kill(pid, 0)  # Check if process exists
                    return pid
                except (OSError, ProcessLookupError):
                    # Process doesn't exist, remove stale PID file
                    self.pid_file.unlink(missing_ok=True)
                    return None
            except (ValueError, FileNotFoundError):
                return None
        return None
    
    def _save_pid(self, pid: int):
        """Save server process ID to file."""
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))
    
    def _remove_pid(self):
        """Remove PID file."""
        self.pid_file.unlink(missing_ok=True)
    
    def _is_port_in_use(self) -> bool:
        """Check if port 8000 is in use."""
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{self.port}"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            return bool(result.stdout.strip())
        except FileNotFoundError:
            # lsof not available, try netstat
            try:
                result = subprocess.run(
                    ["netstat", "-an"], 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                return f":{self.port}" in result.stdout
            except FileNotFoundError:
                return False
    
    def start(self):
        """Start the server."""
        print("🚀 Starting Instagram Downloader API Server...")
        
        # Check if server is already running
        if self._get_server_pid():
            print("⚠️ Server is already running!")
            return False
        
        if self._is_port_in_use():
            print(f"❌ Port {self.port} is already in use!")
            return False
        
        try:
            # Start server in background
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "app.main:app", 
                "--host", "0.0.0.0", 
                "--port", str(self.port),
                "--reload"
            ], cwd=self.project_root)
            
            # Save PID
            self._save_pid(process.pid)
            
            # Wait a moment to check if server started successfully
            time.sleep(2)
            
            if process.poll() is None:
                print(f"✅ Server started successfully on port {self.port}")
                print(f"📝 PID: {process.pid}")
                print(f"🌐 URL: http://localhost:{self.port}")
                return True
            else:
                print("❌ Server failed to start")
                self._remove_pid()
                return False
                
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            self._remove_pid()
            return False
    
    def stop(self):
        """Stop the server."""
        print("🛑 Stopping Instagram Downloader API Server...")
        
        pid = self._get_server_pid()
        if not pid:
            print("ℹ️ Server is not running")
            return True
        
        try:
            # Try graceful shutdown first
            print(f"📡 Sending SIGTERM to process {pid}...")
            os.kill(pid, signal.SIGTERM)
            
            # Wait for graceful shutdown
            for i in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                try:
                    os.kill(pid, 0)  # Check if process still exists
                except (OSError, ProcessLookupError):
                    print("✅ Server stopped gracefully")
                    self._remove_pid()
                    return True
            
            # Force kill if graceful shutdown failed
            print("⚠️ Graceful shutdown failed, force killing...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
            
            # Check if killed
            try:
                os.kill(pid, 0)
                print("❌ Failed to stop server")
                return False
            except (OSError, ProcessLookupError):
                print("✅ Server force stopped")
                self._remove_pid()
                return True
                
        except Exception as e:
            print(f"❌ Error stopping server: {e}")
            return False
    
    def restart(self):
        """Restart the server."""
        print("🔄 Restarting Instagram Downloader API Server...")
        
        # Stop server
        if not self.stop():
            print("⚠️ Failed to stop server, attempting to start anyway...")
        
        # Wait a moment
        time.sleep(2)
        
        # Start server
        return self.start()
    
    def status(self):
        """Check server status."""
        print("📊 Instagram Downloader API Server Status")
        print("=" * 50)
        
        pid = self._get_server_pid()
        port_in_use = self._is_port_in_use()
        
        if pid:
            print(f"✅ Server is RUNNING")
            print(f"📝 PID: {pid}")
            print(f"🌐 Port: {self.port}")
            print(f"🌐 URL: http://localhost:{self.port}")
            
            # Check if port is actually in use
            if port_in_use:
                print("✅ Port is active")
            else:
                print("⚠️ Port is not active (server may be starting up)")
        else:
            print("❌ Server is NOT running")
            if port_in_use:
                print(f"⚠️ Port {self.port} is in use by another process")
            else:
                print(f"✅ Port {self.port} is available")
        
        # Check log file
        if self.log_file.exists():
            print(f"📄 Log file: {self.log_file}")
            try:
                stat = self.log_file.stat()
                print(f"📅 Last modified: {time.ctime(stat.st_mtime)}")
            except OSError:
                pass
        else:
            print("📄 No log file found")
        
        print("=" * 50)
        return pid is not None

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python server_manager.py <command>")
        print("Commands: start, stop, restart, status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    manager = ServerManager()
    
    if command == "start":
        success = manager.start()
        sys.exit(0 if success else 1)
    elif command == "stop":
        success = manager.stop()
        sys.exit(0 if success else 1)
    elif command == "restart":
        success = manager.restart()
        sys.exit(0 if success else 1)
    elif command == "status":
        success = manager.status()
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: start, stop, restart, status")
        sys.exit(1)

if __name__ == "__main__":
    main()
