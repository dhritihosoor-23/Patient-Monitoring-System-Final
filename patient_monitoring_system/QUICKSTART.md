# Quick Start Guide - Patient Monitoring System

## Installation (5 minutes)

```bash
cd patient_monitoring_system
bash setup.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Download YOLOv8 model
- Create necessary directories

## Run the System

### Option 1: Webcam (Real-time)
```bash
source venv/bin/activate  # Activate virtual environment
python main.py --input 0 --visualize
```

### Option 2: Video File
```bash
python main.py --input path/to/video.mp4 --visualize --output output.mp4
```

### Option 3: Headless (No Display)
```bash
python main.py --input video.mp4 --output output.mp4
```

## Test Installation

```bash
python test_system.py
```

Should show all ✓ PASS for each component.

## Configuration

Edit `config.py` to customize:

```python
# Adjust fall detection sensitivity
FALL_DETECTION_CONFIG = {
    "confidence_threshold": 0.7,  # Lower = more sensitive
    "fall_angle_threshold": 60,   # Degrees from vertical
}

# Change vital signs algorithm
VITAL_SIGNS_CONFIG = {
    "algorithm": "CHROM",  # or "POS", "ICA"
}

# Enable/disable alerts
ALERT_CONFIG = {
    "enable_console": True,
    "enable_file": True,
    "enable_webhook": False,
}
```

## Keyboard Controls

- **q**: Quit application
- **Ctrl+C**: Emergency stop

## Output

- **Logs**: `logs/alerts.log`
- **Video**: Specified by `--output` flag
- **Console**: Real-time alerts

## Troubleshooting

### "Could not open video source"
```bash
# Try different webcam index
python main.py --input 1 --visualize  # or 2, 3, etc.
```

### Low FPS
```python
# In config.py, reduce resolution
VIDEO_CONFIG = {
    "frame_width": 640,
    "frame_height": 480,
}
```

### Missing dependencies
```bash
pip install -r requirements.txt
```

## Docker (Alternative)

```bash
# Build
docker build -t patient-monitoring .

# Run with GPU
docker run --gpus all patient-monitoring

# Run with webcam
docker run --gpus all --device=/dev/video0 patient-monitoring --input 0
```

## System Requirements

**Minimum**:
- Python 3.8+
- 8GB RAM
- CPU: Intel i5 or equivalent

**Recommended**:
- Python 3.10+
- 16GB RAM
- GPU: NVIDIA GTX 1660 or better
- CUDA 11.8+

## Next Steps

1. ✅ Run `test_system.py` to verify installation
2. ✅ Test with webcam: `python main.py --input 0 --visualize`
3. ✅ Review logs in `logs/alerts.log`
4. ✅ Customize `config.py` for your needs
5. ✅ Read `README.md` for detailed documentation

## Support

- **Documentation**: See `README.md`
- **Event Schemas**: See `docs/event_schemas.json`
- **Walkthrough**: See walkthrough artifact

---

**Ready to monitor!** 🎯
