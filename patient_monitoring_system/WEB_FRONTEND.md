# Web Frontend Guide

## 🌐 Running the Web Interface

The Patient Monitoring System includes a modern web interface for real-time video monitoring.

### Quick Start

```bash
# 1. Install dependencies (if not already done)
pip install -r requirements.txt

# 2. Start the web server
python web_server.py
```

The server will start at: **http://localhost:5000**

### Features

- ✅ **Real-time video streaming** via WebSocket
- ✅ **Video upload** support (MP4, AVI, MOV)
- ✅ **Webcam selection** (multiple cameras)
- ✅ **Live event display** (falls, emotions, vital signs)
- ✅ **Alert notifications** (color-coded by severity)
- ✅ **Vital signs panel** (heart rate, respiratory rate)
- ✅ **FPS counter** for performance monitoring

### Usage

1. **Open browser** and navigate to `http://localhost:5000`

2. **Select video source**:
   - **Webcam (0)**: Default webcam
   - **Webcam (1)**: Secondary webcam
   - **Upload Video**: Upload your own test video

3. **Upload video** (if selected):
   - Click "Choose File"
   - Select MP4/AVI/MOV file
   - Click "Upload"
   - Wait for upload confirmation

4. **Start monitoring**:
   - Click "▶ Start Monitoring"
   - Video feed will appear
   - Events and alerts will update in real-time

5. **Stop monitoring**:
   - Click "⏹ Stop"

### Interface Layout

```
┌─────────────────────────────────────────────────────────┐
│  🏥 Patient Monitoring System        ● Active/Inactive  │
├──────────────────────────┬──────────────────────────────┤
│                          │  💓 Vital Signs              │
│   📹 Video Feed          │  - Heart Rate: 72 bpm        │
│                          │  - Respiratory Rate: 16/min  │
│                          │  - Signal Quality: 0.85      │
│                          ├──────────────────────────────┤
│                          │  🚨 Active Alerts            │
│                          │  [HIGH] Fall detected        │
│                          │  [MEDIUM] Bed exit           │
├──────────────────────────┼──────────────────────────────┤
│  Video Source: [Webcam]  │  📊 Recent Events            │
│  [▶ Start] [⏹ Stop]      │  - Fall Detection (85%)      │
│  FPS: 25.3               │  - Emotion: Happy (70%)      │
└──────────────────────────┴──────────────────────────────┘
```

### Alert Levels

- 🔴 **CRITICAL**: Falls, seizures (red background)
- 🟠 **HIGH**: Bed exit at night (orange background)
- 🟡 **MEDIUM**: Immobility warnings (yellow background)
- 🟢 **LOW**: General notifications (green background)

### API Endpoints

The web server exposes the following REST API:

#### Start Monitoring
```bash
POST /api/start
Content-Type: application/json

{
  "source": "0"  # or video file path
}
```

#### Stop Monitoring
```bash
POST /api/stop
```

#### Upload Video
```bash
POST /api/upload
Content-Type: multipart/form-data

video: <file>
```

#### Get Status
```bash
GET /api/status
```

### WebSocket Events

The server emits real-time updates via WebSocket:

#### `frame_update`
```javascript
{
  "frame": "base64_encoded_jpeg",
  "events": [
    {
      "type": "fall_detection",
      "confidence": 0.85,
      "agent": "fall_detection",
      "timestamp": 1234567890.123
    }
  ],
  "alerts": [
    {
      "level": "HIGH",
      "message": "Fall detected",
      "timestamp": 1234567890.123
    }
  ],
  "fps": 25.3
}
```

#### `monitoring_stopped`
```javascript
{
  "reason": "End of video"
}
```

### Troubleshooting

**Port already in use:**
```bash
# Change port in web_server.py (last line):
socketio.run(app, host='0.0.0.0', port=5001, debug=True)
```

**Video not displaying:**
- Check browser console for errors
- Ensure WebSocket connection is established
- Try different video source

**Slow performance:**
- Reduce video resolution in `config.py`
- Close other browser tabs
- Use Chrome/Firefox for best performance

### Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Security Note

⚠️ **For development only!** This server is not production-ready.

For production deployment:
- Use HTTPS (SSL/TLS)
- Add authentication
- Implement rate limiting
- Use production WSGI server (Gunicorn, uWSGI)
- Configure CORS properly

### Production Deployment

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --worker-class eventlet -w 1 web_server:app --bind 0.0.0.0:5000
```

---

**Enjoy real-time monitoring!** 🎯
