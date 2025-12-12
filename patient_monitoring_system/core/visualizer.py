"""
Visualization system for real-time overlay rendering.
"""

import cv2
import numpy as np
from typing import List, Optional
import time

import sys
sys.path.append('..')

from schemas import FrameMetadata, ConsolidatedAlert, PersonDetection
from perception.pose_estimator import PoseEstimator


class Visualizer:
    """
    Real-time visualization overlay.
    
    Renders:
    - Bounding boxes
    - Pose keypoints
    - Tracking IDs
    - Vital signs
    - Alerts
    """
    
    def __init__(self, config: dict):
        """
        Initialize visualizer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.show_bboxes = config.get("show_bboxes", True)
        self.show_keypoints = config.get("show_keypoints", True)
        self.show_tracking_id = config.get("show_tracking_id", True)
        self.show_vital_signs = config.get("show_vital_signs", True)
        self.show_alerts = config.get("show_alerts", True)
        self.alert_display_duration = config.get("alert_display_duration", 5)
        self.colors = config.get("colors", {})
        
        # Active alerts
        self.active_alerts = []
        
        # Pose visualizer
        self.pose_visualizer = PoseEstimator({})
    
    def render(self, frame: np.ndarray, metadata: FrameMetadata, 
               alerts: List[ConsolidatedAlert] = None,
               vital_signs: dict = None) -> np.ndarray:
        """
        Render visualization overlay on frame.
        
        Args:
            frame: Input frame
            metadata: Frame metadata with detections
            alerts: List of current alerts
            vital_signs: Dictionary with vital signs data
            
        Returns:
            Frame with overlay
        """
        vis_frame = frame.copy()
        
        # Add new alerts
        if alerts:
            for alert in alerts:
                self.active_alerts.append({
                    "alert": alert,
                    "timestamp": time.time(),
                })
        
        # Draw detections
        if metadata.detections:
            for detection in metadata.detections:
                vis_frame = self._draw_detection(vis_frame, detection)
        
        # Draw vital signs
        if self.show_vital_signs and vital_signs:
            vis_frame = self._draw_vital_signs(vis_frame, vital_signs)
        
        # Draw alerts
        if self.show_alerts:
            vis_frame = self._draw_alerts(vis_frame)
        
        # Draw FPS
        vis_frame = self._draw_fps(vis_frame, metadata.fps)
        
        # Cleanup old alerts
        self._cleanup_alerts()
        
        return vis_frame
    
    def _draw_detection(self, frame: np.ndarray, detection: PersonDetection) -> np.ndarray:
        """Draw person detection"""
        # Draw bounding box
        if self.show_bboxes:
            bbox = detection.bbox
            x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)
            
            color = self.colors.get("bbox", (0, 255, 0))
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw tracking ID
            if self.show_tracking_id:
                label = f"ID: {detection.track_id}"
                cv2.putText(frame, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Draw pose keypoints
        if self.show_keypoints and detection.pose:
            frame = self.pose_visualizer.visualize(frame, detection.pose)
        
        # Draw face bbox
        if detection.face_bbox:
            face = detection.face_bbox
            x1, y1, x2, y2 = int(face.x1), int(face.y1), int(face.x2), int(face.y2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        
        return frame
    
    def _draw_vital_signs(self, frame: np.ndarray, vital_signs: dict) -> np.ndarray:
        """Draw vital signs overlay"""
        hr = vital_signs.get("heart_rate", "N/A")
        rr = vital_signs.get("respiratory_rate", "N/A")
        quality = vital_signs.get("signal_quality", 0.0)
        
        # Draw panel
        panel_height = 100
        panel_width = 250
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (10 + panel_width, 10 + panel_height),
                     (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        
        # Draw text
        y_offset = 35
        cv2.putText(frame, "Vital Signs", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        y_offset += 25
        hr_text = f"HR: {hr if isinstance(hr, str) else f'{hr:.1f}'} bpm"
        cv2.putText(frame, hr_text, (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        y_offset += 25
        rr_text = f"RR: {rr if isinstance(rr, str) else f'{rr:.1f}'} /min"
        cv2.putText(frame, rr_text, (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        y_offset += 25
        quality_text = f"Quality: {quality:.2f}"
        color = (0, 255, 0) if quality > 0.7 else (0, 255, 255) if quality > 0.5 else (0, 0, 255)
        cv2.putText(frame, quality_text, (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame
    
    def _draw_alerts(self, frame: np.ndarray) -> np.ndarray:
        """Draw active alerts"""
        y_offset = frame.shape[0] - 30
        
        for alert_data in self.active_alerts:
            alert = alert_data["alert"]
            
            # Determine color based on level
            color_map = {
                "CRITICAL": self.colors.get("alert_critical", (0, 0, 255)),
                "HIGH": self.colors.get("alert_high", (0, 100, 255)),
                "MEDIUM": self.colors.get("alert_medium", (0, 255, 255)),
                "LOW": self.colors.get("alert_low", (0, 255, 0)),
                "INFO": (255, 255, 255),
            }
            color = color_map.get(alert.level, (255, 255, 255))
            
            # Draw alert message
            text = f"[{alert.level}] {alert.message}"
            cv2.putText(frame, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            y_offset -= 30
            
            if y_offset < 150:  # Don't overlap with vital signs
                break
        
        return frame
    
    def _draw_fps(self, frame: np.ndarray, fps: float) -> np.ndarray:
        """Draw FPS counter"""
        text = f"FPS: {fps:.1f}"
        cv2.putText(frame, text, (frame.shape[1] - 150, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return frame
    
    def _cleanup_alerts(self):
        """Remove old alerts"""
        current_time = time.time()
        self.active_alerts = [
            alert_data for alert_data in self.active_alerts
            if current_time - alert_data["timestamp"] < self.alert_display_duration
        ]
