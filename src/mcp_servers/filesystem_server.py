"""
MCP Server for filesystem operations.

Tools:
- read_file: Read contents of a file
- write_file: Write content to a file
- list_directory: List files in a directory
- search_files: Search for files by name pattern
"""
import asyncio
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("filesystem-server")

# Base directory for file operations (can be restricted)
BASE_DIR = Path(os.getenv("FILESYSTEM_BASE_DIR", ".")).resolve()


def ensure_safe_path(file_path: str) -> Path:
    """Ensure the file path is within the base directory."""
    resolved = (BASE_DIR / file_path).resolve()
    if not str(resolved).startswith(str(BASE_DIR)):
        raise ValueError(f"Path {file_path} is outside allowed directory")
    return resolved


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="read_file",
            description="Read the contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read (relative to base directory)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["file_path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="List files and directories in a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path to the directory",
                        "default": "."
                    }
                }
            }
        ),
        Tool(
            name="search_files",
            description="Search for files by name pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "File name pattern (e.g., '*.txt')"
                    },
                    "directory_path": {
                        "type": "string",
                        "description": "Directory to search in",
                        "default": "."
                    }
                },
                "required": ["pattern"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "read_file":
            file_path = ensure_safe_path(arguments.get("file_path", ""))
            if not file_path.exists():
                return [TextContent(
                    type="text",
                    text=f"Error: File not found: {file_path}"
                )]

            content = file_path.read_text(encoding="utf-8")
            return [TextContent(type="text", text=content)]

        elif name == "write_file":
            file_path = ensure_safe_path(arguments.get("file_path", ""))
            content = arguments.get("content", "")

            # Create parent directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content, encoding="utf-8")
            return [TextContent(
                type="text",
                text=f"Successfully wrote {len(content)} characters to {file_path}"
            )]

        elif name == "list_directory":
            dir_path = ensure_safe_path(arguments.get("directory_path", "."))
            if not dir_path.is_dir():
                return [TextContent(
                    type="text",
                    text=f"Error: Not a directory: {dir_path}"
                )]

            items = []
            for item in sorted(dir_path.iterdir()):
                item_type = "DIR" if item.is_dir() else "FILE"
                items.append(f"{item_type}: {item.name}")

            return [TextContent(
                type="text",
                text="\n".join(items) if items else "Directory is empty"
            )]

        elif name == "search_files":
            pattern = arguments.get("pattern", "")
            dir_path = ensure_safe_path(arguments.get("directory_path", "."))

            if not dir_path.is_dir():
                return [TextContent(
                    type="text",
                    text=f"Error: Not a directory: {dir_path}"
                )]

            matches = list(dir_path.rglob(pattern))
            results = [str(m.relative_to(BASE_DIR)) for m in matches]

            return [TextContent(
                type="text",
                text="\n".join(results) if results else f"No files found matching {pattern}"
            )]

    except ValueError as e:
        return [TextContent(type="text", text=f"Security error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())

