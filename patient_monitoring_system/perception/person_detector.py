"""
Person detection using YOLOv8.
Detects persons in frames and returns bounding boxes.
"""

import numpy as np
from typing import List, Optional
import cv2

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Person detection will not work.")

from schemas import BoundingBox


class PersonDetector:
    """
    YOLOv8-based person detector.
    Detects persons in frames and returns bounding boxes with confidence scores.
    """
    
    def __init__(self, config: dict):
        """
        Initialize person detector.
        
        Args:
            config: Configuration dictionary with model_name, confidence_threshold, etc.
        """
        self.config = config
        self.model = None
        self.confidence_threshold = config.get("confidence_threshold", 0.5)
        self.iou_threshold = config.get("iou_threshold", 0.45)
        self.device = config.get("device", "cpu")
        
        if YOLO_AVAILABLE:
            self._load_model()
        
    def _load_model(self):
        """Load YOLOv8 model safely.
        Recent PyTorch releases set ``weights_only=True`` for ``torch.load`` which
        prevents Ultralytics checkpoints from being deserialized. We explicitly
        allow the required globals before invoking ``YOLO``.
        """
        try:
            import torch
            # Allow Ultralytics DetectionModel class during deserialization
            try:
                from ultralytics.nn.tasks import DetectionModel
                torch.serialization.add_safe_globals([DetectionModel])
            except Exception:
                pass

            model_name = self.config.get("model_name", "yolov8n.pt")
            self.model = YOLO(model_name)
            self.model.to(self.device)
            print(f"✓ YOLOv8 model loaded: {model_name} on {self.device}")
        except Exception as e:
            print(f"Error loading YOLOv8 model: {e}")
            # Attempt to re‑download the model and retry once
            try:
                from ultralytics import YOLO
                print("Attempting to re‑download YOLOv8 model …")
                self.model = YOLO("yolov8n.pt")
                self.model.to(self.device)
                print(f"✓ YOLOv8 model re‑downloaded and loaded on {self.device}")
            except Exception as e2:
                print(f"Failed to download YOLOv8 model: {e2}")
                self.model = None
    
    def detect(self, frame: np.ndarray) -> List[BoundingBox]:
        """
        Detect persons in frame.
        
        Args:
            frame: RGB frame as numpy array (H, W, 3)
            
        Returns:
            List of BoundingBox objects for detected persons
        """
        if self.model is None:
            return []
        
        try:
            # Run inference
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                classes=[0],  # 0 = person class in COCO
                verbose=False,
            )
            
            detections = []
            
            # Process results
            if len(results) > 0:
                boxes = results[0].boxes
                
                for box in boxes:
                    # Get box coordinates and confidence
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    
                    bbox = BoundingBox(
                        x1=float(x1),
                        y1=float(y1),
                        x2=float(x2),
                        y2=float(y2),
                        confidence=conf
                    )
                    detections.append(bbox)
            
            return detections
            
        except Exception as e:
            print(f"Error in person detection: {e}")
            return []
    
    def visualize(self, frame: np.ndarray, detections: List[BoundingBox]) -> np.ndarray:
        """
        Draw bounding boxes on frame.
        
        Args:
            frame: RGB frame
            detections: List of BoundingBox objects
            
        Returns:
            Frame with drawn bounding boxes
        """
        vis_frame = frame.copy()
        
        for bbox in detections:
            x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)
            
            # Draw rectangle
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw confidence
            label = f"Person: {bbox.confidence:.2f}"
            cv2.putText(
                vis_frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )
        
        return vis_frame
