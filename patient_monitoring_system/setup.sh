#!/bin/bash

# Setup script for Patient Monitoring System
# Downloads models and prepares environment

echo "========================================="
echo "Patient Monitoring System - Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "✓ Virtual environment created"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Download YOLOv8 model
echo "Downloading YOLOv8 model..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" 2>/dev/null
echo "✓ YOLOv8 model downloaded"
echo ""

# Create directories
echo "Creating directories..."
mkdir -p logs
mkdir -p output
mkdir -p models/weights
mkdir -p docs
echo "✓ Directories created"
echo ""

echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To run the system:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run with webcam: python main.py --input 0 --visualize"
echo "  3. Run with video: python main.py --input video.mp4 --visualize"
echo ""
echo "For more information, see README.md"
echo ""
