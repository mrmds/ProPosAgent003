#!/usr/bin/env python3
"""
Example client for the SearXNG MCP.
This script demonstrates how to interact with the SearXNG MCP service.
"""

import requests
import time
import argparse
import json


def search_with_searxng_mcp(query, mcp_url="http://localhost:8081", num_results=5, language="all", categories=None):
    """
    Perform a search using the SearXNG MCP.
    
    Args:
        query (str): The search query
        mcp_url (str): Base URL of the SearXNG MCP
        num_results (int): Number of results to return
        language (str): Language filter
        categories (list): List of search categories
        
    Returns:
        dict: Search results or error message
    """
    if categories is None:
        categories = ["general"]
    
    # Step 1: Discover available tools
    try:
        tools_response = requests.get(f"{mcp_url}/tools")
        if tools_response.status_code != 200:
            return {
                "error": f"Failed to discover tools: HTTP {tools_response.status_code}",
                "details": tools_response.text
            }
        
        tools = tools_response.json()
        search_tool = None
        
        # Find the search tool
        for tool in tools:
            if "search" in tool["name"].lower():
                search_tool = tool
                break
        
        if not search_tool:
            return {"error": "Search tool not found in MCP"}
        
        tool_id = search_tool["id"]
        
        # Step 2: Execute search
        search_params = {
            "parameters": {
                "query": query,
                "num_results": num_results,
                "language": language,
                "categories": categories
            }
        }
        
        execute_url = f"{mcp_url}/tools/{tool_id}/execute"
        execute_response = requests.post(execute_url, json=search_params)
        
        if execute_response.status_code != 200:
            return {
                "error": f"Failed to execute search: HTTP {execute_response.status_code}",
                "details": execute_response.text
            }
        
        execution_data = execute_response.json()
        execution_id = execution_data.get("execution_id")
        
        if not execution_id:
            return {"error": "No execution ID received"}
        
        # Step 3: Poll for results
        result_url = f"{mcp_url}/tools/{tool_id}/executions/{execution_id}"
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            result_response = requests.get(result_url)
            
            if result_response.status_code != 200:
                return {
                    "error": f"Failed to get results: HTTP {result_response.status_code}",
                    "details": result_response.text
                }
            
            result_data = result_response.json()
            
            if result_data.get("status") == "success":
                return result_data.get("result", {})
            elif result_data.get("status") == "error":
                return {"error": result_data.get("error", "Unknown error")}
            
            # Wait before polling again
            time.sleep(0.5)
        
        return {"error": "Timed out waiting for results"}
    
    except requests.RequestException as e:
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def format_results(results):
    """Format search results for display."""
    if "error" in results:
        return f"Error: {results['error']}"
    
    if "results" not in results or not results["results"]:
        return "No results found."
    
    output = []
    for i, result in enumerate(results["results"], 1):
        output.append(f"{i}. {result.get('title', 'No title')}")
        output.append(f"   URL: {result.get('url', 'No URL')}")
        if "content" in result:
            content = result["content"]
            if len(content) > 100:
                content = content[:97] + "..."
            output.append(f"   {content}")
        output.append("")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Search with SearXNG MCP")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--url", default="http://localhost:8081", help="SearXNG MCP URL")
    parser.add_argument("--results", type=int, default=5, help="Number of results")
    parser.add_argument("--language", default="all", help="Language filter")
    parser.add_argument("--categories", default="general", help="Categories (comma-separated)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    
    args = parser.parse_args()
    categories = args.categories.split(",")
    
    results = search_with_searxng_mcp(
        args.query,
        mcp_url=args.url,
        num_results=args.results,
        language=args.language,
        categories=categories
    )
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results))


if __name__ == "__main__":
    main()
