"""
Emotion Detection Agent
Classifies facial expressions into 7 basic emotions and computes valence-arousal.
"""

import numpy as np
from typing import Optional
import cv2
import time

import sys
sys.path.append('..')

from core.base_agent import BaseAgent
from schemas import EmotionDetectionEvent, FrameMetadata


class EmotionDetectionAgent(BaseAgent):
    """
    Detects emotions from facial expressions.
    
    Uses a simple rule-based approach as placeholder.
    In production, replace with trained CNN model (FER, ResNet, etc.)
    """
    
    def __init__(self, config: dict):
        super().__init__("emotion_detection", config)
        
        self.emotions = config.get("emotions", [
            "happy", "sad", "angry", "fear", "disgust", "surprise", "neutral"
        ])
        self.confidence_threshold = config.get("confidence_threshold", 0.6)
        self.face_crop_size = config.get("face_crop_size", (224, 224))
        self.update_interval = config.get("update_interval", 5)
        
        self.last_emotion = None
        self.last_update_frame = 0
        
        # Placeholder: In production, load trained model
        # self.model = self._load_emotion_model()
        
    def detect(self, frame: np.ndarray, metadata: FrameMetadata) -> Optional[EmotionDetectionEvent]:
        """
        Detect emotion from facial expression.
        
        Args:
            frame: Current frame
            metadata: Frame metadata with face detections
            
        Returns:
            EmotionDetectionEvent if emotion detected, None otherwise
        """
        if not self.enabled:
            return None
        
        self.frame_count += 1
        
        # Update only every N frames to reduce computation
        if self.frame_count - self.last_update_frame < self.update_interval:
            return None
        
        # Check if we have person detections with face
        if not metadata.detections:
            return None
        
        detection = metadata.detections[0]
        if detection.face_bbox is None:
            return None
        
        face_bbox = detection.face_bbox
        
        # Crop face region
        x1, y1, x2, y2 = int(face_bbox.x1), int(face_bbox.y1), int(face_bbox.x2), int(face_bbox.y2)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        face_crop = frame[y1:y2, x1:x2]
        
        # Classify emotion
        emotion_result = self._classify_emotion(face_crop)
        
        if emotion_result["confidence"] > self.confidence_threshold:
            self.last_update_frame = self.frame_count
            self.last_emotion = emotion_result["emotion"]
            
            return EmotionDetectionEvent(
                event_type="emotion_detection",
                timestamp=metadata.timestamp,
                confidence=emotion_result["confidence"],
                agent_name=self.agent_name,
                frame_id=metadata.frame_id,
                emotion=emotion_result["emotion"],
                valence=emotion_result["valence"],
                arousal=emotion_result["arousal"],
                face_bbox=face_bbox,
                emotion_probabilities=emotion_result["probabilities"],
            )
        
        return None
    
    def _classify_emotion(self, face_crop: np.ndarray) -> dict:
        """
        Classify emotion from face crop.
        
        PLACEHOLDER: This is a simple rule-based approach.
        In production, replace with trained CNN model.
        """
        # Resize face
        face_resized = cv2.resize(face_crop, self.face_crop_size)
        
        # Placeholder: Random emotion for demo
        # In production: face_features = self.model.predict(face_resized)
        
        # Simple brightness-based heuristic (very naive, for demo only)
        gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        # Map brightness to emotion (placeholder logic)
        if brightness > 150:
            emotion = "happy"
            valence = 0.8
            arousal = 0.6
        elif brightness > 120:
            emotion = "neutral"
            valence = 0.0
            arousal = 0.0
        elif brightness > 90:
            emotion = "sad"
            valence = -0.6
            arousal = -0.4
        else:
            emotion = "angry"
            valence = -0.7
            arousal = 0.7
        
        # Create probability distribution
        probabilities = {e: 0.1 for e in self.emotions}
        probabilities[emotion] = 0.7
        
        return {
            "emotion": emotion,
            "confidence": 0.7,
            "valence": valence,
            "arousal": arousal,
            "probabilities": probabilities,
        }
    
    def _load_emotion_model(self):
        """
        Load pre-trained emotion classification model.
        
        Placeholder for production implementation.
        Use models like:
        - FER2013 trained CNN
        - ResNet/MobileNet fine-tuned on emotion datasets
        - EfficientNet for better accuracy
        """
        # Example:
        # import torch
        # model = torch.load(self.config.get("model_path"))
        # model.eval()
        # return model
        pass
    
    def reset(self):
        """Reset agent state"""
        super().reset()
        self.last_emotion = None
        self.last_update_frame = 0
