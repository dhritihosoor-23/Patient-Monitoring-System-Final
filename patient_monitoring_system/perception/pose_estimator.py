"""
Pose estimation using MediaPipe Pose.
Extracts 33 body keypoints with confidence scores.
"""

import numpy as np
from typing import Optional, List
import cv2

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: mediapipe not installed. Pose estimation will not work.")

from schemas import PoseData, Keypoint, BoundingBox


class PoseEstimator:
    """
    MediaPipe Pose estimator.
    Extracts 33 body keypoints from person crops.
    """
    
    def __init__(self, config: dict):
        """
        Initialize pose estimator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.pose = None
        
        if MEDIAPIPE_AVAILABLE:
            self._init_mediapipe()
    
    def _init_mediapipe(self):
        """Initialize MediaPipe Pose"""
        try:
            mp_pose = mp.solutions.pose
            self.pose = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=self.config.get("model_complexity", 1),
                smooth_landmarks=True,
                enable_segmentation=self.config.get("enable_segmentation", False),
                min_detection_confidence=self.config.get("min_detection_confidence", 0.5),
                min_tracking_confidence=self.config.get("min_tracking_confidence", 0.5),
            )
            print("✓ MediaPipe Pose initialized")
        except Exception as e:
            print(f"Error initializing MediaPipe Pose: {e}")
            self.pose = None
    
    def estimate(self, frame: np.ndarray, bbox: Optional[BoundingBox] = None) -> Optional[PoseData]:
        """
        Estimate pose from frame or person crop.
        
        Args:
            frame: RGB frame as numpy array (H, W, 3)
            bbox: Optional bounding box to crop person region
            
        Returns:
            PoseData object with 33 keypoints, or None if pose not detected
        """
        if self.pose is None:
            return None
        
        try:
            # Crop to person region if bbox provided
            if bbox is not None:
                x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
                crop = frame[y1:y2, x1:x2]
            else:
                crop = frame
                x1, y1 = 0, 0
            
            # Process with MediaPipe
            results = self.pose.process(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
            
            if results.pose_landmarks is None:
                return None
            
            # Extract keypoints
            keypoints = []
            h, w = crop.shape[:2]
            
            for landmark in results.pose_landmarks.landmark:
                # Convert normalized coordinates to absolute (relative to crop)
                x = landmark.x * w + x1
                y = landmark.y * h + y1
                z = landmark.z  # Depth (relative to hips)
                
                keypoint = Keypoint(
                    x=x,
                    y=y,
                    z=z,
                    confidence=landmark.visibility,
                    visibility=landmark.visibility,
                )
                keypoints.append(keypoint)
            
            import time
            pose_data = PoseData(
                keypoints=keypoints,
                timestamp=time.time(),
            )
            
            return pose_data
            
        except Exception as e:
            print(f"Error in pose estimation: {e}")
            return None
    
    def get_keypoint_names(self) -> List[str]:
        """Get names of MediaPipe pose keypoints"""
        return [
            "nose", "left_eye_inner", "left_eye", "left_eye_outer",
            "right_eye_inner", "right_eye", "right_eye_outer",
            "left_ear", "right_ear", "mouth_left", "mouth_right",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_pinky", "right_pinky",
            "left_index", "right_index", "left_thumb", "right_thumb",
            "left_hip", "right_hip", "left_knee", "right_knee",
            "left_ankle", "right_ankle", "left_heel", "right_heel",
            "left_foot_index", "right_foot_index"
        ]
    
    def visualize(self, frame: np.ndarray, pose_data: PoseData) -> np.ndarray:
        """
        Draw pose keypoints on frame.
        
        Args:
            frame: RGB frame
            pose_data: PoseData object
            
        Returns:
            Frame with drawn keypoints and skeleton
        """
        vis_frame = frame.copy()
        
        # Define skeleton connections
        connections = [
            (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),  # Left arm
            (12, 14), (14, 16), (16, 18), (16, 20), (16, 22),  # Right arm
            (11, 23), (12, 24), (23, 24),  # Torso
            (23, 25), (25, 27), (27, 29), (27, 31),  # Left leg
            (24, 26), (26, 28), (28, 30), (28, 32),  # Right leg
        ]
        
        # Draw connections
        for start_idx, end_idx in connections:
            if start_idx < len(pose_data.keypoints) and end_idx < len(pose_data.keypoints):
                start_kp = pose_data.keypoints[start_idx]
                end_kp = pose_data.keypoints[end_idx]
                
                if start_kp.visibility > 0.5 and end_kp.visibility > 0.5:
                    cv2.line(
                        vis_frame,
                        (int(start_kp.x), int(start_kp.y)),
                        (int(end_kp.x), int(end_kp.y)),
                        (255, 0, 0),
                        2
                    )
        
        # Draw keypoints
        for kp in pose_data.keypoints:
            if kp.visibility > 0.5:
                cv2.circle(
                    vis_frame,
                    (int(kp.x), int(kp.y)),
                    4,
                    (0, 255, 0),
                    -1
                )
        
        return vis_frame
    
    def __del__(self):
        """Cleanup MediaPipe resources"""
        if self.pose is not None:
            self.pose.close()
