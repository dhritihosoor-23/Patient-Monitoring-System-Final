"""
Bed Exit Agent
Detects when patient exits bed using state machine.
"""

import numpy as np
from typing import Optional
import time

import sys
sys.path.append('..')

from core.base_agent import BaseAgent
from schemas import BedExitEvent, FrameMetadata, BoundingBox
from utils.geometry import compute_iou, point_in_bbox


class BedExitAgent(BaseAgent):
    """
    Detects bed exit events using state machine.
    
    States: IN_BED → SITTING_UP → STANDING → OUT_OF_BED
    """
    
    def __init__(self, config: dict):
        super().__init__("bed_exit", config)
        
        self.bed_region = config.get("bed_region", None)  # BoundingBox or None
        self.states = config.get("states", ["IN_BED", "SITTING_UP", "STANDING", "OUT_OF_BED"])
        self.transition_confidence = config.get("transition_confidence", 0.7)
        self.sitting_angle_threshold = config.get("sitting_angle_threshold", 45)
        self.standing_height_threshold = config.get("standing_height_threshold", 0.6)
        self.alert_on_states = config.get("alert_on_states", ["STANDING", "OUT_OF_BED"])
        
        self.current_state = "IN_BED"
        self.state_start_time = time.time()
        self.last_transition_time = 0
        
        # Auto-calibrate bed region if not provided
        self.calibration_frames = 0
        self.calibration_bboxes = []
        
    def detect(self, frame: np.ndarray, metadata: FrameMetadata) -> Optional[BedExitEvent]:
        """
        Detect bed exit events.
        
        Args:
            frame: Current frame
            metadata: Frame metadata with pose data
            
        Returns:
            BedExitEvent if state change or alert condition, None otherwise
        """
        if not self.enabled:
            return None
        
        self.frame_count += 1
        
        # Auto-calibrate bed region
        if self.bed_region is None:
            return self._calibrate_bed_region(metadata)
        
        # Check if we have person detections
        if not metadata.detections:
            return None
        
        detection = metadata.detections[0]
        person_bbox = detection.bbox
        pose = detection.pose
        
        if pose is None:
            return None
        
        # Determine current state
        new_state = self._determine_state(person_bbox, pose, metadata.height)
        
        # Check for state transition
        transition = new_state != self.current_state
        
        if transition:
            previous_state = self.current_state
            self.current_state = new_state
            self.last_transition_time = time.time()
            duration_in_previous_state = self.last_transition_time - self.state_start_time
            self.state_start_time = self.last_transition_time
            
            # Generate event for transitions or alert states
            if new_state in self.alert_on_states:
                return BedExitEvent(
                    event_type="bed_exit",
                    timestamp=metadata.timestamp,
                    confidence=self.transition_confidence,
                    agent_name=self.agent_name,
                    frame_id=metadata.frame_id,
                    state=new_state,
                    previous_state=previous_state,
                    transition=True,
                    duration_in_state=0.0,
                    bed_region=self.bed_region,
                    person_bbox=person_bbox,
                )
        
        return None
    
    def _determine_state(self, person_bbox: BoundingBox, pose, frame_height: int) -> str:
        """Determine current state based on position and pose"""
        # Get key body points
        keypoints = pose.keypoints
        left_hip = keypoints[23]
        right_hip = keypoints[24]
        left_shoulder = keypoints[11]
        right_shoulder = keypoints[12]
        
        # Compute metrics
        mid_hip_y = (left_hip.y + right_hip.y) / 2
        mid_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        
        # Normalized height (0 = bottom, 1 = top)
        hip_height = 1.0 - (mid_hip_y / frame_height)
        
        # Torso angle
        torso_angle = abs(np.degrees(np.arctan2(
            (left_shoulder.x + right_shoulder.x) / 2 - (left_hip.x + right_hip.x) / 2,
            mid_shoulder_y - mid_hip_y
        )))
        
        # Check overlap with bed region
        if self.bed_region:
            overlap = compute_iou(person_bbox, self.bed_region)
        else:
            overlap = 0.0
        
        # State logic
        if hip_height > self.standing_height_threshold and torso_angle < 30:
            return "STANDING"
        elif overlap < 0.3:
            return "OUT_OF_BED"
        elif torso_angle > self.sitting_angle_threshold and hip_height > 0.3:
            return "SITTING_UP"
        else:
            return "IN_BED"
    
    def _calibrate_bed_region(self, metadata: FrameMetadata) -> None:
        """Auto-calibrate bed region from first N frames"""
        if not metadata.detections:
            return None
        
        detection = metadata.detections[0]
        self.calibration_bboxes.append(detection.bbox)
        self.calibration_frames += 1
        
        # After 30 frames, compute average bed region
        if self.calibration_frames >= 30:
            # Use average of bounding boxes as bed region
            avg_x1 = np.mean([bbox.x1 for bbox in self.calibration_bboxes])
            avg_y1 = np.mean([bbox.y1 for bbox in self.calibration_bboxes])
            avg_x2 = np.mean([bbox.x2 for bbox in self.calibration_bboxes])
            avg_y2 = np.mean([bbox.y2 for bbox in self.calibration_bboxes])
            
            # Expand region by 20% for tolerance
            width = avg_x2 - avg_x1
            height = avg_y2 - avg_y1
            
            self.bed_region = BoundingBox(
                x1=avg_x1 - width * 0.1,
                y1=avg_y1 - height * 0.1,
                x2=avg_x2 + width * 0.1,
                y2=avg_y2 + height * 0.1,
                confidence=1.0,
            )
            
            print(f"✓ Bed region calibrated: {self.bed_region}")
        
        return None
    
    def reset(self):
        """Reset agent state"""
        super().reset()
        self.current_state = "IN_BED"
        self.state_start_time = time.time()
        self.last_transition_time = 0
