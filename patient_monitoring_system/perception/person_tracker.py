"""
Person tracking using DeepSORT algorithm.
Maintains consistent IDs for detected persons across frames.
"""

import numpy as np
from typing import List, Dict
from collections import defaultdict

try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
    DEEPSORT_AVAILABLE = True
except ImportError:
    DEEPSORT_AVAILABLE = False
    print("Warning: deep-sort-realtime not installed. Tracking will use simple IoU matching.")

from schemas import BoundingBox


class PersonTracker:
    """
    Person tracker using DeepSORT or simple IoU-based tracking.
    Maintains consistent track IDs across frames.
    """
    
    def __init__(self, config: dict):
        """
        Initialize tracker.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.tracker = None
        self.max_age = config.get("max_age", 30)
        self.min_hits = config.get("min_hits", 3)
        self.iou_threshold = config.get("iou_threshold", 0.3)
        
        # Fallback simple tracker state
        self.next_id = 0
        self.tracks = {}
        self.track_ages = defaultdict(int)
        
        if DEEPSORT_AVAILABLE:
            self._init_deepsort()
        else:
            print("Using simple IoU-based tracking (install deep-sort-realtime for better tracking)")
    
    def _init_deepsort(self):
        """Initialize DeepSORT tracker"""
        try:
            self.tracker = DeepSort(
                max_age=self.max_age,
                n_init=self.min_hits,
                nms_max_overlap=1.0,
                max_cosine_distance=0.3,
                nn_budget=None,
                override_track_class=None,
                embedder="mobilenet",
                half=True,
                bgr=True,
                embedder_gpu=False,
            )
            print("✓ DeepSORT tracker initialized")
        except Exception as e:
            print(f"Error initializing DeepSORT: {e}")
            self.tracker = None
    
    def update(self, frame: np.ndarray, detections: List[BoundingBox]) -> List[Dict]:
        """
        Update tracker with new detections.
        
        Args:
            frame: Current frame (needed for DeepSORT feature extraction)
            detections: List of BoundingBox objects
            
        Returns:
            List of tracked objects with format:
            [{"track_id": int, "bbox": BoundingBox, "confidence": float}, ...]
        """
        if self.tracker is not None:
            return self._update_deepsort(frame, detections)
        else:
            return self._update_simple(detections)
    
    def _update_deepsort(self, frame: np.ndarray, detections: List[BoundingBox]) -> List[Dict]:
        """Update using DeepSORT"""
        # Convert detections to DeepSORT format: ([x1, y1, w, h], confidence, class)
        raw_detections = []
        for bbox in detections:
            x1, y1, x2, y2 = bbox.x1, bbox.y1, bbox.x2, bbox.y2
            w = x2 - x1
            h = y2 - y1
            raw_detections.append(([x1, y1, w, h], bbox.confidence, 'person'))
        
        # Update tracker
        tracks = self.tracker.update_tracks(raw_detections, frame=frame)
        
        # Convert to our format
        tracked_objects = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            
            track_id = track.track_id
            ltrb = track.to_ltrb()
            
            bbox = BoundingBox(
                x1=float(ltrb[0]),
                y1=float(ltrb[1]),
                x2=float(ltrb[2]),
                y2=float(ltrb[3]),
                confidence=track.get_det_conf() if hasattr(track, 'get_det_conf') else 1.0
            )
            
            tracked_objects.append({
                "track_id": track_id,
                "bbox": bbox,
                "confidence": bbox.confidence,
            })
        
        return tracked_objects
    
    def _update_simple(self, detections: List[BoundingBox]) -> List[Dict]:
        """Simple IoU-based tracking fallback"""
        tracked_objects = []
        
        # Match detections to existing tracks using IoU
        matched_tracks = {}
        unmatched_detections = []
        
        for det in detections:
            best_iou = 0
            best_track_id = None
            
            for track_id, track_bbox in self.tracks.items():
                iou = self._compute_iou(det, track_bbox)
                if iou > best_iou and iou > self.iou_threshold:
                    best_iou = iou
                    best_track_id = track_id
            
            if best_track_id is not None:
                matched_tracks[best_track_id] = det
                self.track_ages[best_track_id] = 0
            else:
                unmatched_detections.append(det)
        
        # Update matched tracks
        for track_id, bbox in matched_tracks.items():
            self.tracks[track_id] = bbox
            tracked_objects.append({
                "track_id": track_id,
                "bbox": bbox,
                "confidence": bbox.confidence,
            })
        
        # Create new tracks for unmatched detections
        for det in unmatched_detections:
            track_id = self.next_id
            self.next_id += 1
            self.tracks[track_id] = det
            self.track_ages[track_id] = 0
            tracked_objects.append({
                "track_id": track_id,
                "bbox": det,
                "confidence": det.confidence,
            })
        
        # Age out old tracks
        tracks_to_remove = []
        for track_id in self.tracks:
            if track_id not in matched_tracks:
                self.track_ages[track_id] += 1
                if self.track_ages[track_id] > self.max_age:
                    tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            del self.tracks[track_id]
            del self.track_ages[track_id]
        
        return tracked_objects
    
    def _compute_iou(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Compute IoU between two bounding boxes"""
        x1 = max(bbox1.x1, bbox2.x1)
        y1 = max(bbox1.y1, bbox2.y1)
        x2 = min(bbox1.x2, bbox2.x2)
        y2 = min(bbox1.y2, bbox2.y2)
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (bbox1.x2 - bbox1.x1) * (bbox1.y2 - bbox1.y1)
        area2 = (bbox2.x2 - bbox2.x1) * (bbox2.y2 - bbox2.y1)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def reset(self):
        """Reset tracker state"""
        if self.tracker is not None:
            self.tracker = None
            self._init_deepsort()
        else:
            self.next_id = 0
            self.tracks = {}
            self.track_ages = defaultdict(int)
