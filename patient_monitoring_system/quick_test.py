#!/usr/bin/env python3
"""
Quick launcher for testing your video in the web interface.
This script automatically uploads and starts monitoring your test video.
"""

import sys
import time
import webbrowser
import threading
import requests

def open_browser():
    """Open browser after server starts"""
    time.sleep(3)  # Wait for server to start
    print("\n🌐 Opening browser...")
    webbrowser.open('http://localhost:5001')

def main():
    print("="*80)
    print("🏥 Patient Monitoring System - Quick Test")
    print("="*80)
    print()
    print("✓ Test video found: test_videos/01.mp4")
    print("✓ Web dependencies installed")
    print()
    print("Starting web server...")
    print("Server will be available at: http://localhost:5001")
    print()
    print("📋 Instructions:")
    print("  1. Browser will open automatically")
    print("  2. Select 'Upload Video' from dropdown")
    print("  3. Choose 'test_videos/01.mp4'")
    print("  4. Click 'Upload' button")
    print("  5. Click '▶ Start Monitoring'")
    print()
    print("Press Ctrl+C to stop")
    print("="*80)
    print()
    
    # Open browser in background
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Import and run server
    try:
        import web_server
        web_server.socketio.run(
            web_server.app,
            host='0.0.0.0',
            port=5001,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
