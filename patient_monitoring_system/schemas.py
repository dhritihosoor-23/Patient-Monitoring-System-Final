"""
Event schemas and data structures for inter-agent communication.
Defines the structure of events emitted by each agent.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json


@dataclass
class BoundingBox:
    """Bounding box representation"""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    @property
    def area(self) -> float:
        return (self.x2 - self.x1) * (self.y2 - self.y1)


@dataclass
class Keypoint:
    """Single keypoint with coordinates and confidence"""
    x: float
    y: float
    z: float = 0.0
    confidence: float = 1.0
    visibility: float = 1.0


@dataclass
class PoseData:
    """Pose estimation data with 33 keypoints (MediaPipe format)"""
    keypoints: List[Keypoint]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "keypoints": [asdict(kp) for kp in self.keypoints],
            "timestamp": self.timestamp,
        }
    
    def get_keypoint_array(self) -> List[List[float]]:
        """Returns keypoints as flat array [x1, y1, z1, x2, y2, z2, ...]"""
        return [[kp.x, kp.y, kp.z] for kp in self.keypoints]


@dataclass
class BaseEvent:
    """Base event class for all agent outputs"""
    event_type: str
    timestamp: float
    confidence: float
    agent_name: str
    frame_id: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class FallDetectionEvent(BaseEvent):
    """Fall detection event"""
    fall_type: str  # "fall", "near_fall", "lying", "abnormal_collapse"
    bbox: Optional[BoundingBox] = None
    pose_vector: Optional[List[float]] = None
    torso_angle: Optional[float] = None
    hip_height: Optional[float] = None
    vertical_velocity: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if self.bbox:
            data["bbox"] = self.bbox.to_dict()
        return data


@dataclass
class EmotionDetectionEvent(BaseEvent):
    """Emotion detection event"""
    emotion: str  # "happy", "sad", "angry", "fear", "disgust", "surprise", "neutral"
    valence: float  # -1 (negative) to +1 (positive)
    arousal: float  # -1 (calm) to +1 (excited)
    face_bbox: Optional[BoundingBox] = None
    emotion_probabilities: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if self.face_bbox:
            data["face_bbox"] = self.face_bbox.to_dict()
        return data


@dataclass
class VitalSignsEvent(BaseEvent):
    """Vital signs (rPPG) event"""
    heart_rate: Optional[float] = None  # bpm
    respiratory_rate: Optional[float] = None  # breaths per minute
    signal_quality: float = 0.0  # 0-1
    hr_confidence: float = 0.0
    rr_confidence: float = 0.0
    
    def is_valid(self) -> bool:
        """Check if vital signs are within valid ranges"""
        hr_valid = self.heart_rate and 40 <= self.heart_rate <= 180
        rr_valid = self.respiratory_rate and 8 <= self.respiratory_rate <= 30
        return hr_valid and rr_valid and self.signal_quality > 0.6


@dataclass
class BedExitEvent(BaseEvent):
    """Bed exit detection event"""
    state: str  # "IN_BED", "SITTING_UP", "STANDING", "OUT_OF_BED"
    previous_state: Optional[str] = None
    transition: bool = False
    duration_in_state: float = 0.0  # seconds
    bed_region: Optional[BoundingBox] = None
    person_bbox: Optional[BoundingBox] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if self.bed_region:
            data["bed_region"] = self.bed_region.to_dict()
        if self.person_bbox:
            data["person_bbox"] = self.person_bbox.to_dict()
        return data


@dataclass
class ImmobilityEvent(BaseEvent):
    """Immobility/pressure ulcer risk event"""
    immobility_duration: float  # seconds
    last_movement_time: float
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    posture: Optional[str] = None  # "supine", "prone", "left_side", "right_side"
    movement_magnitude: float = 0.0
    posture_change_count: int = 0
    
    def is_alert_worthy(self) -> bool:
        """Check if immobility duration warrants an alert"""
        return self.immobility_duration > 7200  # 2 hours


@dataclass
class SeizureDetectionEvent(BaseEvent):
    """Seizure detection event"""
    seizure_detected: bool
    motion_frequency: float  # Hz
    affected_limbs: List[str]  # e.g., ["left_arm", "right_leg"]
    duration: float  # seconds
    magnitude: float
    
    def is_critical(self) -> bool:
        """Check if seizure is critical"""
        return self.seizure_detected and self.duration > 5


@dataclass
class PersonDetection:
    """Person detection result"""
    track_id: int
    bbox: BoundingBox
    confidence: float
    pose: Optional[PoseData] = None
    face_bbox: Optional[BoundingBox] = None


@dataclass
class FrameMetadata:
    """Metadata for each processed frame"""
    frame_id: int
    timestamp: float
    width: int
    height: int
    fps: float
    detections: List[PersonDetection] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "detections": [
                {
                    "track_id": d.track_id,
                    "bbox": d.bbox.to_dict(),
                    "confidence": d.confidence,
                }
                for d in self.detections
            ],
        }


@dataclass
class ConsolidatedAlert:
    """Consolidated alert from orchestrator"""
    alert_id: str
    level: str  # "INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"
    message: str
    timestamp: float
    events: List[BaseEvent]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "level": self.level,
            "message": self.message,
            "timestamp": self.timestamp,
            "events": [e.to_dict() for e in self.events],
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# Event type mapping for deserialization
EVENT_TYPE_MAP = {
    "fall_detection": FallDetectionEvent,
    "emotion_detection": EmotionDetectionEvent,
    "vital_signs": VitalSignsEvent,
    "bed_exit": BedExitEvent,
    "immobility": ImmobilityEvent,
    "seizure_detection": SeizureDetectionEvent,
}


def create_event_from_dict(data: Dict[str, Any]) -> BaseEvent:
    """Factory function to create event from dictionary"""
    event_type = data.get("event_type")
    event_class = EVENT_TYPE_MAP.get(event_type, BaseEvent)
    return event_class(**data)
