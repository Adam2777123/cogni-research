"""Tests for MCP servers."""
import pytest
import os


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires API keys")
async def test_web_search_tool():
    """Test web search tool execution."""
    from src.tools.tool_registry import create_web_search_tool
    
    tool = create_web_search_tool()
    result = tool.invoke({"query": "Python programming", "max_results": 3})
    
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_memory_tools():
    """Test memory storage and retrieval."""
    from src.tools.tool_registry import create_memory_tools
    
    tools = create_memory_tools()
    store_tool = next(t for t in tools if t.name == "store_memory")
    search_tool = next(t for t in tools if t.name == "search_memory")
    
    # Store a memory
    store_result = store_tool.invoke({
        "content": "The capital of France is Paris",
        "metadata": "{\"topic\": \"geography\"}"
    })
    assert "stored" in store_result.lower() or "ID" in store_result
    
    # Search for it
    search_result = search_tool.invoke({
        "query": "capital of France",
        "n_results": 1
    })
    assert isinstance(search_result, str)
    assert len(search_result) > 0

