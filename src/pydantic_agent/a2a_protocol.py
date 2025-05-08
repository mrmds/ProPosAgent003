"""
A2A (Agent-to-Agent) Protocol Implementation for agent collaboration.

This module provides a standardized protocol for communication between 
multiple agents, enabling collaboration on complex tasks.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
import asyncio
import json
import uuid
import time
from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    """Information about an agent for registration with the A2A protocol."""
    
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name of the agent")
    capabilities: List[str] = Field(default_factory=list, description="List of agent capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the agent")


class Message(BaseModel):
    """A message in the A2A protocol system."""
    
    sender_id: str = Field(..., description="ID of the sending agent")
    recipient_id: str = Field(..., description="ID of the receiving agent (or 'broadcast')")
    content: str = Field(..., description="Content of the message")
    type: str = Field(default="request", description="Type of message (request, response, broadcast, etc.)")
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the message")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation tracking")
    timestamp: float = Field(default_factory=time.time, description="Timestamp of the message creation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the message")
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization processing."""
        if self.thread_id is None:
            self.thread_id = self.message_id


class ThreadSummary(BaseModel):
    """Summary information about a conversation thread."""
    
    thread_id: str = Field(..., description="ID of the thread")
    title: str = Field(..., description="Title or subject of the thread")
    participants: List[str] = Field(default_factory=list, description="IDs of participating agents")
    message_count: int = Field(default=0, description="Number of messages in the thread")
    last_activity: float = Field(default_factory=time.time, description="Timestamp of the last activity")
    status: str = Field(default="active", description="Status of the thread (active, resolved, etc.)")


class A2AProtocol:
    """
    A2A Protocol implementation for agent-to-agent communication.
    
    This class provides:
    1. Agent registration and discovery
    2. Message passing between agents
    3. Collaboration patterns
    """
    
    def __init__(self, hub_url: Optional[str] = None):
        """
        Initialize the A2A protocol handler.
        
        Args:
            hub_url: Optional URL of a central A2A hub for multi-process communication
        """
        self.hub_url = hub_url
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.message_history: Dict[str, List[Dict[str, Any]]] = {}
        self.thread_summaries: Dict[str, ThreadSummary] = {}
    
    async def register_agent(self, agent_info: Union[AgentInfo, Dict[str, Any]]) -> bool:
        """
        Register an agent with the A2A protocol.
        
        Args:
            agent_info: Information about the agent to register
            
        Returns:
            Success status
        """
        # Convert dict to AgentInfo if needed
        if isinstance(agent_info, dict):
            agent_info = AgentInfo(**agent_info)
        
        if agent_info.id in self.agents:
            print(f"Agent {agent_info.id} is already registered")
            return False
        
        self.agents[agent_info.id] = {
            "id": agent_info.id,
            "name": agent_info.name,
            "capabilities": agent_info.capabilities,
            "metadata": agent_info.metadata or {},
            "status": "active",
            "registered_at": time.time()
        }
        
        print(f"Agent {agent_info.name} ({agent_info.id}) registered with capabilities: {agent_info.capabilities}")
        return True
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the A2A protocol.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            Success status
        """
        if agent_id not in self.agents:
            print(f"Agent {agent_id} is not registered")
            return False
        
        del self.agents[agent_id]
        print(f"Agent {agent_id} unregistered")
        return True
    
    async def send_message(self, message: Union[Message, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send a message from one agent to another.
        
        Args:
            message: The message to send
            
        Returns:
            Status and message details
        """
        # Convert dict to Message if needed
        if isinstance(message, dict):
            message = Message(**message)
        
        # Check if sender and recipient are registered
        if message.sender_id not in self.agents:
            return {"status": "error", "error": f"Sender agent {message.sender_id} is not registered"}
        
        if message.recipient_id != "broadcast" and message.recipient_id not in self.agents:
            return {"status": "error", "error": f"Recipient agent {message.recipient_id} is not registered"}
        
        # Add message to queue and history
        await self.message_queue.put(message)
        
        if message.thread_id not in self.message_history:
            self.message_history[message.thread_id] = []
            
            # Create thread summary if it doesn't exist
            if message.thread_id not in self.thread_summaries:
                # Extract a title from the first few words of the message
                title = message.content.split("\n", 1)[0][:50]
                if len(title) == 50:
                    title += "..."
                
                self.thread_summaries[message.thread_id] = ThreadSummary(
                    thread_id=message.thread_id,
                    title=title,
                    participants=[message.sender_id, message.recipient_id],
                    message_count=1,
                    last_activity=message.timestamp,
                    status="active"
                )
        else:
            # Update thread summary
            summary = self.thread_summaries.get(message.thread_id)
            if summary:
                summary.message_count += 1
                summary.last_activity = message.timestamp
                
                # Add participants if they're not already there
                if message.sender_id not in summary.participants:
                    summary.participants.append(message.sender_id)
                if message.recipient_id not in summary.participants and message.recipient_id != "broadcast":
                    summary.participants.append(message.recipient_id)
        
        # Add message to history
        self.message_history[message.thread_id].append(message.dict())
        
        return {
            "status": "success", 
            "message_id": message.message_id,
            "thread_id": message.thread_id
        }
    
    async def receive_messages(self, agent_id: str, timeout: float = 0.1) -> List[Dict[str, Any]]:
        """
        Receive messages for a specific agent.
        
        Args:
            agent_id: ID of the agent to receive messages for
            timeout: Time to wait for messages
            
        Returns:
            List of messages for the agent
        """
        messages = []
        
        # Check if agent is registered
        if agent_id not in self.agents:
            return []
        
        # Process queue with timeout
        try:
            while True:
                message = self.message_queue.get_nowait()
                
                if message.recipient_id == agent_id or message.recipient_id == "broadcast":
                    messages.append(message.dict())
                
                self.message_queue.task_done()
        except asyncio.QueueEmpty:
            pass
        
        return messages
    
    def get_agents_with_capability(self, capability: str) -> List[Dict[str, Any]]:
        """
        Find agents that have a specific capability.
        
        Args:
            capability: The capability to search for
            
        Returns:
            List of agents with the specified capability
        """
        matching_agents = []
        
        for agent_id, agent_info in self.agents.items():
            if capability in agent_info["capabilities"]:
                matching_agents.append(agent_info)
        
        return matching_agents
    
    def get_thread_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get the history of messages for a specific thread.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            List of messages in the thread
        """
        return self.message_history.get(thread_id, [])
    
    def get_all_threads(self) -> List[ThreadSummary]:
        """
        Get summaries of all conversation threads.
        
        Returns:
            List of thread summaries
        """
        return list(self.thread_summaries.values())
