"""
Core implementation of the Pydantic AI Agent.

This module provides the main agent implementation with Supabase integration,
Ollama for local LLM execution, MCP client for tool execution, and A2A
protocol for agent collaboration.
"""

import os
import sys
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
import json
import logging

import ollama
from pydantic_ai import RunContext
from pydantic_ai.agent import Agent
from supabase import create_client

from .models import AgentDependencies
from .mcp_client import MCPClient, MCPTool, MCPToolResponse
from .a2a_protocol import A2AProtocol, AgentInfo, Message
from .supabase_client import SupabaseVectorClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pydantic_agent")


class PydanticAgent:
    """
    Pydantic AI Agent with Supabase, Ollama, MCP, and A2A protocol integration.
    
    This agent can:
    1. Query knowledge from Supabase vector storage
    2. Execute tools via MCP servers
    3. Collaborate with other agents using the A2A protocol
    4. Use local LLM inference with Ollama
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        ollama_model: str = "llama3",
        ollama_base_url: str = "http://localhost:11434",
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the Pydantic Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_name: Human-readable name for this agent
            ollama_model: Ollama model to use for inference
            ollama_base_url: Base URL for Ollama API
            system_prompt: Optional custom system prompt
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url
        
        # Set default system prompt if none provided
        if system_prompt is None:
            system_prompt = (
                "You are a helpful assistant that can complete various tasks using tools. "
                "You have access to a knowledge base via Supabase and can collaborate with other agents "
                "using the A2A protocol. You can call MCP servers for tool execution and access advanced capabilities."
            )
        
        # Initialize the Pydantic AI agent
        self.agent = Agent(
            f"ollama:{ollama_model}",  # Use colon for pydantic-ai compatibility
            deps_type=AgentDependencies,
            system_prompt=system_prompt,
        )
        
        # Initialize MCP client
        self.mcp_client = MCPClient()
        
        # Initialize Ollama client
        self.ollama_client = ollama.Client(host=ollama_base_url)
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all agent tools."""
        
        @self.agent.tool
        async def query_knowledge_base(
            context: RunContext[AgentDependencies],
            search_query: str,
            n_results: int = 5,
            filter_metadata: Optional[Dict[str, Any]] = None
        ) -> str:
            """
            Query the knowledge base stored in Supabase.
            
            Args:
                context: The run context containing dependencies
                search_query: The search query to find relevant information
                n_results: Number of results to return
                filter_metadata: Optional metadata filters to apply
                
            Returns:
                Formatted context information from the retrieved data
            """
            supabase_client = SupabaseVectorClient(context.deps.supabase_client)
            
            # Query Supabase for relevant documents
            results = await supabase_client.search_documents(
                context.deps.table_name,
                search_query,
                limit=n_results,
                filter_metadata=filter_metadata
            )
            
            if not results:
                return "No relevant information found in the knowledge base."
            
            # Format results as context
            context_str = "CONTEXT INFORMATION:\n\n"
            
            for i, doc in enumerate(results):
                context_str += f"Document {i+1}"
                if "relevance" in doc:
                    context_str += f" (Relevance: {doc['relevance']:.2f})"
                context_str += ":\n"
                
                # Add metadata if available
                if "metadata" in doc and doc["metadata"]:
                    metadata = doc["metadata"]
                    for key, value in metadata.items():
                        context_str += f"{key}: {value}\n"
                
                # Add content
                context_str += f"Content: {doc['content']}\n\n"
            
            return context_str
        
        @self.agent.tool
        async def call_mcp_tool(
            context: RunContext[AgentDependencies],
            server_id: str,
            tool_id: str,
            parameters: Dict[str, Any]
        ) -> Dict[str, Any]:
            """
            Call a tool on an MCP server.
            
            Args:
                context: The run context containing dependencies
                server_id: ID of the MCP server to use
                tool_id: ID of the tool to execute
                parameters: Parameters to pass to the tool
                
            Returns:
                The result of the tool execution
            """
            # Get API key for the server if available
            api_key = None
            if server_id in context.deps.mcp_servers:
                api_key = context.deps.mcp_servers[server_id].get("api_key")
            
            try:
                # Use the MCP client to execute the tool
                response = await self.mcp_client.execute_tool(
                    tool_id=tool_id,
                    parameters=parameters,
                    api_key=api_key,
                    wait_for_completion=True,
                    timeout=30.0
                )
                
                if response.status == "success":
                    return {"status": "success", "result": response.result}
                else:
                    return {"status": "error", "error": response.error or "Unknown error"}
            
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        @self.agent.tool
        async def discover_mcp_tools(
            context: RunContext[AgentDependencies],
            server_id: str
        ) -> List[Dict[str, Any]]:
            """
            Discover tools available on an MCP server.
            
            Args:
                context: The run context containing dependencies
                server_id: ID of the MCP server to discover tools from
                
            Returns:
                List of discovered tools with their details
            """
            # Get API key for the server if available
            api_key = None
            if server_id in context.deps.mcp_servers:
                api_key = context.deps.mcp_servers[server_id].get("api_key")
            
            try:
                # Use the MCP client to discover tools
                tools = await self.mcp_client.discover_tools(server_id, api_key)
                
                # Convert to simple dictionaries for the LLM
                return [
                    {
                        "id": tool.id,
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                    for tool in tools
                ]
            
            except Exception as e:
                return [{"error": str(e)}]
        
        @self.agent.tool
        async def send_a2a_message(
            context: RunContext[AgentDependencies],
            recipient_id: str,
            content: str,
            message_type: str = "request",
            thread_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Send a message to another agent using the A2A protocol.
            
            Args:
                context: The run context containing dependencies
                recipient_id: ID of the recipient agent
                content: Content of the message
                message_type: Type of message (request, response, etc.)
                thread_id: Optional thread ID for conversation tracking
                
            Returns:
                Status of the message delivery
            """
            # Create message
            message = Message(
                sender_id=context.deps.agent_id,
                recipient_id=recipient_id,
                content=content,
                type=message_type,
                thread_id=thread_id
            )
            
            # Send message
            result = await context.deps.a2a_protocol.send_message(message)
            
            return result
        
        @self.agent.tool
        async def list_available_agents(
            context: RunContext[AgentDependencies],
            capability: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """
            List agents available via the A2A protocol.
            
            Args:
                context: The run context containing dependencies
                capability: Optional capability to filter agents by
                
            Returns:
                List of available agents with their details
            """
            if capability:
                agents = context.deps.a2a_protocol.get_agents_with_capability(capability)
            else:
                agents = [
                    agent_info for agent_id, agent_info in 
                    context.deps.a2a_protocol.agents.items()
                ]
            
            return agents
    
    async def run(
        self,
        input_text: str,
        supabase_url: str,
        supabase_key: str,
        table_name: str = "knowledge_base",
        mcp_servers: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Run the agent to process an input query.
        
        Args:
            input_text: The input text to process
            supabase_url: URL of the Supabase project
            supabase_key: API key for Supabase
            table_name: Name of the Supabase table containing knowledge
            mcp_servers: List of MCP server configurations
            
        Returns:
            The agent's response
        """
        # Create Supabase client
        supabase_client = create_client(supabase_url, supabase_key)
        
        # Initialize A2A protocol
        a2a_protocol = A2AProtocol()
        
        # Register this agent with the A2A protocol
        await a2a_protocol.register_agent(AgentInfo(
            id=self.agent_id,
            name=self.agent_name,
            capabilities=["text_processing", "knowledge_retrieval", "tool_execution"]
        ))
        
        # Process MCP servers
        mcp_server_configs = {}
        
        # First, try to load MCP servers from environment
        env_servers = self._load_mcp_servers_from_env()
        for server_config in env_servers:
            server_id = self.mcp_client.add_server(server_config)
            mcp_server_configs[server_id] = server_config
        
        # Then add any additional servers passed directly
        if mcp_servers:
            for server_config in mcp_servers:
                server_id = self.mcp_client.add_server(server_config)
                mcp_server_configs[server_id] = server_config
        
        # Create dependencies
        deps = AgentDependencies(
            supabase_client=supabase_client,
            table_name=table_name,
            a2a_protocol=a2a_protocol,
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            mcp_servers=mcp_server_configs,
            ollama_base_url=self.ollama_base_url,
            ollama_model=self.ollama_model
        )
        
        try:
            # Run the agent
            result = await self.agent.run(input_text, deps=deps)
            
            response = {
                "status": "success",
                "data": result.data,
                "metadata": {
                    "agent_id": self.agent_id,
                    "model": self.ollama_model,
                }
            }
        
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}", exc_info=True)
            response = {
                "status": "error",
                "error": str(e),
                "metadata": {
                    "agent_id": self.agent_id,
                    "model": self.ollama_model,
                }
            }
        
        finally:
            # Unregister from A2A protocol
            await a2a_protocol.unregister_agent(self.agent_id)
        
        return response

    def _load_mcp_servers_from_env(self) -> List[Dict[str, Any]]:
        """
        Load MCP server configurations from environment variables.
        
        Environment variables should follow the pattern:
        MCP_SERVER_<N>_<FIELD>=value
        
        Returns:
            List of server configurations
        """
        servers = []
        server_index = 1
        
        while True:
            prefix = f"MCP_SERVER_{server_index}_"
            
            # Check if this server exists in env
            if not any(key.startswith(prefix) for key in os.environ):
                break
            
            # Build server config
            config = {
                "name": os.getenv(f"{prefix}NAME"),
                "url": os.getenv(f"{prefix}URL"),
                "auth_type": os.getenv(f"{prefix}AUTH_TYPE", "api_key"),
                "description": os.getenv(f"{prefix}DESCRIPTION", ""),
            }
            
            # Only include if required fields are present
            if config["name"] and config["url"]:
                # Add auth details if present
                if config["auth_type"] == "api_key":
                    api_key = os.getenv(f"{prefix}API_KEY")
                    if api_key:
                        config["api_key"] = api_key
                elif config["auth_type"] == "oauth":
                    client_id = os.getenv(f"{prefix}CLIENT_ID")
                    client_secret = os.getenv(f"{prefix}CLIENT_SECRET")
                    if client_id and client_secret:
                        config["client_id"] = client_id
                        config["client_secret"] = client_secret
                
                servers.append(config)
            
            server_index += 1
        
        return servers
