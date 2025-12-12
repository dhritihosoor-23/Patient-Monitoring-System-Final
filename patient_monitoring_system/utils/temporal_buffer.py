"""
Temporal buffer for maintaining sliding windows of data.
"""

from collections import deque
from typing import Any, List, Optional


class TemporalBuffer:
    """
    Circular buffer for temporal data with sliding window functionality.
    """
    
    def __init__(self, maxlen: int):
        """
        Initialize temporal buffer.
        
        Args:
            maxlen: Maximum number of items to store
        """
        self.maxlen = maxlen
        self.buffer = deque(maxlen=maxlen)
    
    def add(self, item: Any):
        """Add item to buffer"""
        self.buffer.append(item)
    
    def get_latest(self) -> Optional[Any]:
        """Get most recent item"""
        return self.buffer[-1] if len(self.buffer) > 0 else None
    
    def get_oldest(self) -> Optional[Any]:
        """Get oldest item"""
        return self.buffer[0] if len(self.buffer) > 0 else None
    
    def get_all(self) -> List[Any]:
        """Get all items as list"""
        return list(self.buffer)
    
    def get_window(self, window_size: int) -> List[Any]:
        """
        Get most recent N items.
        
        Args:
            window_size: Number of items to retrieve
            
        Returns:
            List of most recent items (may be shorter than window_size)
        """
        if window_size >= len(self.buffer):
            return list(self.buffer)
        return list(self.buffer)[-window_size:]
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return len(self.buffer) == self.maxlen
    
    def clear(self):
        """Clear all items from buffer"""
        self.buffer.clear()
    
    def __len__(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)
    
    def __getitem__(self, index: int) -> Any:
        """Get item by index"""
        return self.buffer[index]
