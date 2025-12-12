#!/usr/bin/env python3
"""
Automated test runner for Patient Monitoring System.
It starts the Flask web server in a background thread, uploads the test video,
starts monitoring, and opens the web UI in the default browser.
"""
import threading
import time
import webbrowser
import requests
import os

# Import the web_server module (Flask app)
import web_server

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5001  # matches quick_test configuration
BASE_URL = f'http://localhost:{SERVER_PORT}'
TEST_VIDEO_PATH = os.path.abspath('test_videos/01.mp4')

def run_server():
    """Run the Flask SocketIO server (blocking)."""
    web_server.socketio.run(
        web_server.app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        debug=False,
        use_reloader=False,
    )

def upload_video():
    """Upload the test video via the /api/upload endpoint."""
    url = f"{BASE_URL}/api/upload"
    with open(TEST_VIDEO_PATH, 'rb') as f:
        files = {'video': (os.path.basename(TEST_VIDEO_PATH), f, 'video/mp4')}
        resp = requests.post(url, files=files)
    resp.raise_for_status()
    data = resp.json()
    print('✅ Video uploaded:', data)
    return data['path']

def start_monitoring(source_path):
    """Start monitoring using the uploaded video file path."""
    url = f"{BASE_URL}/api/start"
    payload = {'source': source_path}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    print('🚀 Monitoring started:', resp.json())

def open_browser():
    """Open the web UI after a short delay."""
    time.sleep(3)  # give server a moment to be ready
    webbrowser.open(f"{BASE_URL}")

if __name__ == '__main__':
    # Start Flask server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait a bit for the server to start
    time.sleep(2)

    # Upload video and start monitoring
    video_path = upload_video()
    start_monitoring(video_path)

    # Open browser for UI
    open_browser()

    # Keep main thread alive while server runs
    try:
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n🛑 Stopping...')
