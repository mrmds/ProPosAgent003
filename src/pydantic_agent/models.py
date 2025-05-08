"""
Data models for the Pydantic AI Agent.

This module defines the Pydantic models used throughout the agent implementation,
including dependencies, configuration, and data structures.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from supabase import Client as SupabaseClient
from .a2a_protocol import A2AProtocol


@dataclass
class AgentDependencies:
    """Dependencies for the Pydantic AI Agent."""
    
    # Database connection
    supabase_client: SupabaseClient
    table_name: str
    
    # A2A protocol for agent communication
    a2a_protocol: A2AProtocol
    agent_id: str
    agent_name: str
    
    # MCP servers configuration
    mcp_servers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Ollama configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"


class ToolParameter(BaseModel):
    """Schema for a tool parameter."""
    
    name: str = Field(..., description="Name of the parameter")
    type: str = Field(..., description="Data type of the parameter")
    description: str = Field(..., description="Description of the parameter")
    required: bool = Field(default=True, description="Whether the parameter is required")
    default: Optional[Any] = Field(None, description="Default value for the parameter")


class ToolSchema(BaseModel):
    """Schema for describing a tool."""
    
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: List[ToolParameter] = Field(default_factory=list, description="Parameters for the tool")
    returns: Dict[str, Any] = Field(default_factory=dict, description="Description of what the tool returns")


class KnowledgeItem(BaseModel):
    """Model for a knowledge item stored in Supabase."""
    
    id: str = Field(..., description="Unique identifier for the knowledge item")
    content: str = Field(..., description="Text content of the knowledge item")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata for the knowledge item")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of the content")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class A2AAgentInfo(BaseModel):
    """Information about an agent in the A2A protocol."""
    
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name of the agent")
    capabilities: List[str] = Field(default_factory=list, description="List of agent capabilities")
