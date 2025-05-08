"""
MCP (Master Control Program) Client implementation.

This module provides a client for interacting with MCP servers according to the
standards defined in the MCP GitHub repository.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
import urllib.parse
from dataclasses import dataclass

import aiohttp
from pydantic import BaseModel, Field


class MCPTool(BaseModel):
    """Model representing an MCP tool."""
    
    id: str = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Human-readable name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    version: str = Field(..., description="Version of the tool")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters schema for the tool")
    returns: Dict[str, Any] = Field(default_factory=dict, description="Return schema for the tool")
    is_streaming: bool = Field(default=False, description="Whether the tool supports streaming responses")
    auth_required: bool = Field(default=True, description="Whether authentication is required to use this tool")
    rate_limited: bool = Field(default=False, description="Whether the tool is rate limited")
    server_id: str = Field(..., description="ID of the server providing this tool")


class MCPServer(BaseModel):
    """Model representing an MCP server."""
    
    id: str = Field(..., description="Unique identifier for the server")
    name: str = Field(..., description="Human-readable name of the server")
    url: str = Field(..., description="Base URL of the server")
    description: str = Field(default="", description="Description of the server")
    auth_type: str = Field(default="api_key", description="Authentication type (api_key, oauth, none)")
    tools: List[MCPTool] = Field(default_factory=list, description="List of tools provided by this server")


class MCPToolResponse(BaseModel):
    """Model representing an MCP tool execution response."""
    
    tool_id: str = Field(..., description="ID of the executed tool")
    status: str = Field(..., description="Status of the execution (success, error, in_progress)")
    execution_id: Optional[str] = Field(None, description="ID of the execution for async operations")
    result: Optional[Any] = Field(None, description="Result of the tool execution if successful")
    error: Optional[str] = Field(None, description="Error message if execution failed")


class MCPClient:
    """
    Client for interacting with MCP servers.
    
    This client implements the standards defined in the MCP GitHub repository
    for discovering and executing tools across multiple MCP servers.
    """
    
    def __init__(self, servers: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the MCP client.
        
        Args:
            servers: Optional list of server configurations to register immediately
        """
        self.servers: Dict[str, MCPServer] = {}
        
        if servers:
            for server_config in servers:
                self.add_server(server_config)
    
    def add_server(self, config: Dict[str, Any]) -> str:
        """
        Add an MCP server to the client.
        
        Args:
            config: Server configuration dictionary with url, name, and optional auth details
            
        Returns:
            The server ID
        """
        server_id = config.get("id", str(hash(config["url"])))
        
        server = MCPServer(
            id=server_id,
            name=config.get("name", f"MCP Server {len(self.servers) + 1}"),
            url=config["url"].rstrip("/"),
            description=config.get("description", ""),
            auth_type=config.get("auth_type", "api_key"),
            tools=[]
        )
        
        self.servers[server_id] = server
        return server_id
    
    def remove_server(self, server_id: str) -> bool:
        """
        Remove an MCP server from the client.
        
        Args:
            server_id: ID of the server to remove
            
        Returns:
            True if the server was removed, False if it wasn't found
        """
        if server_id in self.servers:
            del self.servers[server_id]
            return True
        return False
    
    async def discover_tools(self, server_id: str, api_key: Optional[str] = None) -> List[MCPTool]:
        """
        Discover tools available on an MCP server.
        
        Args:
            server_id: ID of the server to discover tools from
            api_key: Optional API key for authenticated discovery
            
        Returns:
            List of discovered tools
            
        Raises:
            ValueError: If the server ID is invalid
            ConnectionError: If connection to the server fails
        """
        if server_id not in self.servers:
            raise ValueError(f"Unknown MCP server ID: {server_id}")
        
        server = self.servers[server_id]
        
        async with aiohttp.ClientSession() as session:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            try:
                async with session.get(f"{server.url}/tools", headers=headers) as response:
                    if response.status != 200:
                        raise ConnectionError(f"Failed to discover tools: {response.status} {await response.text()}")
                    
                    data = await response.json()
                    tools = []
                    
                    for tool_data in data.get("tools", []):
                        tool_data["server_id"] = server_id
                        tool = MCPTool(**tool_data)
                        tools.append(tool)
                    
                    # Update server's tool list
                    server.tools = tools
                    self.servers[server_id] = server
                    
                    return tools
            
            except Exception as e:
                raise ConnectionError(f"Failed to connect to MCP server: {str(e)}")
    
    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        api_key: Optional[str] = None,
        wait_for_completion: bool = True,
        timeout: float = 30.0
    ) -> MCPToolResponse:
        """
        Execute a tool on an MCP server.
        
        Args:
            tool_id: ID of the tool to execute
            parameters: Parameters to pass to the tool
            api_key: Optional API key for authenticated execution
            wait_for_completion: Whether to wait for async tool completion
            timeout: Timeout in seconds for waiting for completion
            
        Returns:
            The tool execution response
            
        Raises:
            ValueError: If the tool ID is invalid
            ConnectionError: If connection to the server fails
        """
        # Find which server has this tool
        server_id = None
        tool = None
        
        for s_id, server in self.servers.items():
            for t in server.tools:
                if t.id == tool_id:
                    server_id = s_id
                    tool = t
                    break
            
            if server_id:
                break
        
        if not server_id or not tool:
            raise ValueError(f"Unknown tool ID: {tool_id}")
        
        server = self.servers[server_id]
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
            }
            
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            try:
                # Execute the tool
                async with session.post(
                    f"{server.url}/tools/{tool_id}/execute",
                    headers=headers,
                    json={"parameters": parameters}
                ) as response:
                    if response.status not in (200, 202):
                        raise ConnectionError(f"Failed to execute tool: {response.status} {await response.text()}")
                    
                    data = await response.json()
                    tool_response = MCPToolResponse(
                        tool_id=tool_id,
                        status=data.get("status", "error"),
                        execution_id=data.get("execution_id"),
                        result=data.get("result"),
                        error=data.get("error")
                    )
                    
                    # If the tool execution is asynchronous and we should wait for completion
                    if (
                        tool_response.status == "in_progress" and
                        tool_response.execution_id and
                        wait_for_completion
                    ):
                        return await self._wait_for_completion(
                            server.url,
                            tool_id,
                            tool_response.execution_id,
                            headers,
                            timeout
                        )
                    
                    return tool_response
            
            except Exception as e:
                return MCPToolResponse(
                    tool_id=tool_id,
                    status="error",
                    error=f"Failed to connect to MCP server: {str(e)}"
                )
    
    async def _wait_for_completion(
        self,
        server_url: str,
        tool_id: str,
        execution_id: str,
        headers: Dict[str, str],
        timeout: float
    ) -> MCPToolResponse:
        """
        Wait for an asynchronous tool execution to complete.
        
        Args:
            server_url: Base URL of the server
            tool_id: ID of the tool
            execution_id: ID of the execution
            headers: HTTP headers to use for the request
            timeout: Timeout in seconds
            
        Returns:
            The tool execution response
        """
        start_time = asyncio.get_event_loop().time()
        
        async with aiohttp.ClientSession() as session:
            while asyncio.get_event_loop().time() - start_time < timeout:
                async with session.get(
                    f"{server_url}/tools/{tool_id}/executions/{execution_id}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return MCPToolResponse(
                            tool_id=tool_id,
                            status="error",
                            execution_id=execution_id,
                            error=f"Failed to check execution status: {response.status} {await response.text()}"
                        )
                    
                    data = await response.json()
                    status = data.get("status")
                    
                    if status in ("success", "error"):
                        return MCPToolResponse(
                            tool_id=tool_id,
                            status=status,
                            execution_id=execution_id,
                            result=data.get("result"),
                            error=data.get("error")
                        )
                
                # Wait a bit before checking again
                await asyncio.sleep(0.5)
        
        # Timeout reached
        return MCPToolResponse(
            tool_id=tool_id,
            status="error",
            execution_id=execution_id,
            error="Execution timed out"
        )
