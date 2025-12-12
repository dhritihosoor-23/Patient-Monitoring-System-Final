"""
Base agent interface for all monitoring agents.
All agents must inherit from this class and implement the detect() method.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import numpy as np
from schemas import BaseEvent, FrameMetadata


class BaseAgent(ABC):
    """
    Abstract base class for all monitoring agents.
    
    Each agent processes frames and metadata to detect specific events.
    Agents should be stateless where possible, or manage their own state internally.
    """
    
    def __init__(self, agent_name: str, config: Dict[str, Any]):
        """
        Initialize the agent.
        
        Args:
            agent_name: Unique identifier for this agent
            config: Configuration dictionary for this agent
        """
        self.agent_name = agent_name
        self.config = config
        self.enabled = True
        self.frame_count = 0
        
    @abstractmethod
    def detect(self, frame: np.ndarray, metadata: FrameMetadata) -> Optional[BaseEvent]:
        """
        Process a frame and detect events.
        
        Args:
            frame: RGB frame as numpy array (H, W, 3)
            metadata: Frame metadata including detections, pose, etc.
            
        Returns:
            Event object if an event is detected, None otherwise
        """
        pass
    
    def enable(self):
        """Enable this agent"""
        self.enabled = True
        
    def disable(self):
        """Disable this agent"""
        self.enabled = False
        
    def reset(self):
        """Reset agent state (override if agent maintains state)"""
        self.frame_count = 0
        
    def update_config(self, config: Dict[str, Any]):
        """Update agent configuration"""
        self.config.update(config)
        
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "agent_name": self.agent_name,
            "enabled": self.enabled,
            "frame_count": self.frame_count,
            "config": self.config,
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.agent_name}, enabled={self.enabled})"
