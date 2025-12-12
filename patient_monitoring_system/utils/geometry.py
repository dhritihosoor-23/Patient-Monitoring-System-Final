"""
Geometric utility functions for pose analysis.
"""

import numpy as np
from typing import List, Tuple
import sys
sys.path.append('..')
from schemas import BoundingBox, Keypoint


def compute_angle(p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> float:
    """
    Compute angle at p2 formed by p1-p2-p3.
    
    Args:
        p1, p2, p3: Points as (x, y) tuples
        
    Returns:
        Angle in degrees
    """
    v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
    v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
    
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angle = np.degrees(np.arccos(cos_angle))
    
    return angle


def compute_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Compute Euclidean distance between two points.
    
    Args:
        p1, p2: Points as (x, y) tuples
        
    Returns:
        Distance
    """
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def normalize_keypoints(keypoints: List[Keypoint], width: int, height: int) -> List[Keypoint]:
    """
    Normalize keypoint coordinates to [0, 1] range.
    
    Args:
        keypoints: List of Keypoint objects
        width: Frame width
        height: Frame height
        
    Returns:
        List of normalized Keypoint objects
    """
    normalized = []
    
    for kp in keypoints:
        normalized.append(Keypoint(
            x=kp.x / width,
            y=kp.y / height,
            z=kp.z,
            confidence=kp.confidence,
            visibility=kp.visibility,
        ))
    
    return normalized


def compute_iou(bbox1: BoundingBox, bbox2: BoundingBox) -> float:
    """
    Compute Intersection over Union (IoU) between two bounding boxes.
    
    Args:
        bbox1, bbox2: BoundingBox objects
        
    Returns:
        IoU value [0, 1]
    """
    x1 = max(bbox1.x1, bbox2.x1)
    y1 = max(bbox1.y1, bbox2.y1)
    x2 = min(bbox1.x2, bbox2.x2)
    y2 = min(bbox1.y2, bbox2.y2)
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (bbox1.x2 - bbox1.x1) * (bbox1.y2 - bbox1.y1)
    area2 = (bbox2.x2 - bbox2.x1) * (bbox2.y2 - bbox2.y1)
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0


def point_in_bbox(point: Tuple[float, float], bbox: BoundingBox) -> bool:
    """
    Check if a point is inside a bounding box.
    
    Args:
        point: Point as (x, y) tuple
        bbox: BoundingBox object
        
    Returns:
        True if point is inside bbox
    """
    x, y = point
    return bbox.x1 <= x <= bbox.x2 and bbox.y1 <= y <= bbox.y2


def get_bbox_center(bbox: BoundingBox) -> Tuple[float, float]:
    """Get center point of bounding box"""
    return ((bbox.x1 + bbox.x2) / 2, (bbox.y1 + bbox.y2) / 2)


def get_bbox_area(bbox: BoundingBox) -> float:
    """Get area of bounding box"""
    return (bbox.x2 - bbox.x1) * (bbox.y2 - bbox.y1)


def expand_bbox(bbox: BoundingBox, factor: float = 1.2) -> BoundingBox:
    """
    Expand bounding box by a factor.
    
    Args:
        bbox: BoundingBox object
        factor: Expansion factor (1.0 = no change, 1.2 = 20% larger)
        
    Returns:
        Expanded BoundingBox
    """
    width = bbox.x2 - bbox.x1
    height = bbox.y2 - bbox.y1
    
    center_x, center_y = get_bbox_center(bbox)
    
    new_width = width * factor
    new_height = height * factor
    
    return BoundingBox(
        x1=center_x - new_width / 2,
        y1=center_y - new_height / 2,
        x2=center_x + new_width / 2,
        y2=center_y + new_height / 2,
        confidence=bbox.confidence,
    )
