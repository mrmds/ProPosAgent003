# SearXNG MCP

This MCP (Master Control Program) integrates [SearXNG](https://github.com/searxng/searxng) as a service that can be used by ProPosAgent.

## Features

- Provides privacy-focused web search capabilities to ProPosAgent
- Exposes SearXNG functionality through MCP protocol
- Supports customizable search parameters (language, categories, etc.)
- Runs as a containerized service

## Building and Running

Build the Docker image:

```bash
docker build -t mcp-searxng:latest -f Dockerfile .
```

Run the container:

```bash
docker run -p 8080:8080 --name searxng01 searxng01
```

If port 8080 is already in use, you can map to a different port:

```bash
docker run -p 8081:8080 --name searxng01 searxng01
```

## MCP Configuration

Add the following to your `mcp.env` file to register this MCP server:

```
MCP_SERVER_3_NAME=SearXNG Search
MCP_SERVER_3_URL=http://localhost:8080
MCP_SERVER_3_AUTH_TYPE=none
MCP_SERVER_3_DESCRIPTION=Privacy-focused web search capabilities
```

## Usage

Once configured, you can use the SearXNG search tool in your agent:

```python
# Discover available tools on the SearXNG MCP
tools = await agent.tools.discover_mcp_tools(server_id="searxng")

# Execute a search
result = await agent.tools.call_mcp_tool(
    server_id="searxng",
    tool_id="searxng_search",
    parameters={
        "query": "your search query",
        "num_results": 5,
        "language": "en"
    }
)
```

## Advanced Configuration

You can customize the SearXNG settings by modifying the `settings.yml` file before building the Docker image.
