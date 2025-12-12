"""
Orchestrator Agent
Fuses outputs from all agents and applies intelligent rules for consolidated alerts.
"""

import numpy as np
from typing import List, Optional, Dict
import time
import uuid

import sys
sys.path.append('..')

from schemas import BaseEvent, ConsolidatedAlert
from config import ORCHESTRATOR_CONFIG, is_nighttime


class Orchestrator:
    """
    Orchestrates multiple agents and fuses their outputs.
    
    Responsibilities:
    - Collect events from all agents
    - Apply fusion rules
    - Remove duplicates
    - Prioritize alerts
    - Generate consolidated alerts
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize orchestrator.
        
        Args:
            config: Configuration dictionary (uses ORCHESTRATOR_CONFIG if None)
        """
        self.config = config or ORCHESTRATOR_CONFIG
        self.alert_levels = self.config.get("alert_levels", ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.deduplication_window = self.config.get("deduplication_window", 5)
        self.rules = self.config.get("rules", {})
        
        # Event history for deduplication
        self.recent_alerts = []
        self.event_buffer = []
        
    def process_events(self, events: List[BaseEvent]) -> List[ConsolidatedAlert]:
        """
        Process events from agents and generate consolidated alerts.
        
        Args:
            events: List of events from various agents
            
        Returns:
            List of ConsolidatedAlert objects
        """
        if not events:
            return []
        
        # Add to event buffer
        self.event_buffer.extend(events)
        
        # Apply fusion rules
        consolidated_alerts = []
        
        # Check each rule
        for rule_name, rule_config in self.rules.items():
            alert = self._apply_rule(rule_name, rule_config, events)
            if alert:
                # Check for duplicates
                if not self._is_duplicate(alert):
                    consolidated_alerts.append(alert)
                    self._add_to_recent(alert)
        
        # Generate individual alerts for events not covered by rules
        for event in events:
            if not self._is_covered_by_rules(event):
                alert = self._create_individual_alert(event)
                if alert and not self._is_duplicate(alert):
                    consolidated_alerts.append(alert)
                    self._add_to_recent(alert)
        
        # Clean up old alerts from recent history
        self._cleanup_recent_alerts()
        
        return consolidated_alerts
    
    def _apply_rule(self, rule_name: str, rule_config: Dict, events: List[BaseEvent]) -> Optional[ConsolidatedAlert]:
        """Apply a specific fusion rule"""
        conditions = rule_config.get("conditions", [])
        level = rule_config.get("level", "INFO")
        message = rule_config.get("message", "")
        
        # Check if all conditions are met
        matched_events = []
        
        for condition in conditions:
            # Check for specific event types or conditions
            if condition == "fall_detected":
                fall_events = [e for e in events if e.event_type == "fall_detection"]
                if fall_events:
                    matched_events.extend(fall_events)
                else:
                    return None
            
            elif condition == "low_heart_rate":
                vital_events = [e for e in events if e.event_type == "vital_signs"]
                if vital_events:
                    for ve in vital_events:
                        if ve.heart_rate and ve.heart_rate < 50:
                            matched_events.append(ve)
                            break
                    else:
                        return None
                else:
                    return None
            
            elif condition == "bed_exit":
                bed_events = [e for e in events if e.event_type == "bed_exit"]
                if bed_events:
                    matched_events.extend(bed_events)
                else:
                    return None
            
            elif condition == "nighttime":
                if not is_nighttime():
                    return None
            
            elif condition == "immobility_alert":
                immobility_events = [e for e in events if e.event_type == "immobility"]
                if immobility_events:
                    matched_events.extend(immobility_events)
                else:
                    return None
            
            elif condition == "seizure":
                seizure_events = [e for e in events if e.event_type == "seizure_detection"]
                if seizure_events:
                    matched_events.extend(seizure_events)
                else:
                    return None
        
        # All conditions met, create consolidated alert
        if matched_events:
            alert_id = str(uuid.uuid4())
            timestamp = time.time()
            
            return ConsolidatedAlert(
                alert_id=alert_id,
                level=level,
                message=message,
                timestamp=timestamp,
                events=matched_events,
                metadata={"rule": rule_name},
            )
        
        return None
    
    def _create_individual_alert(self, event: BaseEvent) -> Optional[ConsolidatedAlert]:
        """Create alert for individual event"""
        # Map event types to alert levels
        level_map = {
            "fall_detection": "HIGH",
            "seizure_detection": "CRITICAL",
            "bed_exit": "MEDIUM",
            "immobility": "MEDIUM",
            "emotion_detection": "INFO",
            "vital_signs": "INFO",
        }
        
        level = level_map.get(event.event_type, "INFO")
        
        # Generate message
        message_map = {
            "fall_detection": f"Fall detected: {event.fall_type if hasattr(event, 'fall_type') else 'unknown'}",
            "seizure_detection": "Seizure activity detected",
            "bed_exit": f"Bed exit: {event.state if hasattr(event, 'state') else 'unknown'}",
            "immobility": f"Immobility detected: {event.risk_level if hasattr(event, 'risk_level') else 'unknown'} risk",
            "emotion_detection": f"Emotion: {event.emotion if hasattr(event, 'emotion') else 'unknown'}",
            "vital_signs": f"HR: {event.heart_rate if hasattr(event, 'heart_rate') else 'N/A'} bpm, RR: {event.respiratory_rate if hasattr(event, 'respiratory_rate') else 'N/A'}",
        }
        
        message = message_map.get(event.event_type, f"Event: {event.event_type}")
        
        alert_id = str(uuid.uuid4())
        
        return ConsolidatedAlert(
            alert_id=alert_id,
            level=level,
            message=message,
            timestamp=event.timestamp,
            events=[event],
            metadata={"source": event.agent_name},
        )
    
    def _is_covered_by_rules(self, event: BaseEvent) -> bool:
        """Check if event is already covered by fusion rules"""
        # For simplicity, only emotion and vital signs are not covered by rules
        return event.event_type not in ["emotion_detection", "vital_signs"]
    
    def _is_duplicate(self, alert: ConsolidatedAlert) -> bool:
        """Check if alert is duplicate of recent alert"""
        current_time = time.time()
        
        for recent_alert in self.recent_alerts:
            # Check if within deduplication window
            if current_time - recent_alert.timestamp < self.deduplication_window:
                # Check if same message
                if recent_alert.message == alert.message:
                    return True
        
        return False
    
    def _add_to_recent(self, alert: ConsolidatedAlert):
        """Add alert to recent history"""
        self.recent_alerts.append(alert)
    
    def _cleanup_recent_alerts(self):
        """Remove old alerts from recent history"""
        current_time = time.time()
        self.recent_alerts = [
            alert for alert in self.recent_alerts
            if current_time - alert.timestamp < self.deduplication_window * 2
        ]
    
    def reset(self):
        """Reset orchestrator state"""
        self.recent_alerts = []
        self.event_buffer = []
