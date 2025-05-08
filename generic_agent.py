"""Generic Agent implementing Supabase connection, MCP server interaction, and A2A protocol."""

import os
import sys
import argparse
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union
import asyncio
import json

import dotenv
from agent_core import Agent
import ollama

# Import Supabase client
from supabase import create_client, Client as SupabaseClient

from utils import (
    get_supabase_client,
    query_supabase_collection,
    format_results_as_context
)

# Load environment variables from .env file
dotenv.load_dotenv()

# Check for required environment variables
required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OLLAMA_BASE_URL"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"Error: The following environment variables are not set: {', '.join(missing_vars)}")
    print("Please create a .env file with these variables or set them in your environment.")
    sys.exit(1)


@dataclass
class AgentDeps:
    """Dependencies for the generic agent."""
    supabase_client: SupabaseClient
    table_name: str


# Create a function to get the agent with the specified Ollama model
def get_agent(model: str = "llama2"):
    return Agent(
        model=model,  # Use Ollama model directly

        system_prompt="You are a helpful assistant that can complete various tasks using tools. "
                     "You have access to a knowledge base via Supabase and can collaborate with other agents "
                     "using the A2A protocol. You can call an MCP server for tool execution and access advanced capabilities."
    )

# Create the default agent with llama3
agent = get_agent()




@agent.tool
async def query_knowledge_base(search_query: str, n_results: int = 5) -> str:
    """Query the knowledge base stored in Supabase.
    
    Args:
        search_query: The search query to find relevant information.
        n_results: Number of results to return (default: 5).
        
    Returns:
        Formatted context information from the retrieved data.
    """
    # Create Supabase client
    supabase = get_supabase_client()
    
    # Query Supabase
    query_results = await query_supabase_collection(
        supabase,
        "knowledge_base",
        search_query,
        n_results=n_results
    )
    
    # Format the results as context
    return format_results_as_context(query_results)


@agent.tool
async def query_mcp_server(server_name: str, query: str) -> str:
    """Query an MCP server.
    
    Args:
        server_name: Name of the MCP server to query.
        query: The query to send to the server.
        
    Returns:
        The server's response.
    """
    # This is a placeholder for the actual MCP server implementation
    return f"Queried MCP server {server_name} with: {query}"


@agent.tool



async def run_generic_agent(
    input_text: str,
    table_name: str = "knowledge_base",
    model: str = "llama2"
) -> str:
    """Run the generic agent to process an input and generate a response.
    
    Args:
        input_text: The input text to process.
        table_name: Name of the Supabase table to use.
        model: The Ollama model to use (default: llama2).
        
    Returns:
        The agent's response.
    """
    # Create dependencies
    deps = AgentDeps(
        supabase_client=get_supabase_client(),
        table_name=table_name
    )
    
    # Get agent with specified model
    current_agent = get_agent(model)
    
    # Run the agent
    response = await current_agent.run(input_text)
    
    return response


def main():
    """Main function to parse arguments and run the generic agent."""
    parser = argparse.ArgumentParser(description="Run a generic agent with Supabase and Ollama")
    parser.add_argument("--input", help="The input text to process")
    parser.add_argument("--table", default="knowledge_base", help="Name of the Supabase table")
    parser.add_argument("--model", default="llama2", help="Name of the Ollama model to use")
    
    args = parser.parse_args()
    
    # Get input from command line or stdin
    input_text = args.input
    if not input_text:
        print("Enter your input (Ctrl+D to finish):")
        input_text = sys.stdin.read().strip()
    
    # Run the agent
    response = asyncio.run(run_generic_agent(
        input_text,
        table_name=args.table,
        model=args.model
    ))
    
    print("\nResponse:")
    print(response)


if __name__ == "__main__":
    main()
