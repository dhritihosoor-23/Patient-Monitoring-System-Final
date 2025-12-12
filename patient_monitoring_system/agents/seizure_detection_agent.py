"""
Seizure Detection Agent
Detects high-frequency repetitive limb movements indicative of seizures.
"""

import numpy as np
from typing import Optional, List
import time
from scipy import signal as scipy_signal

import sys
sys.path.append('..')

from core.base_agent import BaseAgent
from schemas import SeizureDetectionEvent, FrameMetadata
from utils.temporal_buffer import TemporalBuffer


class SeizureDetectionAgent(BaseAgent):
    """
    Detects seizure activity from repetitive limb movements.
    
    Uses FFT analysis on keypoint trajectories to detect high-frequency patterns.
    """
    
    def __init__(self, config: dict):
        super().__init__("seizure_detection", config)
        
        self.frequency_range = config.get("frequency_range", (3, 10))  # Hz
        self.magnitude_threshold = config.get("magnitude_threshold", 0.3)
        self.duration_threshold = config.get("duration_threshold", 5)  # seconds
        self.confidence_threshold = config.get("confidence_threshold", 0.75)
        self.affected_limbs_min = config.get("affected_limbs_min", 2)
        
        # Buffer for temporal analysis (need ~5 seconds of data)
        self.buffer_size = 150  # 5 seconds at 30 fps
        self.pose_buffer = TemporalBuffer(maxlen=self.buffer_size)
        
        self.seizure_start_time = None
        self.last_event_time = 0
        self.event_cooldown = 10.0  # seconds
        
    def detect(self, frame: np.ndarray, metadata: FrameMetadata) -> Optional[SeizureDetectionEvent]:
        """
        Detect seizure events.
        
        Args:
            frame: Current frame
            metadata: Frame metadata with pose data
            
        Returns:
            SeizureDetectionEvent if seizure detected, None otherwise
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
        
        # Need full buffer for FFT analysis
        if len(self.pose_buffer) < self.buffer_size:
            return None
        
        # Cooldown to prevent duplicate events
        if time.time() - self.last_event_time < self.event_cooldown:
            return None
        
        # Analyze limb movements
        seizure_indicators = self._analyze_limb_movements()
        
        if seizure_indicators["seizure_detected"]:
            # Track seizure duration
            if self.seizure_start_time is None:
                self.seizure_start_time = time.time()
            
            duration = time.time() - self.seizure_start_time
            
            # Only alert if duration exceeds threshold
            if duration > self.duration_threshold:
                self.last_event_time = time.time()
                
                return SeizureDetectionEvent(
                    event_type="seizure_detection",
                    timestamp=metadata.timestamp,
                    confidence=seizure_indicators["confidence"],
                    agent_name=self.agent_name,
                    frame_id=metadata.frame_id,
                    seizure_detected=True,
                    motion_frequency=seizure_indicators["dominant_frequency"],
                    affected_limbs=seizure_indicators["affected_limbs"],
                    duration=duration,
                    magnitude=seizure_indicators["magnitude"],
                )
        else:
            # Reset seizure tracking
            self.seizure_start_time = None
        
        return None
    
    def _analyze_limb_movements(self) -> dict:
        """Analyze limb movements using FFT"""
        # Define limb keypoint indices
        limbs = {
            "left_arm": [11, 13, 15],  # shoulder, elbow, wrist
            "right_arm": [12, 14, 16],
            "left_leg": [23, 25, 27],  # hip, knee, ankle
            "right_leg": [24, 26, 28],
        }
        
        affected_limbs = []
        max_magnitude = 0.0
        dominant_frequency = 0.0
        
        for limb_name, keypoint_indices in limbs.items():
            # Extract trajectories for this limb
            trajectories = self._extract_trajectories(keypoint_indices)
            
            if trajectories is None:
                continue
            
            # Perform FFT analysis
            fft_result = self._fft_analysis(trajectories)
            
            if fft_result["is_seizure_pattern"]:
                affected_limbs.append(limb_name)
                max_magnitude = max(max_magnitude, fft_result["magnitude"])
                dominant_frequency = max(dominant_frequency, fft_result["frequency"])
        
        # Seizure detected if multiple limbs affected
        seizure_detected = len(affected_limbs) >= self.affected_limbs_min
        
        confidence = min(1.0, (len(affected_limbs) / 4.0) * (max_magnitude / self.magnitude_threshold))
        
        return {
            "seizure_detected": seizure_detected,
            "affected_limbs": affected_limbs,
            "magnitude": max_magnitude,
            "dominant_frequency": dominant_frequency,
            "confidence": confidence,
        }
    
    def _extract_trajectories(self, keypoint_indices: List[int]) -> Optional[np.ndarray]:
        """Extract position trajectories for keypoints"""
        trajectories = []
        
        for frame_data in self.pose_buffer.buffer:
            pose = frame_data["pose"]
            
            # Average position of keypoints in this limb
            positions = []
            for idx in keypoint_indices:
                if idx < len(pose.keypoints):
                    kp = pose.keypoints[idx]
                    if kp.visibility > 0.5:
                        positions.append([kp.x, kp.y])
            
            if positions:
                avg_pos = np.mean(positions, axis=0)
                trajectories.append(avg_pos)
            else:
                return None
        
        if len(trajectories) < self.buffer_size:
            return None
        
        return np.array(trajectories)
    
    def _fft_analysis(self, trajectories: np.ndarray) -> dict:
        """Perform FFT analysis on trajectories"""
        # Compute velocity (derivative of position)
        velocity = np.diff(trajectories, axis=0)
        velocity_magnitude = np.linalg.norm(velocity, axis=1)
        
        # Perform FFT
        fft_values = np.fft.fft(velocity_magnitude)
        fft_freq = np.fft.fftfreq(len(velocity_magnitude), d=1.0/30.0)  # 30 fps
        
        # Get positive frequencies only
        positive_freq_idx = fft_freq > 0
        fft_freq = fft_freq[positive_freq_idx]
        fft_magnitude = np.abs(fft_values[positive_freq_idx])
        
        # Find dominant frequency in seizure range
        seizure_range_mask = (fft_freq >= self.frequency_range[0]) & (fft_freq <= self.frequency_range[1])
        
        if not np.any(seizure_range_mask):
            return {
                "is_seizure_pattern": False,
                "frequency": 0.0,
                "magnitude": 0.0,
            }
        
        seizure_freq = fft_freq[seizure_range_mask]
        seizure_magnitude = fft_magnitude[seizure_range_mask]
        
        max_idx = np.argmax(seizure_magnitude)
        dominant_freq = seizure_freq[max_idx]
        max_magnitude = seizure_magnitude[max_idx]
        
        # Normalize magnitude
        normalized_magnitude = max_magnitude / (len(velocity_magnitude) / 2)
        
        is_seizure = normalized_magnitude > self.magnitude_threshold
        
        return {
            "is_seizure_pattern": is_seizure,
            "frequency": dominant_freq,
            "magnitude": normalized_magnitude,
        }
    
    def reset(self):
        """Reset agent state"""
        super().reset()
        self.pose_buffer.clear()
        self.seizure_start_time = None
        self.last_event_time = 0
