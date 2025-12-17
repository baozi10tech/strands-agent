"""
Message Queue System for Agent-CS Communication

This module provides a simple asynchronous message queue for communication
between the Negotiation Agent and the CS Simulator CLI (human tester).

The queue handles:
- Agent -> CS messages
- CS -> Agent responses
- Async/blocking coordination
"""

import asyncio
from collections import deque
from typing import Optional
from datetime import datetime


class MessageQueue:
    """
    Bidirectional message queue for Negotiation Agent <-> CS Simulator communication.
    
    Flow:
    1. Negotiation Agent sends message -> agent_to_cs queue
    2. CS Simulator (human) reads message (blocking)
    3. Human types response -> cs_to_agent queue
    4. Negotiation Agent receives response (async)
    """
    
    def __init__(self):
        """Initialize empty queues and events"""
        self.agent_to_cs = deque()  # Messages from Negotiation Agent to CS
        self.cs_to_agent = deque()  # Responses from CS to Negotiation Agent
        
        # Events for signaling
        self.agent_message_ready = asyncio.Event()  # CS waits on this
        self.cs_response_ready = asyncio.Event()    # Agent waits on this
        
        # Track conversation history
        self.conversation_history = []
        
        # Active conversation flag
        self.active = False
    
    async def send_from_agent(self, message: str) -> None:
        """
        Negotiation Agent sends a message to CS.
        
        Args:
            message: The message text to send
        """
        timestamp = datetime.now().isoformat()
        message_data = {
            "text": message,
            "timestamp": timestamp,
            "sender": "negotiation_agent"
        }
        
        self.agent_to_cs.append(message_data)
        self.conversation_history.append(message_data)
        self.agent_message_ready.set()
        self.active = True
    
    async def wait_for_cs_response(self, timeout: Optional[float] = None) -> str:
        """
        Negotiation Agent waits for CS response.
        
        Args:
            timeout: Optional timeout in seconds
        
        Returns:
            The CS response message text
        
        Raises:
            asyncio.TimeoutError: If timeout is reached
        """
        try:
            if timeout:
                await asyncio.wait_for(self.cs_response_ready.wait(), timeout=timeout)
            else:
                await self.cs_response_ready.wait()
            
            if self.cs_to_agent:
                response_data = self.cs_to_agent.popleft()
                self.cs_response_ready.clear()
                return response_data["text"]
            else:
                return ""
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError("Timeout waiting for CS response")
    
    def send_from_cs(self, message: str) -> None:
        """
        CS sends response to Negotiation Agent (blocking/sync).
        
        Args:
            message: The response message text
        """
        timestamp = datetime.now().isoformat()
        message_data = {
            "text": message,
            "timestamp": timestamp,
            "sender": "cs_simulator"
        }
        
        self.cs_to_agent.append(message_data)
        self.conversation_history.append(message_data)
        self.cs_response_ready.set()
    
    async def wait_for_agent_message(self, timeout: Optional[float] = None) -> str:
        """
        CS waits for message from Negotiation Agent.
        
        Args:
            timeout: Optional timeout in seconds
        
        Returns:
            The agent message text
        
        Raises:
            asyncio.TimeoutError: If timeout is reached
        """
        try:
            if timeout:
                await asyncio.wait_for(self.agent_message_ready.wait(), timeout=timeout)
            else:
                await self.agent_message_ready.wait()
            
            if self.agent_to_cs:
                message_data = self.agent_to_cs.popleft()
                self.agent_message_ready.clear()
                return message_data["text"]
            else:
                return ""
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError("Timeout waiting for agent message")
    
    def get_conversation_history(self) -> list:
        """
        Get full conversation history.
        
        Returns:
            List of message dictionaries with text, timestamp, sender
        """
        return self.conversation_history.copy()
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
    
    def is_active(self) -> bool:
        """Check if conversation is active"""
        return self.active
    
    def end_conversation(self) -> None:
        """Mark conversation as ended"""
        self.active = False


# Global message queue instance (singleton pattern)
_global_queue = None


def get_global_queue() -> MessageQueue:
    """
    Get or create the global message queue instance.
    
    Returns:
        The global MessageQueue instance
    """
    global _global_queue
    if _global_queue is None:
        _global_queue = MessageQueue()
    return _global_queue


def reset_global_queue() -> None:
    """Reset the global queue (useful for testing)"""
    global _global_queue
    _global_queue = None
