"""
Video Pipeline
Handles video capture, frame preprocessing, and distribution to perception layer.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
import time

import sys
sys.path.append('..')

from schemas import FrameMetadata, PersonDetection, BoundingBox
from perception.person_detector import PersonDetector
from perception.person_tracker import PersonTracker
from perception.pose_estimator import PoseEstimator
from perception.face_detector import FaceDetector


class VideoPipeline:
    """
    Video capture and preprocessing pipeline.
    
    Responsibilities:
    - Capture frames from video source
    - Run perception layer (detection, tracking, pose, face)
    - Create FrameMetadata for agents
    """
    
    def __init__(self, config: dict):
        """
        Initialize video pipeline.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.input_source = config.get("input_source", 0)
        self.frame_width = config.get("frame_width", 1280)
        self.frame_height = config.get("frame_height", 720)
        self.target_fps = config.get("fps", 30)
        
        # Video capture
        self.cap = None
        self.frame_count = 0
        self.start_time = time.time()
        
        # Perception components (initialized lazily)
        self.person_detector = None
        self.person_tracker = None
        self.pose_estimator = None
        self.face_detector = None
        
    def initialize(self, person_detector_config, tracking_config, pose_config, face_config):
        """Initialize perception components"""
        self.person_detector = PersonDetector(person_detector_config)
        self.person_tracker = PersonTracker(tracking_config)
        self.pose_estimator = PoseEstimator(pose_config)
        self.face_detector = FaceDetector(face_config)
        
        print("✓ Video pipeline perception layer initialized")
    
    def start(self) -> bool:
        """Start video capture"""
        self.cap = cv2.VideoCapture(self.input_source)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open video source: {self.input_source}")
            return False
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        
        # Get actual resolution
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"✓ Video capture started: {self.frame_width}x{self.frame_height} @ {self.target_fps} fps")
        print(f"  Source: {self.input_source}")
        
        self.start_time = time.time()
        self.frame_count = 0
        
        return True
    
    def read_frame(self) -> Tuple[Optional[np.ndarray], Optional[FrameMetadata]]:
        """
        Read and process next frame.
        
        Returns:
            Tuple of (frame, metadata) or (None, None) if no frame available
        """
        if self.cap is None or not self.cap.isOpened():
            return None, None
        
        ret, frame = self.cap.read()
        
        if not ret:
            return None, None
        
        self.frame_count += 1
        timestamp = time.time()
        
        # Run perception layer
        detections = self._run_perception(frame)
        
        # Create metadata
        metadata = FrameMetadata(
            frame_id=self.frame_count,
            timestamp=timestamp,
            width=self.frame_width,
            height=self.frame_height,
            fps=self.get_fps(),
            detections=detections,
        )
        
        return frame, metadata
    
    def _run_perception(self, frame: np.ndarray) -> list:
        """Run perception layer on frame"""
        detections = []
        
        # Person detection
        if self.person_detector:
            person_bboxes = self.person_detector.detect(frame)
        else:
            person_bboxes = []
        
        # Person tracking
        if self.person_tracker and person_bboxes:
            tracked_objects = self.person_tracker.update(frame, person_bboxes)
        else:
            # Create dummy tracked objects
            tracked_objects = [
                {"track_id": i, "bbox": bbox, "confidence": bbox.confidence}
                for i, bbox in enumerate(person_bboxes)
            ]
        
        # Process each tracked person
        for tracked_obj in tracked_objects:
            track_id = tracked_obj["track_id"]
            bbox = tracked_obj["bbox"]
            confidence = tracked_obj["confidence"]
            
            # Pose estimation
            pose = None
            if self.pose_estimator:
                pose = self.pose_estimator.estimate(frame, bbox)
            
            # Face detection
            face_bbox = None
            if self.face_detector:
                faces = self.face_detector.detect(frame, bbox)
                if faces:
                    face_bbox = faces[0]  # Use first detected face
            
            # Create PersonDetection
            detection = PersonDetection(
                track_id=track_id,
                bbox=bbox,
                confidence=confidence,
                pose=pose,
                face_bbox=face_bbox,
            )
            detections.append(detection)
        
        return detections
    
    def get_fps(self) -> float:
        """Calculate current FPS"""
        if self.frame_count == 0:
            return 0.0
        
        elapsed = time.time() - self.start_time
        return self.frame_count / elapsed if elapsed > 0 else 0.0
    
    def stop(self):
        """Stop video capture"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        print("✓ Video capture stopped")
    
    def __del__(self):
        """Cleanup"""
        self.stop()
