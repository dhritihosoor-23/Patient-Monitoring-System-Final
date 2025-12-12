"""
Configuration management for the Patient Monitoring System.
Contains model paths, thresholds, and system parameters.
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models" / "weights"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"

# Create directories if they don't exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==================== VIDEO PIPELINE ====================
VIDEO_CONFIG = {
    "input_source": 0,  # 0 for webcam, or path to video file
    "frame_width": 1280,
    "frame_height": 720,
    "fps": 30,
    "buffer_size": 30,  # Number of frames to buffer for temporal analysis
}

# ==================== PERCEPTION LAYER ====================
PERSON_DETECTION_CONFIG = {
    "model_name": "yolov8n.pt",  # YOLOv8 nano for speed
    "confidence_threshold": 0.3,
    "iou_threshold": 0.45,
    "device": "cpu",  # forced to CPU for compatibility
}

TRACKING_CONFIG = {
    "max_age": 30,  # Maximum frames to keep track alive without detection
    "min_hits": 3,  # Minimum detections before track is confirmed
    "iou_threshold": 0.3,
}

POSE_ESTIMATION_CONFIG = {
    "model_complexity": 1,  # MediaPipe: 0=Lite, 1=Full, 2=Heavy
    "min_detection_confidence": 0.5,
    "min_tracking_confidence": 0.5,
    "enable_segmentation": False,
}

FACE_DETECTION_CONFIG = {
    "min_detection_confidence": 0.1,
    "model_selection": 0,  # 0 = short-range (2m)
}

# ==================== FALL DETECTION AGENT ====================
FALL_DETECTION_CONFIG = {
    "model_path": MODELS_DIR / "fall_lstm.pth",
    "sequence_length": 30,  # Number of frames for temporal analysis
    "confidence_threshold": 0.7,
    "fall_angle_threshold": 60,  # degrees from vertical
    "hip_height_threshold": 0.3,  # normalized height (0-1)
    "velocity_threshold": 0.5,  # normalized velocity
    "events": ["fall", "near_fall", "lying", "abnormal_collapse"],
}

# ==================== EMOTION DETECTION AGENT ====================
EMOTION_DETECTION_CONFIG = {
    "model_path": MODELS_DIR / "emotion_model.pth",
    "emotions": ["happy", "sad", "angry", "fear", "disgust", "surprise", "neutral"],
    "confidence_threshold": 0.4,
    "face_crop_size": (224, 224),
    "update_interval": 5,  # Process every N frames to reduce computation
}

# ==================== VITAL SIGNS AGENT ====================
VITAL_SIGNS_CONFIG = {
    "algorithm": "CHROM",  # "CHROM", "POS", or "ICA"
    "fps": 30,
    "window_size": 300,  # 10 seconds at 30 fps
    "hr_range": (40, 180),  # Valid heart rate range (bpm)
    "rr_range": (8, 30),  # Valid respiratory rate range (breaths/min)
    "signal_quality_threshold": 0.6,
    "update_interval": 30,  # Update every N frames
}

# ==================== BED EXIT AGENT ====================
BED_EXIT_CONFIG = {
    "bed_region": None,  # Will be set via calibration or manual input
    "states": ["IN_BED", "SITTING_UP", "STANDING", "OUT_OF_BED"],
    "transition_confidence": 0.7,
    "sitting_angle_threshold": 45,  # degrees
    "standing_height_threshold": 0.6,  # normalized height
    "alert_on_states": ["STANDING", "OUT_OF_BED"],
}

# ==================== IMMOBILITY AGENT ====================
IMMOBILITY_CONFIG = {
    "movement_threshold": 0.05,  # Normalized movement magnitude
    "alert_duration": 7200,  # Alert after 2 hours (seconds)
    "warning_duration": 5400,  # Warning after 1.5 hours
    "check_interval": 60,  # Check every 60 seconds
    "posture_change_threshold": 15,  # degrees
}

# ==================== SEIZURE DETECTION AGENT ====================
SEIZURE_DETECTION_CONFIG = {
    "frequency_range": (3, 10),  # Hz - typical seizure frequency
    "magnitude_threshold": 0.3,
    "duration_threshold": 5,  # seconds
    "confidence_threshold": 0.75,
    "affected_limbs_min": 2,  # Minimum limbs showing seizure pattern
}

# ==================== ORCHESTRATOR ====================
ORCHESTRATOR_CONFIG = {
    "alert_levels": ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
    "deduplication_window": 5,  # seconds
    "rules": {
        # Rule format: (conditions, alert_level, message)
        "critical_fall": {
            "conditions": ["fall_detected", "low_heart_rate"],
            "level": "CRITICAL",
            "message": "Critical: Fall detected with abnormal vital signs",
        },
        "bed_exit_night": {
            "conditions": ["bed_exit", "nighttime"],
            "level": "HIGH",
            "message": "High Alert: Patient exited bed during nighttime",
        },
        "prolonged_immobility": {
            "conditions": ["immobility_alert"],
            "level": "MEDIUM",
            "message": "Warning: Prolonged immobility detected",
        },
        "seizure_detected": {
            "conditions": ["seizure"],
            "level": "CRITICAL",
            "message": "Critical: Seizure activity detected",
        },
    },
}

# ==================== VISUALIZATION ====================
VISUALIZATION_CONFIG = {
    "show_bboxes": True,
    "show_keypoints": True,
    "show_tracking_id": True,
    "show_vital_signs": True,
    "show_alerts": True,
    "alert_display_duration": 5,  # seconds
    "colors": {
        "bbox": (0, 255, 0),
        "keypoints": (255, 0, 0),
        "alert_critical": (0, 0, 255),
        "alert_high": (0, 100, 255),
        "alert_medium": (0, 255, 255),
        "alert_low": (0, 255, 0),
    },
}

# ==================== ALERT SYSTEM ====================
ALERT_CONFIG = {
    "enable_console": True,
    "enable_file": True,
    "enable_webhook": False,
    "enable_email": False,
    "log_file": LOGS_DIR / "alerts.log",
    "webhook_url": None,  # Set if using webhook
    "email_config": {
        "smtp_server": None,
        "smtp_port": 587,
        "sender": None,
        "recipients": [],
        "password": None,
    },
}

# ==================== PERFORMANCE ====================
PERFORMANCE_CONFIG = {
    "enable_profiling": False,
    "log_fps": True,
    "target_fps": 15,
    "skip_frames": 1,  # Process every Nth frame (1 = process all)
}

# ==================== NIGHTTIME DETECTION ====================
def is_nighttime():
    """Check if current time is nighttime (10 PM - 6 AM)"""
    from datetime import datetime
    hour = datetime.now().hour
    return hour >= 22 or hour < 6
