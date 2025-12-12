"""
Face detection using MediaPipe Face Detection.
Extracts facial regions for emotion and vital signs analysis.
"""

import numpy as np
from typing import List, Optional
import cv2

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: mediapipe not installed. Face detection will not work.")

from schemas import BoundingBox


class FaceDetector:
    """
    MediaPipe Face Detection.
    Detects faces and returns bounding boxes.
    """
    
    def __init__(self, config: dict):
        """
        Initialize face detector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.face_detection = None
        
        if MEDIAPIPE_AVAILABLE:
            self._init_mediapipe()
    
    def _init_mediapipe(self):
        """Initialize MediaPipe Face Detection"""
        try:
            mp_face_detection = mp.solutions.face_detection
            self.face_detection = mp_face_detection.FaceDetection(
                model_selection=self.config.get("model_selection", 0),
                min_detection_confidence=self.config.get("min_detection_confidence", 0.5),
            )
            print("✓ MediaPipe Face Detection initialized")
        except Exception as e:
            print(f"Error initializing MediaPipe Face Detection: {e}")
            self.face_detection = None
    
    def detect(self, frame: np.ndarray, bbox: Optional[BoundingBox] = None) -> List[BoundingBox]:
        """
        Detect faces in frame or person crop.
        
        Args:
            frame: RGB frame as numpy array (H, W, 3)
            bbox: Optional bounding box to crop person region
            
        Returns:
            List of BoundingBox objects for detected faces
        """
        if self.face_detection is None:
            return []
        
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
            results = self.face_detection.process(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
            
            if results.detections is None:
                return []
            
            # Extract face bounding boxes
            faces = []
            h, w = crop.shape[:2]
            
            for detection in results.detections:
                bbox_data = detection.location_data.relative_bounding_box
                
                # Convert normalized coordinates to absolute
                face_x1 = bbox_data.xmin * w + x1
                face_y1 = bbox_data.ymin * h + y1
                face_w = bbox_data.width * w
                face_h = bbox_data.height * h
                
                face_bbox = BoundingBox(
                    x1=face_x1,
                    y1=face_y1,
                    x2=face_x1 + face_w,
                    y2=face_y1 + face_h,
                    confidence=detection.score[0],
                )
                faces.append(face_bbox)
            
            return faces
            
        except Exception as e:
            print(f"Error in face detection: {e}")
            return []
    
    def visualize(self, frame: np.ndarray, faces: List[BoundingBox]) -> np.ndarray:
        """
        Draw face bounding boxes on frame.
        
        Args:
            frame: RGB frame
            faces: List of BoundingBox objects
            
        Returns:
            Frame with drawn bounding boxes
        """
        vis_frame = frame.copy()
        
        for face_bbox in faces:
            x1, y1, x2, y2 = int(face_bbox.x1), int(face_bbox.y1), int(face_bbox.x2), int(face_bbox.y2)
            
            # Draw rectangle
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
            
            # Draw confidence
            label = f"Face: {face_bbox.confidence:.2f}"
            cv2.putText(
                vis_frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 0),
                2
            )
        
        return vis_frame
    
    def __del__(self):
        """Cleanup MediaPipe resources"""
        if self.face_detection is not None:
            self.face_detection.close()
