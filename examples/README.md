# ProPosAgent003 Examples

This directory contains example scripts that demonstrate how to use various components of the ProPosAgent003 system.

## SearXNG MCP Client

The `searxng_client.py` script demonstrates how to interact with the SearXNG MCP service for web search functionality.

### Usage

```bash
python searxng_client.py "your search query" [options]
```

#### Options:

- `--url URL`: SearXNG MCP URL (default: http://localhost:8081)
- `--results N`: Number of results to return (default: 5)
- `--language LANG`: Language filter (default: all)
- `--categories CATS`: Categories to search (comma-separated, default: general)
- `--json`: Output raw JSON instead of formatted results

#### Examples:

Basic search:
```bash
python searxng_client.py "python programming"
```

Specifying more options:
```bash
python searxng_client.py "climate news" --results 10 --language en --categories news,science
```

Get raw JSON output:
```bash
python searxng_client.py "technology trends" --json
```
