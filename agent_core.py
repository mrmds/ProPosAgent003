"""Simplified agent core with Ollama support."""

import asyncio
import os
from typing import Any, Callable, Dict, List, Optional
import ollama

class Agent:
    """Simplified agent that works with Ollama."""
    
    def __init__(
        self,
        model: str = "llama2",
        system_prompt: str = "You are a helpful assistant.",
        tools: Optional[List[Callable]] = None
    ):
        """Initialize the agent.
        
        Args:
            model: Name of the Ollama model to use
            system_prompt: System prompt for the agent
            tools: List of tool functions the agent can use
        """
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.client = ollama.Client(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    
    def tool(self, func: Callable) -> Callable:
        """Decorator to register a tool with the agent.
        
        Args:
            func: The tool function to register
            
        Returns:
            The decorated function
        """
        self.tools.append(func)
        return func

        
    async def _generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a response using Ollama.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            The model's response text
        """
        response = self.client.chat(
            model=self.model,
            messages=messages
        )
        return response.message.content
    
    async def run(self, prompt: str) -> str:
        """Run the agent on a prompt.
        
        Args:
            prompt: The user's input prompt
            
        Returns:
            The agent's response
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._generate_response(messages)
        return response
    
    def run_sync(self, prompt: str) -> str:
        """Synchronous version of run.
        
        Args:
            prompt: The user's input prompt
            
        Returns:
            The agent's response
        """
        return asyncio.run(self.run(prompt))
    
    async def run_tool(self, tool_name: str, **kwargs) -> Any:
        """Run a specific tool.
        
        Args:
            tool_name: Name of the tool to run
            **kwargs: Arguments for the tool
            
        Returns:
            The tool's output
        """
        for tool in self.tools:
            if tool.__name__ == tool_name:
                return await tool(**kwargs)
        raise ValueError(f"Tool {tool_name} not found")
