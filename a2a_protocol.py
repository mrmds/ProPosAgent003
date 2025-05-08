"""A2A (Agent-to-Agent) Protocol Implementation for agent collaboration."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
import json
import uuid


@dataclass
class AgentInfo:
    """Information about an agent for registration with the A2A protocol."""
    id: str
    name: str
    capabilities: List[str]
    metadata: Dict[str, Any] = None


@dataclass
class Message:
    """A message in the A2A protocol system."""
    sender_id: str
    recipient_id: str
    content: str
    type: str = "request"  # request, response, broadcast, etc.
    message_id: str = None
    thread_id: str = None
    timestamp: float = None
    
    def __post_init__(self):
        """Initialize default values for message_id and thread_id if not provided."""
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
        
        if self.thread_id is None:
            self.thread_id = self.message_id
        
        if self.timestamp is None:
            import time
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "type": self.type,
            "timestamp": self.timestamp
        }


class A2AProtocol:
    """
    A2A Protocol implementation for agent-to-agent communication.
    
    This class provides:
    1. Agent registration and discovery
    2. Message passing between agents
    3. Collaboration patterns
    """
    
    def __init__(self):
        """Initialize the A2A protocol handler."""
        self.agents = {}  # Dictionary of registered agents
        self.message_queue = asyncio.Queue()  # Queue for messages
        self.message_history = {}  # History of messages by thread_id
    
    async def register_agent(self, agent_info: AgentInfo) -> bool:
        """Register an agent with the A2A protocol.
        
        Args:
            agent_info: Information about the agent to register
            
        Returns:
            Success status
        """
        if agent_info.id in self.agents:
            print(f"Agent {agent_info.id} is already registered")
            return False
        
        self.agents[agent_info.id] = {
            "id": agent_info.id,
            "name": agent_info.name,
            "capabilities": agent_info.capabilities,
            "metadata": agent_info.metadata or {},
            "status": "active"
        }
        
        print(f"Agent {agent_info.name} ({agent_info.id}) registered with capabilities: {agent_info.capabilities}")
        return True
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the A2A protocol.
        
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
    
    async def send_message(self, message: Message) -> Dict[str, Any]:
        """Send a message from one agent to another.
        
        Args:
            message: The message to send
            
        Returns:
            Status and message details
        """
        # Check if sender and recipient are registered
        if message.sender_id not in self.agents:
            return {"status": "error", "error": f"Sender agent {message.sender_id} is not registered"}
        
        if message.recipient_id != "broadcast" and message.recipient_id not in self.agents:
            return {"status": "error", "error": f"Recipient agent {message.recipient_id} is not registered"}
        
        # Add message to queue and history
        await self.message_queue.put(message)
        
        if message.thread_id not in self.message_history:
            self.message_history[message.thread_id] = []
        
        self.message_history[message.thread_id].append(message.to_dict())
        
        return {
            "status": "success", 
            "message_id": message.message_id,
            "thread_id": message.thread_id
        }
    
    async def receive_messages(self, agent_id: str, timeout: float = 0.1) -> List[Dict[str, Any]]:
        """Receive messages for a specific agent.
        
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
                    messages.append(message.to_dict())
                
                self.message_queue.task_done()
        except asyncio.QueueEmpty:
            pass
        
        return messages
    
    def get_agents_with_capability(self, capability: str) -> List[Dict[str, Any]]:
        """Find agents that have a specific capability.
        
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
        """Get the history of messages for a specific thread.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            List of messages in the thread
        """
        return self.message_history.get(thread_id, [])
