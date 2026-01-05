"""
MCP Server for SQLite database operations.

Tools:
- query_database: Execute SELECT queries
- list_tables: Show available tables
- describe_table: Get table schema
"""
import asyncio
import json
import sqlite3
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("database-server")

DATABASE_PATH = "./data/research.db"


def get_connection():
    """Get a database connection."""
    return sqlite3.connect(DATABASE_PATH)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="query_database",
            description="Execute a read-only SQL query on the research database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_tables",
            description="List all tables in the database",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="describe_table",
            description="Get the schema of a specific table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to describe"
                    }
                },
                "required": ["table_name"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if name == "query_database":
            query = arguments.get("query", "").strip().upper()
            if not query.startswith("SELECT"):
                return [TextContent(
                    type="text",
                    text="Error: Only SELECT queries are allowed"
                )]

            cursor.execute(arguments["query"])
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            result = {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            }
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]

        elif name == "list_tables":
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            return [TextContent(
                type="text",
                text=json.dumps({"tables": tables})
            )]

        elif name == "describe_table":
            table_name = arguments.get("table_name", "")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema = [
                {
                    "name": c[1],
                    "type": c[2],
                    "nullable": not c[3]
                }
                for c in columns
            ]
            return [TextContent(
                type="text",
                text=json.dumps(schema, indent=2)
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Database error: {str(e)}"
        )]
    finally:
        conn.close()

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())

