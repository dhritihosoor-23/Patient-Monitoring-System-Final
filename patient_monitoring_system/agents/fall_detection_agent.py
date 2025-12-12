"""
Fall Detection Agent
Detects falls, near-falls, lying on ground, and abnormal collapses using pose keypoints.
"""

import numpy as np
from typing import Optional, List
import time
from collections import deque

import sys
sys.path.append('..')

from core.base_agent import BaseAgent
from schemas import FallDetectionEvent, FrameMetadata, PoseData
from utils.geometry import compute_angle, compute_distance, normalize_keypoints
from utils.temporal_buffer import TemporalBuffer


class FallDetectionAgent(BaseAgent):
    """
    Detects fall events using pose keypoints and temporal analysis.
    
    Analyzes:
    - Vertical velocity of key body points
    - Torso angle from vertical
    - Hip height relative to frame
    - Sudden changes in pose
    """
    
    def __init__(self, config: dict):
        super().__init__("fall_detection", config)
        
        self.sequence_length = config.get("sequence_length", 30)
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.fall_angle_threshold = config.get("fall_angle_threshold", 60)
        self.hip_height_threshold = config.get("hip_height_threshold", 0.3)
        self.velocity_threshold = config.get("velocity_threshold", 0.5)
        
        # Temporal buffer for pose sequences
        self.pose_buffer = TemporalBuffer(maxlen=self.sequence_length)
        self.last_event_time = 0
        self.event_cooldown = 3.0  # seconds
        
    def detect(self, frame: np.ndarray, metadata: FrameMetadata) -> Optional[FallDetectionEvent]:
        """
        Detect fall events from pose data.
        
        Args:
            frame: Current frame (not used directly)
            metadata: Frame metadata with pose data
            
        Returns:
            FallDetectionEvent if fall detected, None otherwise
        """
        if not self.enabled:
            return None
        
        self.frame_count += 1
        
        # Check if we have person detections with pose
        if not metadata.detections:
            return None
        
        # Process first detected person (can be extended for multi-person)
        detection = metadata.detections[0]
        if detection.pose is None:
            return None
        
        pose = detection.pose
        
        # Add to temporal buffer
        self.pose_buffer.add({
            "pose": pose,
            "timestamp": metadata.timestamp,
            "bbox": detection.bbox,
        })
        
        # Need enough frames for temporal analysis
        if len(self.pose_buffer) < self.sequence_length:
            return None
        
        # Cooldown to prevent duplicate events
        if time.time() - self.last_event_time < self.event_cooldown:
            return None
        
        # Analyze current pose and temporal sequence
        fall_indicators = self._analyze_fall_indicators(pose, metadata.height)
        
        # Check for fall conditions
        fall_type = None
        confidence = 0.0
        
        if fall_indicators["is_lying"]:
            fall_type = "lying"
            confidence = fall_indicators["lying_confidence"]
        elif fall_indicators["is_falling"]:
            fall_type = "fall"
            confidence = fall_indicators["fall_confidence"]
        elif fall_indicators["is_near_fall"]:
            fall_type = "near_fall"
            confidence = fall_indicators["near_fall_confidence"]
        
        if fall_type and confidence > self.confidence_threshold:
            self.last_event_time = time.time()
            
            return FallDetectionEvent(
                event_type="fall_detection",
                timestamp=metadata.timestamp,
                confidence=confidence,
                agent_name=self.agent_name,
                frame_id=metadata.frame_id,
                fall_type=fall_type,
                bbox=detection.bbox,
                pose_vector=self._get_pose_vector(pose),
                torso_angle=fall_indicators["torso_angle"],
                hip_height=fall_indicators["hip_height"],
                vertical_velocity=fall_indicators["vertical_velocity"],
            )
        
        return None
    
    def _analyze_fall_indicators(self, pose: PoseData, frame_height: int) -> dict:
        """Analyze pose for fall indicators"""
        keypoints = pose.keypoints
        
        # Key body points (MediaPipe indices)
        nose = keypoints[0]
        left_shoulder = keypoints[11]
        right_shoulder = keypoints[12]
        left_hip = keypoints[23]
        right_hip = keypoints[24]
        left_knee = keypoints[25]
        right_knee = keypoints[26]
        
        # Compute torso angle from vertical
        mid_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        mid_hip_y = (left_hip.y + right_hip.y) / 2
        mid_shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
        mid_hip_x = (left_hip.x + right_hip.x) / 2
        
        torso_angle = abs(np.degrees(np.arctan2(
            mid_shoulder_x - mid_hip_x,
            mid_shoulder_y - mid_hip_y
        )))
        
        # Compute normalized hip height
        hip_height = 1.0 - (mid_hip_y / frame_height)
        
        # Compute vertical velocity from temporal buffer
        vertical_velocity = self._compute_vertical_velocity()
        
        # Determine fall indicators
        is_lying = (
            hip_height < self.hip_height_threshold and
            torso_angle > self.fall_angle_threshold
        )
        
        is_falling = (
            vertical_velocity > self.velocity_threshold and
            torso_angle > self.fall_angle_threshold / 2
        )
        
        is_near_fall = (
            vertical_velocity > self.velocity_threshold * 0.7 and
            torso_angle > self.fall_angle_threshold * 0.7
        )
        
        return {
            "torso_angle": torso_angle,
            "hip_height": hip_height,
            "vertical_velocity": vertical_velocity,
            "is_lying": is_lying,
            "is_falling": is_falling,
            "is_near_fall": is_near_fall,
            "lying_confidence": min(1.0, (1.0 - hip_height) * (torso_angle / 90.0)),
            "fall_confidence": min(1.0, vertical_velocity * (torso_angle / 90.0)),
            "near_fall_confidence": min(1.0, vertical_velocity * 0.8),
        }
    
    def _compute_vertical_velocity(self) -> float:
        """Compute vertical velocity from pose buffer"""
        if len(self.pose_buffer) < 2:
            return 0.0
        
        # Get hip positions from first and last frames
        first_frame = self.pose_buffer.get_oldest()
        last_frame = self.pose_buffer.get_latest()
        
        first_pose = first_frame["pose"]
        last_pose = last_frame["pose"]
        
        # Average hip y-coordinate
        first_hip_y = (first_pose.keypoints[23].y + first_pose.keypoints[24].y) / 2
        last_hip_y = (last_pose.keypoints[23].y + last_pose.keypoints[24].y) / 2
        
        # Compute velocity (normalized)
        time_diff = last_frame["timestamp"] - first_frame["timestamp"]
        if time_diff > 0:
            velocity = abs(last_hip_y - first_hip_y) / time_diff
            return min(1.0, velocity / 100.0)  # Normalize
        
        return 0.0
    
    def _get_pose_vector(self, pose: PoseData) -> List[float]:
        """Convert pose to flat vector"""
        vector = []
        for kp in pose.keypoints:
            vector.extend([kp.x, kp.y, kp.z])
        return vector
    
    def reset(self):
        """Reset agent state"""
        super().reset()
        self.pose_buffer.clear()
        self.last_event_time = 0
