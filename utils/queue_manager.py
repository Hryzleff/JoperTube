# Queue manager for handling music queues
import logging

# Setup logger
logger = logging.getLogger(__name__)

class QueueManager:
    """Manages a queue of songs for a guild"""
    
    def __init__(self):
        """Initialize an empty queue"""
        self._queue = []
        self._current_index = 0
    
    def add(self, item):
        """
        Add an item to the queue
        
        Args:
            item: The item to add (typically a YouTube URL)
        """
        self._queue.append(item)
        logger.debug(f"Added item to queue. Queue size: {len(self._queue)}")
    
    def get_next(self):
        """
        Get the next item in the queue
        
        Returns:
            The next item in the queue, or None if the queue is empty
        """
        if self.is_empty():
            return None
        
        item = self._queue.pop(0)
        logger.debug(f"Retrieved next item from queue. Remaining: {len(self._queue)}")
        return item
    
    def peek(self):
        """
        Look at the next item in the queue without removing it
        
        Returns:
            The next item in the queue, or None if the queue is empty
        """
        if self.is_empty():
            return None
        return self._queue[0]
    
    def clear(self):
        """Clear the queue"""
        self._queue = []
        logger.debug("Queue cleared")
    
    def is_empty(self):
        """
        Check if the queue is empty
        
        Returns:
            bool: True if the queue is empty, False otherwise
        """
        return len(self._queue) == 0
    
    def size(self):
        """
        Get the size of the queue
        
        Returns:
            int: The number of items in the queue
        """
        return len(self._queue)
    
    def get_queue(self):
        """
        Get a copy of the current queue
        
        Returns:
            list: A copy of the queue
        """
        return self._queue.copy()
