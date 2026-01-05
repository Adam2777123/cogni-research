"""Agent state definition for LangGraph."""
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ResearchState(TypedDict):
    """State for the research agent."""

    # Core conversation
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Research context
    query: str
    research_notes: list[str]
    sources: list[dict]

    # Agent control
    current_step: str
    iteration_count: int
    should_continue: bool

    # Output
    final_report: str | None
    error: str | None

