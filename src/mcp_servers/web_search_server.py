"""
MCP Server for web search using Tavily API.

This server exposes the following tools:
- web_search: Search the web for information
- get_page_content: Get detailed content from a URL
"""
import asyncio
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from tavily import TavilyClient

# Initialize server
server = Server("web-search-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="web_search",
            description=(
                "Search the web for current information on any topic. "
                "Returns relevant snippets and URLs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_page_content",
            description="Fetch and extract the main content from a specific URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch content from"
                    }
                },
                "required": ["url"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return [TextContent(
            type="text",
            text="Error: TAVILY_API_KEY not set in environment"
        )]

    client = TavilyClient(api_key=api_key)

    if name == "web_search":
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)

        try:
            results = client.search(
                query=query,
                max_results=max_results
            )

            formatted_results = []
            for r in results.get("results", []):
                formatted_results.append(
                    f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r.get('content', '')}\n"
                )

            if not formatted_results:
                return [TextContent(
                    type="text",
                    text=f"No results found for query: {query}"
                )]

            return [TextContent(
                type="text",
                text="\n---\n".join(formatted_results)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error searching: {str(e)}"
            )]

    elif name == "get_page_content":
        url = arguments.get("url", "")
        try:
            # Use Tavily's extract feature for clean content
            result = client.extract(urls=[url])
            content = result.get("results", [{}])[0].get("raw_content", "No content found")
            # Limit content length
            return [TextContent(
                type="text",
                text=content[:10000]
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error fetching page content: {str(e)}"
            )]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())

