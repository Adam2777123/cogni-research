"""Streamlit demo interface for the research agent."""
import asyncio
import streamlit as st
from langchain_core.messages import HumanMessage

from src.agent.graph import create_research_agent
from src.agent.state import ResearchState
from src.utils.config import get_settings

settings = get_settings()

st.set_page_config(
    page_title="CogniResearch",
    page_icon=None,
    layout="wide"
)

st.title("CogniResearch")
st.markdown("*Powered by Claude + MCP + LangGraph*")

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    max_iterations = st.slider("Max Research Iterations", 1, 10, settings.max_iterations)
    show_steps = st.checkbox("Show Research Steps", value=True)
    
    st.divider()
    st.markdown("### About")
    st.markdown("""
    This research assistant:
    - Searches the web for information
    - Maintains memory across queries
    - Writes structured reports
    - Self-reflects and improves
    """)

# Main interface
query = st.text_area(
    "What would you like me to research?",
    placeholder="e.g., What are the latest developments in quantum computing?",
    height=100
)

col1, col2 = st.columns([1, 5])
with col1:
    research_button = st.button("Research", type="primary", use_container_width=True)

if research_button and query:
    with st.spinner("Researching..."):
        # Progress tracking
        progress_container = st.empty()
        steps_container = st.container()
        status_container = st.empty()
        
        # Run research
        async def run_with_progress():
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
            
            step_count = 0
            final_result = None
            
            async for state in agent.astream(initial_state):
                step_count += 1
                step_name = list(state.keys())[0] if state else "unknown"
                
                if show_steps:
                    with steps_container:
                        st.write(f"**Step {step_count}**: {step_name}")
                
                progress_container.progress(
                    min(step_count / (max_iterations * 3), 1.0),
                    text=f"Running {step_name}..."
                )
                
                # Update status
                if state:
                    node_state = list(state.values())[0]
                    if isinstance(node_state, dict):
                        status_container.info(
                            f"Current step: {node_state.get('current_step', 'unknown')} | "
                            f"Iteration: {node_state.get('iteration_count', 0)}/{max_iterations}"
                        )
                
                final_result = state
            
            return final_result
        
        result = asyncio.run(run_with_progress())
        
        # Display results
        st.divider()
        progress_container.empty()
        status_container.empty()
        
        if result:
            # Extract final state from the last node
            final_states = list(result.values())
            if final_states:
                final_state = final_states[-1]
                
                if isinstance(final_state, dict):
                    if final_state.get("final_report"):
                        st.header("Research Report")
                        st.markdown(final_state["final_report"])
                        
                        if final_state.get("sources"):
                            st.header("Sources")
                            for source in final_state["sources"]:
                                st.markdown(
                                    f"- **{source.get('title', 'Source')}**: "
                                    f"[{source.get('url', '#')}]({source.get('url', '#')})"
                                )
                        
                        # Show research notes if available
                        if final_state.get("research_notes") and show_steps:
                            with st.expander("View Research Notes"):
                                for i, note in enumerate(final_state["research_notes"], 1):
                                    st.text_area(f"Note {i}", note, height=100, disabled=True)
                    
                    elif final_state.get("error"):
                        st.error(f"Research failed: {final_state['error']}")
                    else:
                        st.warning("Research completed but no report was generated.")
        else:
            st.warning("No results returned")

# Footer
st.divider()
st.markdown("*Built with LangGraph, MCP, and Claude*")

