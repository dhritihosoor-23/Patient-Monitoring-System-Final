# Quick Start - Web Interface

## 🚀 Launch in 3 Steps

### 1. Install Dependencies
```bash
cd patient_monitoring_system
pip install -r requirements.txt
```

### 2. Start Web Server
```bash
python web_server.py
```

### 3. Open Browser
Navigate to: **http://localhost:5000**

## 📺 Using the Web Interface

### Upload a Video
1. Select "Upload Video" from dropdown
2. Click "Choose File"
3. Select your test video (MP4, AVI, MOV)
4. Click "Upload"
5. Wait for confirmation
6. Click "▶ Start Monitoring"

### Use Webcam
1. Select "Webcam (0)" from dropdown
2. Click "▶ Start Monitoring"
3. Allow camera access if prompted

### View Results
- **Video Feed**: Center panel shows processed video
- **Vital Signs**: Top right shows HR, RR, signal quality
- **Alerts**: Middle right shows critical events
- **Events**: Bottom right shows all detected events
- **FPS**: Bottom left shows processing speed

## 🎥 Test Videos

### Download Test Videos
```bash
python download_test_videos.py
```

This provides links to:
- **Pexels**: https://www.pexels.com/search/videos/elderly%20care/
- **Pixabay**: https://pixabay.com/videos/search/elderly/

### Recommended Test Scenarios

**Fall Detection:**
- Person standing → slowly lowering to ground
- Person sitting → lying down
- Person walking → crouching

**Bed Exit:**
- Person lying in bed
- Person sitting up
- Person standing from bed

**Vital Signs:**
- Close-up face (good lighting)
- Person sitting still 30+ seconds
- Minimal head movement

**Emotion:**
- Clear frontal face view
- Various expressions
- Good lighting

## 🎯 Quick Test

```bash
# 1. Start web server
python web_server.py

# 2. Open browser: http://localhost:5000

# 3. Select "Webcam (0)"

# 4. Click "▶ Start Monitoring"

# 5. Move in front of camera and test:
#    - Stand still (person detection)
#    - Move around (tracking)
#    - Face camera (emotion, vital signs)
#    - Sit/stand (bed exit simulation)
```

## 🔧 Troubleshooting

**"Address already in use":**
```bash
# Kill existing process
lsof -ti:5000 | xargs kill -9

# Or change port in web_server.py:
socketio.run(app, port=5001)
```

**Video not showing:**
- Check browser console (F12)
- Ensure WebSocket connected
- Try different browser (Chrome recommended)

**Slow performance:**
- Reduce resolution in config.py
- Close other tabs
- Use GPU if available

---

**Ready to monitor!** 🎯
