"""
Vital Signs Agent (rPPG)
Extracts heart rate and respiratory rate from facial ROI using remote photoplethysmography.
"""

import numpy as np
from typing import Optional
import cv2
from collections import deque

import sys
sys.path.append('..')

from core.base_agent import BaseAgent
from schemas import VitalSignsEvent, FrameMetadata
from models.rppg_processor import RPPGProcessor


class VitalSignsAgent(BaseAgent):
    """
    Extracts vital signs (HR, RR) using rPPG from facial video.
    
    Uses CHROM, POS, or ICA algorithm to extract pulse signal from skin color changes.
    """
    
    def __init__(self, config: dict):
        super().__init__("vital_signs", config)
        
        self.algorithm = config.get("algorithm", "CHROM")
        self.fps = config.get("fps", 30)
        self.window_size = config.get("window_size", 300)  # 10 seconds
        self.hr_range = config.get("hr_range", (40, 180))
        self.rr_range = config.get("rr_range", (8, 30))
        self.signal_quality_threshold = config.get("signal_quality_threshold", 0.6)
        self.update_interval = config.get("update_interval", 30)
        
        # Initialize rPPG processor
        self.rppg_processor = RPPGProcessor(
            algorithm=self.algorithm,
            fps=self.fps,
            window_size=self.window_size,
        )
        
        self.face_roi_buffer = deque(maxlen=self.window_size)
        self.last_update_frame = 0
        
    def detect(self, frame: np.ndarray, metadata: FrameMetadata) -> Optional[VitalSignsEvent]:
        """
        Extract vital signs from facial ROI.
        
        Args:
            frame: Current frame
            metadata: Frame metadata with face detections
            
        Returns:
            VitalSignsEvent if vital signs extracted, None otherwise
        """
        if not self.enabled:
            return None
        
        self.frame_count += 1
        
        # Check if we have person detections with face
        if not metadata.detections:
            return None
        
        detection = metadata.detections[0]
        if detection.face_bbox is None:
            return None
        
        face_bbox = detection.face_bbox
        
        # Extract face ROI
        x1, y1, x2, y2 = int(face_bbox.x1), int(face_bbox.y1), int(face_bbox.x2), int(face_bbox.y2)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        face_roi = frame[y1:y2, x1:x2]
        
        # Add to buffer
        self.face_roi_buffer.append(face_roi)
        
        # Update only every N frames
        if self.frame_count - self.last_update_frame < self.update_interval:
            return None
        
        # Need full window for analysis
        if len(self.face_roi_buffer) < self.window_size:
            return None
        
        # Process rPPG signal
        vital_signs = self.rppg_processor.process(list(self.face_roi_buffer))
        
        if vital_signs is None:
            return None
        
        # Validate ranges
        hr_valid = self.hr_range[0] <= vital_signs["heart_rate"] <= self.hr_range[1]
        rr_valid = self.rr_range[0] <= vital_signs["respiratory_rate"] <= self.rr_range[1]
        quality_valid = vital_signs["signal_quality"] >= self.signal_quality_threshold
        
        if hr_valid and rr_valid and quality_valid:
            self.last_update_frame = self.frame_count
            
            return VitalSignsEvent(
                event_type="vital_signs",
                timestamp=metadata.timestamp,
                confidence=vital_signs["signal_quality"],
                agent_name=self.agent_name,
                frame_id=metadata.frame_id,
                heart_rate=vital_signs["heart_rate"],
                respiratory_rate=vital_signs["respiratory_rate"],
                signal_quality=vital_signs["signal_quality"],
                hr_confidence=vital_signs["hr_confidence"],
                rr_confidence=vital_signs["rr_confidence"],
            )
        
        return None
    
    def reset(self):
        """Reset agent state"""
        super().reset()
        self.face_roi_buffer.clear()
        self.rppg_processor.reset()
        self.last_update_frame = 0
