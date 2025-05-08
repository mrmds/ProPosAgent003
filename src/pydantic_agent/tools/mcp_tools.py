"""
MCP integration tools for the Pydantic AI Agent.

This module provides tools for interacting with MCP servers,
discovering available tools, and executing them.
"""

from typing import Dict, List, Any, Optional, Union, Callable
import json
import asyncio

from pydantic_ai import RunContext
from ..models import AgentDependencies
from ..mcp_client import MCPClient


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
    mcp_client = MCPClient()
    
    # Get API key for the server if available
    api_key = None
    if server_id in context.deps.mcp_servers:
        api_key = context.deps.mcp_servers[server_id].get("api_key")
    
    try:
        # Use the MCP client to discover tools
        tools = await mcp_client.discover_tools(server_id, api_key)
        
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
    mcp_client = MCPClient()
    
    # Get API key for the server if available
    api_key = None
    if server_id in context.deps.mcp_servers:
        api_key = context.deps.mcp_servers[server_id].get("api_key")
    
    try:
        # Use the MCP client to execute the tool
        response = await mcp_client.execute_tool(
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


async def list_mcp_servers(context: RunContext[AgentDependencies]) -> List[Dict[str, Any]]:
    """
    List all configured MCP servers.
    
    Args:
        context: The run context containing dependencies
        
    Returns:
        List of MCP servers with their details
    """
    servers = []
    
    for server_id, server_config in context.deps.mcp_servers.items():
        # Don't include API keys in the output
        server_info = server_config.copy()
        if "api_key" in server_info:
            server_info["api_key"] = "********"  # Mask the API key
        
        server_info["id"] = server_id
        servers.append(server_info)
    
    return servers


# Register tools in the registry
from ..tools import TOOL_REGISTRY

TOOL_REGISTRY["discover_mcp_tools"] = discover_mcp_tools
TOOL_REGISTRY["call_mcp_tool"] = call_mcp_tool
TOOL_REGISTRY["list_mcp_servers"] = list_mcp_servers
