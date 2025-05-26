#!/usr/bin/env python3
"""
Simple server startup script without debug reloader issues.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the Flask app
    from app import app
    
    print("🚀 Starting Ristrutturazioni Morcianesi Flask Server...")
    print("📁 Database: " + app.config['DATABASE'])
    print("🌐 Server URL: http://127.0.0.1:5007")
    print("📧 Email configured: " + app.config['EMAIL_HOST'])
    print("🔑 Google OAuth: " + ("✅ Enabled" if app.config.get('GOOGLE_OAUTH_ENABLED') else "❌ Disabled"))
    print("🍎 Apple OAuth: " + ("✅ Enabled" if app.config.get('APPLE_OAUTH_ENABLED') else "❌ Disabled"))
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the server without reloader to avoid termios issues
    app.run(
        debug=False,  # Disable debug to avoid reloader issues
        port=5007,
        host='127.0.0.1',
        threaded=True,
        use_reloader=False  # Explicitly disable reloader
    )
    
except Exception as e:
    print(f"❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()
