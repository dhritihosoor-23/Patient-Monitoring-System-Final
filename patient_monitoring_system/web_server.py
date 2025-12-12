"""
Web server for Patient Monitoring System.
Provides REST API and WebSocket for real-time monitoring.
"""

from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import numpy as np
import base64
import threading
import time
import json
from pathlib import Path

import sys
sys.path.append('..')

from config import (
    VIDEO_CONFIG, PERSON_DETECTION_CONFIG, TRACKING_CONFIG,
    POSE_ESTIMATION_CONFIG, FACE_DETECTION_CONFIG,
    FALL_DETECTION_CONFIG, EMOTION_DETECTION_CONFIG,
    VITAL_SIGNS_CONFIG, BED_EXIT_CONFIG, IMMOBILITY_CONFIG,
    SEIZURE_DETECTION_CONFIG, VISUALIZATION_CONFIG
)
from core.video_pipeline import VideoPipeline
from core.orchestrator import Orchestrator
from core.visualizer import Visualizer
from agents.fall_detection_agent import FallDetectionAgent
from agents.emotion_detection_agent import EmotionDetectionAgent
from agents.vital_signs_agent import VitalSignsAgent
from agents.bed_exit_agent import BedExitAgent
from agents.immobility_agent import ImmobilityAgent
from agents.seizure_detection_agent import SeizureDetectionAgent

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'patient-monitoring-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Global state
monitoring_active = False
monitoring_thread = None
current_video_source = None


class MonitoringSystem:
    """Monitoring system wrapper for web interface"""
    
    def __init__(self):
        self.video_pipeline = None
        self.orchestrator = Orchestrator()
        self.visualizer = Visualizer(VISUALIZATION_CONFIG)
        self.agents = []
        self.running = False
        
    def initialize(self, video_source):
        """Initialize monitoring system"""
        # Update video config
        video_config = VIDEO_CONFIG.copy()
        video_config["input_source"] = video_source
        
        # Initialize pipeline
        self.video_pipeline = VideoPipeline(video_config)
        self.video_pipeline.initialize(
            PERSON_DETECTION_CONFIG,
            TRACKING_CONFIG,
            POSE_ESTIMATION_CONFIG,
            FACE_DETECTION_CONFIG
        )
        
        # Initialize agents
        self.agents = [
            FallDetectionAgent(FALL_DETECTION_CONFIG),
            EmotionDetectionAgent(EMOTION_DETECTION_CONFIG),
            VitalSignsAgent(VITAL_SIGNS_CONFIG),
            BedExitAgent(BED_EXIT_CONFIG),
            ImmobilityAgent(IMMOBILITY_CONFIG),
            SeizureDetectionAgent(SEIZURE_DETECTION_CONFIG),
        ]
        
        return self.video_pipeline.start()
    
    def process_frame(self):
        """Process single frame and return results"""
        frame, metadata = self.video_pipeline.read_frame()
        
        if frame is None:
            return None, None, None
        
        # Process with agents
        events = []
        for agent in self.agents:
            event = agent.detect(frame, metadata)
            if event:
                events.append(event)
        
        # Orchestrate
        alerts = self.orchestrator.process_events(events)
        
        # Get vital signs
        vital_signs = {}
        for event in events:
            if event.event_type == "vital_signs":
                vital_signs = {
                    "heart_rate": event.heart_rate,
                    "respiratory_rate": event.respiratory_rate,
                    "signal_quality": event.signal_quality,
                }
        
        # Visualize
        vis_frame = self.visualizer.render(frame, metadata, alerts, vital_signs)
        
        return vis_frame, events, alerts
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.video_pipeline:
            self.video_pipeline.stop()


# Global monitoring system
monitoring_system = MonitoringSystem()


def monitoring_loop():
    """Main monitoring loop for WebSocket streaming"""
    global monitoring_active
    
    print("🎬 Monitoring loop started!")
    
    while monitoring_active:
        try:
            vis_frame, events, alerts = monitoring_system.process_frame()
            
            if vis_frame is None:
                monitoring_active = False
                socketio.emit('monitoring_stopped', {'reason': 'End of video'})
                break
            
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', vis_frame)
            
            # Debug: Save first frame
            if not hasattr(monitoring_loop, "debug_saved"):
                cv2.imwrite("debug_frame.jpg", vis_frame)
                monitoring_loop.debug_saved = True
                print("Saved debug_frame.jpg")
                
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Prepare event data
            event_data = []
            for event in events:
                event_data.append({
                    'type': event.event_type,
                    'confidence': event.confidence,
                    'agent': event.agent_name,
                    'timestamp': event.timestamp,
                })
            
            # Prepare alert data
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    'level': alert.level,
                    'message': alert.message,
                    'timestamp': alert.timestamp,
                })
            
            # Emit to clients
            print(f"Emitting frame: {len(frame_base64)} bytes, FPS: {monitoring_system.video_pipeline.get_fps():.1f}")
            socketio.emit('frame_update', {
                'frame': frame_base64,
                'events': event_data,
                'alerts': alert_data,
                'fps': monitoring_system.video_pipeline.get_fps(),
            })
            
            time.sleep(0.01)  # Small delay to prevent overwhelming clients
            
        except Exception as e:
            import traceback
            print(f"❌ Error in monitoring loop: {e}")
            traceback.print_exc()
            monitoring_active = False
            socketio.emit('monitoring_stopped', {'reason': str(e)})
            break


@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


@app.route('/test')
def test():
    """Serve test page"""
    return render_template('test.html')


@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start monitoring"""
    global monitoring_active, monitoring_thread, current_video_source
    
    data = request.json
    video_source = data.get('source', 0)
    
    # Convert to int if it's a webcam index
    try:
        video_source = int(video_source)
    except ValueError:
        pass  # It's a file path
    
    if monitoring_active:
        return jsonify({'error': 'Monitoring already active'}), 400
    
    # Initialize system
    if not monitoring_system.initialize(video_source):
        return jsonify({'error': f'Failed to initialize video source {video_source}. Please check if the camera is connected and accessible, or try a different source.'}), 400
    
    current_video_source = video_source
    monitoring_active = True
    monitoring_system.running = True
    
    # Start monitoring thread
    monitoring_thread = threading.Thread(target=monitoring_loop)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    
    return jsonify({'status': 'started', 'source': video_source})


@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring"""
    global monitoring_active
    
    monitoring_active = False
    monitoring_system.stop()
    
    return jsonify({'status': 'stopped'})


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get monitoring status"""
    return jsonify({
        'active': monitoring_active,
        'source': current_video_source,
    })


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Upload video file"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save uploaded file
    upload_dir = Path('uploads')
    upload_dir.mkdir(exist_ok=True)
    
    filepath = upload_dir / video_file.filename
    video_file.save(str(filepath))
    
    return jsonify({
        'status': 'uploaded',
        'path': str(filepath),
        'filename': video_file.filename,
    })


if __name__ == '__main__':
    print("="*80)
    print("Patient Monitoring System - Web Server")
    print("="*80)
    print("\nStarting server at http://localhost:5001")
    print("Press Ctrl+C to stop\n")
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
