"""LangGraph state machine for the research agent."""
from langgraph.graph import StateGraph, END

from .state import ResearchState
from .nodes import researcher_node, writer_node, reflector_node, should_continue


def create_research_agent():
    """Create the LangGraph research agent."""
    
    # Initialize graph
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("research", researcher_node)
    workflow.add_node("write", writer_node)
    workflow.add_node("reflect", reflector_node)
    
    # Set entry point
    workflow.set_entry_point("research")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "research",
        should_continue,
        {
            "write": "write",
            "error": END,
            "complete": END
        }
    )
    
    workflow.add_conditional_edges(
        "write",
        should_continue,
        {
            "reflect": "reflect",
            "error": END,
            "complete": END
        }
    )
    
    workflow.add_conditional_edges(
        "reflect",
        should_continue,
        {
            "research": "research",  # Loop back for more research
            "complete": END,
            "error": END
        }
    )
    
    # Compile
    return workflow.compile()


async def run_research(query: str) -> dict:
    """Run a research query through the agent.
    
    Args:
        query: The research query
        
    Returns:
        Final state dictionary
    """
    from langchain_core.messages import HumanMessage
    
    agent = create_research_agent()
    
    initial_state: ResearchState = {
        "messages": [HumanMessage(content=query)],
        "query": query,
        "research_notes": [],
        "sources": [],
        "current_step": "",
        "iteration_count": 0,
        "should_continue": True,
        "final_report": None,
        "error": None
    }
    
    # Run with streaming
    final_state = None
    async for state in agent.astream(initial_state):
        final_state = state
    
    # Extract the last node's state
    if final_state:
        # Get the state from the last completed node
        node_states = list(final_state.values())
        if node_states:
            return node_states[-1]
    
    return initial_state

