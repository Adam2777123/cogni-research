"""Agent nodes for the research workflow."""
import json
import re
import uuid
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import Tool

from .state import ResearchState
from .prompts import RESEARCHER_PROMPT, WRITER_PROMPT, REFLECTOR_PROMPT
from ..utils.config import get_settings
from ..tools.tool_registry import get_all_tools

settings = get_settings()


def create_llm():
    """Create an LLM instance."""
    return ChatAnthropic(
        model=settings.model_name,
        api_key=settings.anthropic_api_key,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature
    )


def extract_tool_results(messages: list) -> tuple[list[str], list[dict]]:
    """Extract research notes and sources from tool call messages."""
    notes = []
    sources = []
    
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call["name"] == "web_search":
                    # Parse search results
                    result_content = tool_call.get("result", "")
                    if result_content:
                        # Extract sources from search results
                        parts = result_content.split("---")
                        for part in parts:
                            if "URL:" in part:
                                url_match = re.search(r"URL:\s*(.+)", part)
                                title_match = re.search(r"Title:\s*(.+)", part)
                                if url_match:
                                    sources.append({
                                        "title": title_match.group(1).strip() if title_match else "Unknown",
                                        "url": url_match.group(1).strip()
                                    })
                                notes.append(part.strip())
    
    return notes, sources


async def researcher_node(state: ResearchState) -> ResearchState:
    """
    Research node: Searches for information and gathers sources.
    Uses web_search and memory tools.
    """
    llm = create_llm()
    tools = get_all_tools()
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Check memory first
    memory_tool = next((t for t in tools if t.name == "search_memory"), None)
    memory_context = ""
    if memory_tool:
        try:
            memory_results = memory_tool.invoke({"query": state["query"], "n_results": 3})
            if memory_results and "No memories found" not in str(memory_results):
                memory_context = f"\n\nPrevious research findings:\n{memory_results}"
        except Exception:
            pass  # Continue even if memory search fails
    
    messages = [
        SystemMessage(content=RESEARCHER_PROMPT),
        HumanMessage(
            content=(
                f"Research this topic: {state['query']}\n\n"
                f"Current notes: {', '.join(state['research_notes'][:3]) if state['research_notes'] else 'None'}"
                f"{memory_context}"
            )
        )
    ]
    
    try:
        response = await llm_with_tools.ainvoke(messages)
        
        # Execute tool calls if any
        if hasattr(response, "tool_calls") and response.tool_calls:
            from langchain_core.messages import ToolMessage
            
            tool_results = []
            tool_messages = []
            
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None)
                tool_args = tool_call.get("args") if isinstance(tool_call, dict) else getattr(tool_call, "args", {})
                
                tool = next((t for t in tools if t.name == tool_name), None)
                if tool:
                    try:
                        # Handle different tool argument formats
                        if tool_name == "web_search":
                            result = tool.invoke({
                                "query": tool_args.get("query", state["query"]) if isinstance(tool_args, dict) else state["query"],
                                "max_results": tool_args.get("max_results", 5) if isinstance(tool_args, dict) else 5
                            })
                        elif tool_name == "search_memory":
                            result = tool.invoke({
                                "query": tool_args.get("query", state["query"]) if isinstance(tool_args, dict) else state["query"],
                                "n_results": tool_args.get("n_results", 5) if isinstance(tool_args, dict) else 5
                            })
                        elif tool_name == "store_memory":
                            content = tool_args.get("content", "") if isinstance(tool_args, dict) else ""
                            metadata = tool_args.get("metadata", {}) if isinstance(tool_args, dict) else {}
                            result = tool.invoke({
                                "content": content,
                                "metadata": json.dumps(metadata) if isinstance(metadata, dict) else str(metadata)
                            })
                        else:
                            # Convert tool_args to dict if needed
                            if not isinstance(tool_args, dict):
                                tool_args = {}
                            result = tool.invoke(tool_args)
                        
                        tool_results.append(result)
                        
                        # Create ToolMessage for LangChain
                        tool_call_id = tool_call.get("id") if isinstance(tool_call, dict) else getattr(tool_call, "id", str(uuid.uuid4()))
                        tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
                        
                        # Store important findings in memory
                        if tool_name == "web_search" and result:
                            store_tool = next((t for t in tools if t.name == "store_memory"), None)
                            if store_tool:
                                try:
                                    # Extract key findings to store
                                    findings = str(result)[:500]  # First 500 chars
                                    store_tool.invoke({
                                        "content": f"Research on {state['query']}: {findings}",
                                        "metadata": json.dumps({"topic": state["query"]})
                                    })
                                except Exception:
                                    pass  # Continue if storage fails
                    except Exception as e:
                        error_msg = f"Error executing tool: {str(e)}"
                        tool_results.append(error_msg)
                        tool_call_id = tool_call.get("id") if isinstance(tool_call, dict) else getattr(tool_call, "id", str(uuid.uuid4()))
                        tool_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
            
            # Get a follow-up response with tool results
            follow_up_response = await llm_with_tools.ainvoke(
                state["messages"] + [response] + tool_messages
            )
            
            # Extract notes and sources from tool results
            new_notes = []
            new_sources = []
            
            for result in tool_results:
                if isinstance(result, str) and "Title:" in result:
                    # Parse web search results
                    parts = result.split("---")
                    for part in parts:
                        if "URL:" in part:
                            import re
                            url_match = re.search(r"URL:\s*(.+)", part)
                            title_match = re.search(r"Title:\s*(.+)", part)
                            if url_match:
                                new_sources.append({
                                    "title": title_match.group(1).strip() if title_match else "Unknown",
                                    "url": url_match.group(1).strip()
                                })
                            new_notes.append(part.strip())
                elif result and "No memories found" not in str(result):
                    new_notes.append(str(result))
            
            return {
                **state,
                "messages": state["messages"] + [response] + tool_messages + [follow_up_response],
                "research_notes": state["research_notes"] + new_notes,
                "sources": state["sources"] + new_sources,
                "current_step": "research",
                "iteration_count": state["iteration_count"] + 1
            }
        else:
            # No tool calls, just add the response
            return {
                **state,
                "messages": state["messages"] + [response],
                "current_step": "research",
                "iteration_count": state["iteration_count"] + 1
            }
    except Exception as e:
        return {
            **state,
            "error": f"Research error: {str(e)}",
            "current_step": "research"
        }


async def writer_node(state: ResearchState) -> ResearchState:
    """
    Writer node: Synthesizes research into a coherent report.
    """
    llm = create_llm()
    
    research_context = "\n\n".join(state["research_notes"][-10:])  # Last 10 notes
    sources_text = "\n".join([
        f"- {s.get('title', 'Unknown')}: {s.get('url', 'N/A')}"
        for s in state["sources"]
    ])
    
    messages = [
        SystemMessage(content=WRITER_PROMPT),
        HumanMessage(content=f"""
Write a comprehensive research report based on:

QUERY: {state['query']}

RESEARCH NOTES:
{research_context if research_context else 'No research notes available yet.'}

SOURCES:
{sources_text if sources_text else 'No sources found yet.'}

Generate a well-structured report that answers the query completely.
""")
    ]
    
    try:
        response = await llm.ainvoke(messages)
        
        return {
            **state,
            "messages": state["messages"] + [response],
            "final_report": response.content,
            "current_step": "write"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Writing error: {str(e)}",
            "current_step": "write"
        }


async def reflector_node(state: ResearchState) -> ResearchState:
    """
    Reflector node: Reviews the report and decides if more research is needed.
    """
    llm = create_llm()
    
    if not state.get("final_report"):
        return {
            **state,
            "should_continue": True,
            "current_step": "reflect"
        }
    
    messages = [
        SystemMessage(content=REFLECTOR_PROMPT),
        HumanMessage(content=f"""
Review this research report:

ORIGINAL QUERY: {state['query']}

REPORT:
{state['final_report']}

EVALUATE:
1. Does it fully answer the query?
2. Are there gaps that need more research?
3. Is the information accurate and well-sourced?

Respond with either:
- "COMPLETE" if the report is satisfactory
- "NEEDS_RESEARCH: <specific gaps to fill>" if more research is needed
""")
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = response.content.upper()
        
        needs_more = "NEEDS_RESEARCH" in content or "COMPLETE" not in content
        # Also check iteration limit
        max_iterations_reached = state["iteration_count"] >= settings.max_iterations
        
        return {
            **state,
            "messages": state["messages"] + [response],
            "should_continue": needs_more and not max_iterations_reached,
            "current_step": "reflect"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Reflection error: {str(e)}",
            "should_continue": False,
            "current_step": "reflect"
        }


def should_continue(state: ResearchState) -> str:
    """Routing function to decide next step."""
    if state.get("error"):
        return "error"
    if state["current_step"] == "reflect" and not state["should_continue"]:
        return "complete"
    if state["current_step"] == "reflect" and state["should_continue"]:
        return "research"
    if state["current_step"] == "research":
        return "write"
    if state["current_step"] == "write":
        return "reflect"
    return "research"  # Default starting point

