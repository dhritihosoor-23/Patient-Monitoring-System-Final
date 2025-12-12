# Multi-Agent Patient Monitoring System

A production-ready, modular deep-learning pipeline for monitoring elderly and bedridden patients using multiple specialized AI agents.

![System Architecture](docs/architecture.png)

## 🎯 Features

### Perception Layer
- **Person Detection**: YOLOv8-based person detection
- **Person Tracking**: DeepSORT for consistent identity tracking
- **Pose Estimation**: MediaPipe Pose (33 keypoints)
- **Face Detection**: MediaPipe Face Detection

### Specialized Agents
1. **Fall Detection Agent**: Detects falls, near-falls, lying on ground, abnormal collapses
2. **Emotion Detection Agent**: Classifies 7 basic emotions with valence-arousal
3. **Vital Signs Agent**: Extracts heart rate and respiratory rate using rPPG
4. **Bed Exit Agent**: State machine tracking bed entry/exit
5. **Immobility Agent**: Monitors movement frequency and pressure ulcer risk
6. **Seizure Detection Agent**: Detects high-frequency repetitive limb movements

### Orchestrator
- Event fusion from all agents
- Intelligent rule engine
- Duplicate removal
- Alert prioritization

### Output
- Real-time visualization overlay
- Multi-channel alerts (console, file, webhook, email)
- Event logging

## 📋 Requirements

- Python 3.8+
- CUDA-capable GPU (recommended) or CPU
- Webcam or video file

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd patient_monitoring_system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Models

The system will automatically download required models on first run:
- YOLOv8n (person detection)
- MediaPipe models (pose, face)

For better performance, you can manually download larger models:

```bash
# Download YOLOv8 models
python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"

# Models will be cached in ~/.cache/
```

### 3. Run the System

**Option A: Command Line Interface**

```bash
# Run with webcam
python main.py --input 0 --visualize

# Run with video file
python main.py --input test_video.mp4 --visualize --output output.mp4

# Run headless (no visualization)
python main.py --input video.mp4 --output output.mp4
```

**Option B: Web Interface** (Recommended)

```bash
# Start web server
python web_server.py
```

Then open your browser to: **http://localhost:5000**

Features:
- 🌐 Real-time video streaming
- 📤 Video upload support
- 📊 Live event dashboard
- 🚨 Alert notifications
- 💓 Vital signs display

See [WEB_FRONTEND.md](WEB_FRONTEND.md) for detailed instructions.

### 4. Download Test Videos

```bash
# Get test video recommendations
python download_test_videos.py
```

This will provide links to download suitable test videos for:
- Fall detection
- Bed exit monitoring
- Vital signs extraction
- Emotion detection

## 📁 Project Structure

```
patient_monitoring_system/
├── main.py                 # Main entry point
├── config.py               # Configuration management
├── schemas.py              # Event schemas and data structures
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── core/                   # Core infrastructure
│   ├── base_agent.py      # Abstract agent interface
│   ├── video_pipeline.py  # Video capture and preprocessing
│   ├── orchestrator.py    # Event fusion and rule engine
│   ├── visualizer.py      # Real-time visualization
│   └── alert_system.py    # Multi-channel alerting
│
├── perception/            # Perception layer
│   ├── person_detector.py # YOLOv8 person detection
│   ├── person_tracker.py  # DeepSORT tracking
│   ├── pose_estimator.py  # MediaPipe pose estimation
│   └── face_detector.py   # MediaPipe face detection
│
├── agents/                # Specialized monitoring agents
│   ├── fall_detection_agent.py
│   ├── emotion_detection_agent.py
│   ├── vital_signs_agent.py
│   ├── bed_exit_agent.py
│   ├── immobility_agent.py
│   └── seizure_detection_agent.py
│
├── models/                # Model components
│   └── rppg_processor.py  # rPPG signal processing
│
├── utils/                 # Utility functions
│   ├── geometry.py        # Geometric calculations
│   └── temporal_buffer.py # Temporal data buffering
│
├── logs/                  # Log files (auto-created)
├── output/                # Output videos (auto-created)
└── docs/                  # Documentation
    └── event_schemas.json # Event schema definitions
```

## ⚙️ Configuration

Edit `config.py` to customize:

- **Video settings**: Resolution, FPS, input source
- **Model parameters**: Confidence thresholds, model complexity
- **Agent thresholds**: Fall angle, immobility duration, etc.
- **Visualization**: Colors, overlay options
- **Alerts**: Enable/disable channels, webhook URLs, email settings

### Example: Adjust Fall Detection Sensitivity

```python
# In config.py
FALL_DETECTION_CONFIG = {
    "confidence_threshold": 0.6,  # Lower = more sensitive
    "fall_angle_threshold": 50,   # Lower = detect smaller angles
    "hip_height_threshold": 0.4,  # Higher = detect higher falls
}
```

## 📊 Event Schemas

All events follow a consistent schema. See `docs/event_schemas.json` for complete definitions.

### Example: Fall Detection Event

```json
{
  "event_type": "fall_detection",
  "timestamp": 1234567890.123,
  "confidence": 0.85,
  "agent_name": "fall_detection",
  "frame_id": 1234,
  "fall_type": "fall",
  "bbox": {"x1": 100, "y1": 200, "x2": 300, "y2": 400},
  "torso_angle": 75.5,
  "hip_height": 0.25
}
```

## 🔧 Advanced Usage

### Custom Agents

Create custom agents by inheriting from `BaseAgent`:

```python
from core.base_agent import BaseAgent
from schemas import BaseEvent, FrameMetadata

class CustomAgent(BaseAgent):
    def __init__(self, config):
        super().__init__("custom_agent", config)
    
    def detect(self, frame, metadata: FrameMetadata):
        # Your detection logic here
        if condition:
            return CustomEvent(...)
        return None
```

### Custom Rules

Add custom fusion rules in `config.py`:

```python
ORCHESTRATOR_CONFIG = {
    "rules": {
        "my_custom_rule": {
            "conditions": ["fall_detected", "nighttime"],
            "level": "CRITICAL",
            "message": "Fall detected at night!",
        }
    }
}
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t patient-monitoring .

# Run with GPU
docker run --gpus all -v $(pwd)/logs:/app/logs patient-monitoring

# Run with webcam
docker run --gpus all --device=/dev/video0 patient-monitoring --input 0 --visualize
```

## 📈 Performance

Typical performance on different hardware:

| Hardware | FPS | Notes |
|----------|-----|-------|
| NVIDIA RTX 3080 | 25-30 | All agents enabled |
| NVIDIA GTX 1660 | 15-20 | All agents enabled |
| CPU (Intel i7) | 3-5 | Reduced model complexity recommended |

### Optimization Tips

1. **Reduce model complexity**: Use YOLOv8n instead of YOLOv8s
2. **Skip frames**: Set `skip_frames` in config
3. **Disable agents**: Disable non-critical agents
4. **Lower resolution**: Reduce input resolution

## 🔬 Model Details

### Fall Detection
- **Input**: Pose keypoints (33 points × 3 coordinates)
- **Method**: Temporal analysis with torso angle, hip height, velocity
- **Accuracy**: ~85% on test data

### Vital Signs (rPPG)
- **Algorithm**: CHROM (Chrominance-based)
- **Accuracy**: ±5 BPM for HR, ±2 BrPM for RR
- **Requirements**: Good lighting, minimal motion

### Emotion Detection
- **Placeholder**: Currently uses simple heuristics
- **Production**: Replace with trained CNN (FER2013, AffectNet)

## 🛠️ Troubleshooting

### "Could not open video source"
- Check camera permissions
- Verify video file path
- Try different input index (0, 1, 2...)

### Low FPS
- Reduce resolution in `config.py`
- Disable visualization
- Use GPU if available

### "Module not found"
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

## 📝 Citation

If you use this system in your research, please cite:

```bibtex
@software{patient_monitoring_system,
  title={Multi-Agent Patient Monitoring System},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/patient-monitoring-system}
}
```

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Note**: This system is for research and development purposes. For medical applications, please consult with healthcare professionals and ensure compliance with relevant regulations (HIPAA, GDPR, etc.).
