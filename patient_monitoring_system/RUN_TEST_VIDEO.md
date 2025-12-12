# 🚀 Running Your Test Video - Step by Step

## Your Test Video
✅ Found: `test_videos/01.mp4` (6.9 MB)

## Option 1: Web Interface (Recommended - Visual)

### Step 1: Start the Web Server
```bash
cd /Users/sujith/Desktop/Reva/patient_monitoring_system
python web_server.py
```

### Step 2: Open Browser
Navigate to: **http://localhost:5000**

### Step 3: Upload Your Video
1. In the dropdown, select **"Upload Video"**
2. Click **"Choose File"**
3. Navigate to `test_videos/01.mp4`
4. Click **"Upload"** button
5. Wait for upload confirmation
6. Click **"▶ Start Monitoring"**

### Step 4: Watch the Results
You'll see in real-time:
- 📹 **Video Feed**: Processed video with overlays
- 💓 **Vital Signs**: Heart rate, respiratory rate (if face visible)
- 🚨 **Alerts**: Fall detection, bed exit, etc.
- 📊 **Events**: All detected activities
- ⚡ **FPS**: Processing speed

---

## Option 2: Command Line (Faster)

```bash
cd /Users/sujith/Desktop/Reva/patient_monitoring_system

# Run with visualization
python main.py --input test_videos/01.mp4 --visualize --output output/01_processed.mp4

# This will:
# - Show live video window with overlays
# - Save processed video to output/01_processed.mp4
# - Print alerts to console
# - Log events to logs/alerts.log
```

---

## What You'll See

### Visual Overlays:
- 🟢 **Green boxes**: Person detection
- 🔴 **Red dots**: Pose keypoints (33 points)
- 🟡 **Yellow box**: Face detection
- **Track ID**: Person identifier
- **Vital signs panel**: HR, RR, quality
- **Alert messages**: Color-coded by severity

### Console Output:
```
[HIGH] Fall detected
[MEDIUM] Bed exit: SITTING_UP
[INFO] Emotion: happy (0.75)
```

### Log File:
Check `logs/alerts.log` for complete event history

---

## Quick Launch Commands

### Web Interface:
```bash
# Quick launch
bash launch_web.sh

# Or manually
python web_server.py
# Then open: http://localhost:5000
```

### Command Line:
```bash
# With visualization
python main.py --input test_videos/01.mp4 --visualize

# Save output
python main.py --input test_videos/01.mp4 --visualize --output output/result.mp4

# Headless (no window)
python main.py --input test_videos/01.mp4 --output output/result.mp4
```

---

## Keyboard Controls (Command Line Mode)

- **q**: Quit
- **Ctrl+C**: Stop

---

## Expected Performance

| Component | What to Expect |
|-----------|---------------|
| Person Detection | Green box around person |
| Pose Estimation | 33 keypoints on body |
| Face Detection | Yellow box on face |
| Fall Detection | Alert if person falls/lies down |
| Emotion | Detected emotion (if face clear) |
| Vital Signs | HR/RR (if face still & well-lit) |
| Bed Exit | State changes (in bed → sitting → standing) |

---

## Troubleshooting

**"No module named 'flask'":**
```bash
pip install Flask Flask-SocketIO Flask-CORS python-socketio eventlet
```

**"Could not open video":**
```bash
# Check file exists
ls -lh test_videos/01.mp4

# Try absolute path
python main.py --input /Users/sujith/Desktop/Reva/patient_monitoring_system/test_videos/01.mp4 --visualize
```

**Slow processing:**
- Expected: 5-15 FPS on CPU, 20-30 FPS on GPU
- Normal for first run (model loading)

---

## 🎯 Ready to Run!

Choose your preferred method and run the commands above.

**Recommended**: Start with the web interface for the best visual experience!
