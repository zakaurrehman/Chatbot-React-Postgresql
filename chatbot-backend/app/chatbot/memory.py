# Conversation memory management
"""Conversation memory management for the chatbot."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)

class ConversationMemory:
    """Manages conversation history for the chatbot."""
    
    def __init__(self, max_messages: int = 10):
        """Initialize conversation memory.
        
        Args:
            max_messages: Maximum number of messages to retain in memory
        """
        self.messages = []
        self.max_messages = max_messages
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to the conversation history.
        
        Args:
            role: The role of the message sender ('user' or 'assistant')
            content: The content of the message
            metadata: Additional metadata for the message (e.g., database results, intent)
        """
        timestamp = datetime.now().isoformat()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
        
        if metadata:
            message["metadata"] = metadata
            
        self.messages.append(message)
        
        # Trim history if needed
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[len(self.messages) - self.max_messages:]
            
        logger.debug(f"Added message to conversation history. Total messages: {len(self.messages)}")
    
    def get_messages(self, include_metadata: bool = False) -> List[Dict[str, Any]]:
        """Get the conversation history.
        
        Args:
            include_metadata: Whether to include metadata in the returned messages
            
        Returns:
            List of message dictionaries
        """
        if include_metadata:
            return self.messages.copy()
        
        # Remove metadata from messages
        return [
            {k: v for k, v in message.items() if k != 'metadata'}
            for message in self.messages
        ]
    
    def get_formatted_history(self, max_tokens: int = 2000) -> str:
        """Get the conversation history formatted as a string for the LLM context.
        
        Args:
            max_tokens: Approximate maximum number of tokens to include
            
        Returns:
            Formatted conversation history string
        """
        formatted_history = ""
        # Start from the most recent messages
        for message in reversed(self.messages):
            message_text = f"{message['role'].upper()}: {message['content']}\n\n"
            
            # Simple token estimation (very approximate)
            estimated_tokens = len(message_text) / 4
            
            # Check if adding this message would exceed the limit
            if len(formatted_history) / 4 + estimated_tokens > max_tokens:
                break
                
            # Add message to the beginning
            formatted_history = message_text + formatted_history
            
        return formatted_history.strip()
    
    def clear(self) -> None:
        """Clear the conversation history."""
        self.messages = []
        logger.debug("Conversation history cleared")
    
    def to_json(self) -> str:
        """Convert the conversation history to a JSON string.
        
        Returns:
            JSON string representation of the conversation history
        """
        return json.dumps(self.messages, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str, max_messages: int = 10) -> 'ConversationMemory':
        """Create a ConversationMemory instance from a JSON string.
        
        Args:
            json_str: JSON string representation of conversation history
            max_messages: Maximum number of messages to retain
            
        Returns:
            ConversationMemory instance
        """
        memory = cls(max_messages=max_messages)
        try:
            memory.messages = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding conversation history: {e}")
        return memory