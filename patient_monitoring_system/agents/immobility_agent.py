"""
Immobility / Pressure Ulcer Agent
Tracks patient movement and alerts on prolonged immobility.
"""

import numpy as np
from typing import Optional
import time

import sys
sys.path.append('..')

from core.base_agent import BaseAgent
from schemas import ImmobilityEvent, FrameMetadata
from utils.temporal_buffer import TemporalBuffer


class ImmobilityAgent(BaseAgent):
    """
    Detects prolonged immobility and pressure ulcer risk.
    
    Tracks:
    - Movement frequency
    - Posture changes
    - Time since last significant movement
    """
    
    def __init__(self, config: dict):
        super().__init__("immobility", config)
        
        self.movement_threshold = config.get("movement_threshold", 0.05)
        self.alert_duration = config.get("alert_duration", 7200)  # 2 hours
        self.warning_duration = config.get("warning_duration", 5400)  # 1.5 hours
        self.check_interval = config.get("check_interval", 60)  # Check every 60 seconds
        self.posture_change_threshold = config.get("posture_change_threshold", 15)
        
        self.last_pose = None
        self.last_movement_time = time.time()
        self.last_check_time = time.time()
        self.posture_change_count = 0
        self.current_posture = "unknown"
        
        # Buffer for movement tracking
        self.pose_buffer = TemporalBuffer(maxlen=30)
        
    def detect(self, frame: np.ndarray, metadata: FrameMetadata) -> Optional[ImmobilityEvent]:
        """
        Detect immobility events.
        
        Args:
            frame: Current frame
            metadata: Frame metadata with pose data
            
        Returns:
            ImmobilityEvent if prolonged immobility detected, None otherwise
        """
        if not self.enabled:
            return None
        
        self.frame_count += 1
        
        # Check if we have person detections with pose
        if not metadata.detections:
            return None
        
        detection = metadata.detections[0]
        pose = detection.pose
        
        if pose is None:
            return None
        
        # Add to buffer
        self.pose_buffer.add({
            "pose": pose,
            "timestamp": metadata.timestamp,
        })
        
        # Compute movement
        if self.last_pose is not None:
            movement_magnitude = self._compute_movement(self.last_pose, pose)
            
            if movement_magnitude > self.movement_threshold:
                self.last_movement_time = time.time()
            
            # Check for posture change
            new_posture = self._determine_posture(pose)
            if new_posture != self.current_posture:
                self.posture_change_count += 1
                self.current_posture = new_posture
        
        self.last_pose = pose
        
        # Check periodically
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return None
        
        self.last_check_time = current_time
        
        # Compute immobility duration
        immobility_duration = current_time - self.last_movement_time
        
        # Determine risk level
        if immobility_duration > self.alert_duration:
            risk_level = "HIGH"
        elif immobility_duration > self.warning_duration:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Generate event if risk is elevated
        if risk_level in ["MEDIUM", "HIGH"]:
            return ImmobilityEvent(
                event_type="immobility",
                timestamp=metadata.timestamp,
                confidence=min(1.0, immobility_duration / self.alert_duration),
                agent_name=self.agent_name,
                frame_id=metadata.frame_id,
                immobility_duration=immobility_duration,
                last_movement_time=self.last_movement_time,
                risk_level=risk_level,
                posture=self.current_posture,
                movement_magnitude=0.0,
                posture_change_count=self.posture_change_count,
            )
        
        return None
    
    def _compute_movement(self, pose1, pose2) -> float:
        """Compute movement magnitude between two poses"""
        # Compute average displacement of key body points
        key_indices = [0, 11, 12, 23, 24]  # nose, shoulders, hips
        
        total_displacement = 0.0
        count = 0
        
        for idx in key_indices:
            kp1 = pose1.keypoints[idx]
            kp2 = pose2.keypoints[idx]
            
            if kp1.visibility > 0.5 and kp2.visibility > 0.5:
                displacement = np.sqrt(
                    (kp1.x - kp2.x) ** 2 + (kp1.y - kp2.y) ** 2
                )
                total_displacement += displacement
                count += 1
        
        if count > 0:
            return total_displacement / count
        
        return 0.0
    
    def _determine_posture(self, pose) -> str:
        """Determine posture from pose keypoints"""
        keypoints = pose.keypoints
        
        # Get shoulder and hip positions
        left_shoulder = keypoints[11]
        right_shoulder = keypoints[12]
        left_hip = keypoints[23]
        right_hip = keypoints[24]
        
        # Compute torso angle
        mid_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        mid_hip_y = (left_hip.y + right_hip.y) / 2
        mid_shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
        mid_hip_x = (left_hip.x + right_hip.x) / 2
        
        torso_angle = abs(np.degrees(np.arctan2(
            mid_shoulder_x - mid_hip_x,
            mid_shoulder_y - mid_hip_y
        )))
        
        # Simple posture classification
        if torso_angle > 60:
            return "lying_side"
        elif mid_shoulder_y < mid_hip_y:
            return "prone"
        else:
            return "supine"
    
    def reset(self):
        """Reset agent state"""
        super().reset()
        self.last_pose = None
        self.last_movement_time = time.time()
        self.last_check_time = time.time()
        self.posture_change_count = 0
        self.pose_buffer.clear()
