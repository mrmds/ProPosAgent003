#!/usr/bin/env python3
"""
MCP API wrapper for SearXNG.

This module provides an MCP-compatible API layer over SearXNG
to enable integration with ProPosAgent.
"""

import os
import json
import asyncio
import subprocess
import uuid
from typing import Dict, List, Any, Optional
import urllib.parse
import httpx

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Start SearXNG in background
def start_searxng():
    subprocess.Popen(
        ["python", "-m", "searx.webapp"],
        env={**os.environ, "SEARXNG_SETTINGS_PATH": "/app/settings.yml"}
    )

# Define API models
class ToolParameters(BaseModel):
    query: str = Field(..., description="The search query")
    num_results: int = Field(default=5, description="Number of results to return")
    language: str = Field(default="all", description="Language filter")
    categories: List[str] = Field(default=["general"], description="Search categories")

class ToolResponse(BaseModel):
    status: str
    execution_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None

class ExecutionRequest(BaseModel):
    parameters: ToolParameters

# Create FastAPI app
app = FastAPI(
    title="SearXNG MCP",
    description="MCP-compatible API for SearXNG search engine",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store execution state
executions = {}

# Search function
async def perform_search(execution_id: str, parameters: ToolParameters):
    try:
        # URL encode query parameters
        query = urllib.parse.quote(parameters.query)
        format_param = "json"
        
        # Build URL for SearXNG API
        url = f"http://localhost:8888/search?q={query}&format={format_param}"
        
        # Add optional parameters if specified
        if parameters.num_results != 5:
            url += f"&number={parameters.num_results}"
        
        if parameters.language != "all":
            url += f"&language={parameters.language}"
            
        if parameters.categories != ["general"]:
            for category in parameters.categories:
                url += f"&category_{category}=1"
        
        # Make request to SearXNG
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                executions[execution_id] = {
                    "status": "error",
                    "error": f"SearXNG request failed with status {response.status_code}"
                }
                return
            
            # Parse results
            search_results = response.json()
            
            # Update execution status
            executions[execution_id] = {
                "status": "success",
                "result": search_results
            }
            
    except Exception as e:
        executions[execution_id] = {
            "status": "error",
            "error": f"Search failed: {str(e)}"
        }

# Routes for MCP API
@app.get("/")
async def root():
    return {
        "name": "SearXNG MCP",
        "description": "MCP-compatible API for SearXNG search engine",
        "version": "1.0.0"
    }

@app.get("/tools")
async def list_tools():
    return [
        {
            "id": "searxng_search",
            "name": "SearXNG Search",
            "description": "Search the web using SearXNG metasearch engine",
            "version": "1.0.0",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    },
                    "language": {
                        "type": "string",
                        "description": "Language filter",
                        "default": "all"
                    },
                    "categories": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Search categories",
                        "default": ["general"]
                    }
                },
                "required": ["query"]
            },
            "returns": {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object"
                        },
                        "description": "The search results"
                    }
                }
            },
            "is_streaming": False,
            "auth_required": False,
            "rate_limited": False,
            "auth_type": "none"
        }
    ]

@app.post("/tools/searxng_search/execute", response_model=ToolResponse)
async def execute_search(request: ExecutionRequest, background_tasks: BackgroundTasks):
    execution_id = str(uuid.uuid4())
    
    # Store initial status
    executions[execution_id] = {
        "status": "in_progress"
    }
    
    # Execute search in background
    background_tasks.add_task(perform_search, execution_id, request.parameters)
    
    return ToolResponse(
        status="in_progress",
        execution_id=execution_id
    )

@app.get("/tools/searxng_search/executions/{execution_id}", response_model=ToolResponse)
async def get_execution_status(execution_id: str):
    if execution_id not in executions:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    execution = executions[execution_id]
    
    return ToolResponse(
        status=execution["status"],
        result=execution.get("result"),
        error=execution.get("error"),
        execution_id=execution_id
    )

# Main entry point
if __name__ == "__main__":
    # Start SearXNG in the background
    start_searxng()
    
    # Give SearXNG a moment to start up
    asyncio.run(asyncio.sleep(2))
    
    # Start FastAPI with Uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
