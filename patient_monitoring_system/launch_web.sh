#!/bin/bash

# Quick launch script for web interface
# This script starts the web server and opens the browser

echo "=========================================="
echo "Patient Monitoring System - Web Interface"
echo "=========================================="
echo ""

# Check if dependencies are installed
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing web dependencies..."
    pip install Flask Flask-SocketIO Flask-CORS python-socketio eventlet
fi

echo "✓ Dependencies ready"
echo ""

# Start the web server
echo "Starting web server..."
echo "Server will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 web_server.py
