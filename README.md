# CogniResearch

An AI-powered research assistant that autonomously researches topics, synthesizes information, and generates comprehensive reports. Built with LangGraph for workflow orchestration, Claude for reasoning, and MCP for tool integration.

## Tech Stack

<div align="center">

### AI & Orchestration
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-blue)
![LangChain](https://img.shields.io/badge/LangChain-0.3+-green)
![Claude](https://img.shields.io/badge/Claude%20Sonnet-4-orange)
![Anthropic](https://img.shields.io/badge/Anthropic-API-red)

### Tools & Protocol
![MCP](https://img.shields.io/badge/MCP-1.0+-purple)
![Tavily](https://img.shields.io/badge/Tavily-API-9cf)

### Data & Memory
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5+-yellow)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey)

### Backend & Frontend
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B)
![Uvicorn](https://img.shields.io/badge/Uvicorn-0.32+-499848)

### Language & Framework
![Python](https://img.shields.io/badge/Python-3.11+-3776AB)
![Pydantic](https://img.shields.io/badge/Pydantic-2.9+-E92063)

### Testing & Quality
![Pytest](https://img.shields.io/badge/Pytest-8.0+-0A9EDC)
![Ruff](https://img.shields.io/badge/Ruff-0.7+-F7B93E)

</div>

#### Technology Details

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Orchestration** | LangGraph | Agent workflow and state management |
| **LLM** | Claude Sonnet 4 | Primary language model for research and writing |
| **Protocol** | MCP | Model Context Protocol for tool integration |
| **Memory** | ChromaDB | Persistent vector storage for research findings |
| **Database** | SQLite | Structured data storage |
| **Search** | Tavily API | Web search and content extraction |
| **Backend** | FastAPI | RESTful API server |
| **Frontend** | Streamlit | Interactive web interface |
| **Framework** | LangChain | LLM orchestration and tool integration |

---

## Architecture

The Research Agent uses a three-stage iterative workflow:

1. **Research Node**: Searches the web, queries memory, and collects sources
2. **Write Node**: Synthesizes findings into a structured report
3. **Reflect Node**: Evaluates completeness and loops back if needed

### System Components

- **LangGraph**: Orchestrates the workflow and manages state
- **Claude LLM**: Powers reasoning, writing, and evaluation
- **Tool Registry**: Provides web search (Tavily) and memory (ChromaDB) access
- **ChromaDB**: Stores research findings for semantic search
- **FastAPI/Streamlit**: User interfaces
- **MCP Servers**: Standalone servers for web search, memory, database, and filesystem operations

## Features

- **Web Search**: Search the web using Tavily API
- **Persistent Memory**: Store and retrieve research findings with ChromaDB
- **Structured Reports**: Generate well-organized research reports
- **Self-Reflection**: Agent reviews its own work and improves iteratively
- **MCP Integration**: Modular tool system using Model Context Protocol
- **Multiple Interfaces**: FastAPI backend and Streamlit frontend

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd research-agent
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
# or using uv
uv pip install -e ".[dev]"
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Initialize data directories:
```bash
mkdir -p data/chroma
python -c "from src.mcp_servers.database_server import get_connection; conn = get_connection(); conn.close()"
```

## Usage

### Running MCP Servers

The MCP servers can be run as standalone processes (they use stdio for communication):

```bash
# Terminal 1: Web Search Server
python -m src.mcp_servers.web_search_server

# Terminal 2: Memory Server
python -m src.mcp_servers.memory_server

# Terminal 3: Database Server
python -m src.mcp_servers.database_server
```

**Note**: In the current implementation, the agent uses direct tool calls rather than MCP servers. The MCP servers are included for future integration or standalone use.

### Running the FastAPI Backend

```bash
uvicorn app.api:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

### Running the Streamlit Interface

```bash
streamlit run app/streamlit_app.py
```

The interface will open in your browser at `http://localhost:8501`.

## Project Structure

```
research-agent/
├── src/
│   ├── agent/              # LangGraph agent implementation
│   │   ├── graph.py        # Main agent graph
│   │   ├── nodes.py        # Agent nodes (research, write, reflect)
│   │   ├── state.py        # Agent state definition
│   │   └── prompts.py      # System prompts
│   ├── mcp_servers/        # MCP server implementations
│   │   ├── web_search_server.py
│   │   ├── memory_server.py
│   │   ├── database_server.py
│   │   └── filesystem_server.py
│   ├── memory/             # ChromaDB integration
│   │   └── knowledge_base.py
│   ├── tools/              # Tool registry
│   │   └── tool_registry.py
│   └── utils/              # Utilities
│       ├── config.py
│       └── logging.py
├── app/
│   ├── api.py             # FastAPI backend
│   └── streamlit_app.py   # Streamlit frontend
├── tests/                 # Test suite
├── configs/               # Configuration files
├── data/                  # Data directory (gitignored)
├── pyproject.toml         # Project configuration
├── .env.example           # Environment template
└── README.md             # This file
```

## How It Works

The research agent follows a three-stage workflow:

1. **Research Node**: Searches the web for information using Tavily, stores important findings in ChromaDB memory, and gathers sources.

2. **Writer Node**: Synthesizes the research notes into a comprehensive, well-structured report with proper citations.

3. **Reflector Node**: Reviews the report for completeness and quality. If gaps are found, it loops back to the Research Node for additional information.

The agent continues this cycle until the report is satisfactory or a maximum iteration limit is reached.

## Configuration

All configuration is done through environment variables (see `.env.example`):

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `TAVILY_API_KEY`: Your Tavily API key (required)
- `MODEL_NAME`: Claude model to use (default: claude-sonnet-4-20250514)
- `MAX_TOKENS`: Maximum tokens per response (default: 4096)
- `TEMPERATURE`: Model temperature (default: 0.7)
- `MAX_ITERATIONS`: Maximum research iterations (default: 10)
- `CHROMA_PATH`: Path to ChromaDB data directory
- `DATABASE_PATH`: Path to SQLite database

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
ruff format src/ app/ tests/
ruff check src/ app/ tests/
```

## API Endpoints

- `POST /research`: Start a new research job
- `GET /research/{job_id}`: Get the status and results of a research job
- `GET /health`: Health check endpoint
- `GET /`: API information

## What This Does

The Research Agent is an autonomous AI system that:

1. **Researches Topics**: Searches the web for current information using Tavily API
2. **Maintains Memory**: Stores findings in ChromaDB for semantic search across sessions
3. **Synthesizes Reports**: Uses Claude LLM to create well-structured, cited reports
4. **Self-Improves**: Reflects on output quality and iteratively refines results
5. **Tracks Sources**: Maintains a comprehensive list of sources with URLs

### Example Workflow

**Input Query**: "What are the latest developments in quantum computing error correction?"

**Step 1 - Research Node**:
- Claude LLM decides what information is needed
- Searches Tavily API for recent quantum computing news
- Queries ChromaDB for previously stored related research
- Stores key findings in memory
- Collects 5-7 relevant source URLs

**Step 2 - Write Node**:
- Receives research notes and sources
- Claude synthesizes into structured report:
  - Executive summary
  - Main sections with citations
  - Key takeaways
  - Source list

**Step 3 - Reflect Node**:
- Claude evaluates if report fully answers the query
- Checks for completeness and accuracy
- If gaps found: loops back to Research Node
- If complete: returns final report

**Output**: Comprehensive report with citations, ready for review

## Example Usage

### Example 1: Using the Streamlit Interface

1. Start the Streamlit app:
```bash
cd research-agent
source venv/bin/activate
PYTHONPATH=. streamlit run app/streamlit_app.py
```

2. Enter a research query:
   - "What are the latest breakthroughs in quantum computing?"
   - "Explain how LangGraph works for agent orchestration"
   - "Compare FastAPI and Flask for building APIs"

3. Click "Research" button and watch the agent work

4. View the generated report with:
   - Structured sections
   - Inline citations
   - Source URLs
   - Research notes (optional)

### Example 2: Using the FastAPI Backend

Start the API server:
```bash
uvicorn app.api:app --reload --port 8000
```

Submit a research job:
```python
import requests
import time

# Start a research job
response = requests.post("http://localhost:8000/research", json={
    "query": "What are the benefits and challenges of renewable energy?"
})
job_id = response.json()["job_id"]
print(f"Research job started: {job_id}")

# Poll for results
while True:
    result = requests.get(f"http://localhost:8000/research/{job_id}").json()
    
    if result["status"] == "complete":
        print("\n=== Research Report ===\n")
        print(result["report"])
        print("\n=== Sources ===\n")
        for source in result.get("sources", []):
            print(f"- {source.get('title', 'Unknown')}: {source.get('url', 'N/A')}")
        break
    elif result["status"] == "error":
        print(f"Error: {result['error']}")
        break
    else:
        print(f"Status: {result['status']}... waiting")
        time.sleep(2)
```

### Example 3: Direct Python Usage

```python
import asyncio
from src.agent.graph import run_research

async def research_topic():
    query = "What is LangGraph and how does it work?"
    
    result = await run_research(query)
    
    print("Query:", result["query"])
    print("\nFinal Report:")
    print(result.get("final_report", "No report generated"))
    print("\nSources:")
    for source in result.get("sources", []):
        print(f"- {source.get('title')}: {source.get('url')}")
    print(f"\nIterations: {result.get('iteration_count', 0)}")

# Run the research
asyncio.run(research_topic())
```

### Example Output

Here's what a completed research report looks like:

```
Research Report: Latest Developments in Quantum Computing Error Correction

Executive Summary:
Quantum error correction has seen significant advances in 2024, with new 
approaches to fault-tolerant quantum computing and improved error rates in 
physical qubits.

1. Surface Code Improvements
Recent developments in surface code implementations have shown promise...
[Source: Nature Quantum Information, 2024]

2. Quantum Error Correction Algorithms
New algorithms for error correction have reduced overhead by 30%...
[Source: arXiv:2401.12345]

3. Hardware Advances
Physical qubit error rates have improved to 0.1% in recent experiments...
[Source: IBM Research Blog, 2024]

Key Takeaways:
- Surface codes remain the most practical approach
- Error rates continue to improve
- Scaling remains the primary challenge

Sources:
1. "Quantum Error Correction Advances" - https://example.com/quantum-errors
2. "Surface Code Improvements" - https://example.com/surface-code
3. "Hardware Error Rates" - https://example.com/hardware-errors
```

### Real-World Use Cases

- **Research**: Quickly gather and synthesize information on complex topics
- **Content Creation**: Generate well-researched articles with citations
- **Due Diligence**: Research companies, technologies, or markets
- **Learning**: Get comprehensive overviews of new topics
- **Documentation**: Research and document technical concepts
- **News Analysis**: Synthesize information from multiple sources

## Limitations

- The current implementation uses direct tool calls rather than MCP protocol communication
- MCP servers are provided but need additional integration for full protocol support
- In-memory job storage (use Redis for production)

## Future Enhancements

- Full MCP protocol integration
- More specialized research agents
- Human-in-the-loop approval workflows
- Enhanced evaluation and quality metrics
- LangSmith integration for observability
- Docker deployment configuration


