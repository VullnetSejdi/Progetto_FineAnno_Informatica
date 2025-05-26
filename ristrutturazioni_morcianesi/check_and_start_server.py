#!/usr/bin/env python3
"""
Server status checker and starter for Ristrutturazioni Morcianesi
"""
import requests
import subprocess
import sys
import os
import time

def check_server():
    """Check if server is running on port 5007"""
    try:
        response = requests.get('http://127.0.0.1:5007', timeout=5)
        return True, response.status_code
    except requests.exceptions.RequestException:
        return False, None

def start_server():
    """Start the Flask server"""
    print("🚀 Starting Flask server...")
    try:
        # Start the server in a new process
        process = subprocess.Popen([
            sys.executable, 'app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if it's running
        running, status_code = check_server()
        if running:
            print(f"✅ Server started successfully! Status: {status_code}")
            print("🌐 Access at: http://127.0.0.1:5007")
            return True
        else:
            print("❌ Server failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == '__main__':
    print("🔍 Checking server status...")
    
    running, status_code = check_server()
    
    if running:
        print(f"✅ Server is already running! Status: {status_code}")
        print("🌐 Access at: http://127.0.0.1:5007")
    else:
        print("⚡ Server not running, attempting to start...")
        success = start_server()
        if not success:
            print("💡 Try running manually: python app.py")
            sys.exit(1)
