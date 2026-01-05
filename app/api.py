"""FastAPI backend for the research agent."""
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agent.graph import run_research

app = FastAPI(title="Research Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo (use Redis in production)
research_jobs: dict = {}


class ResearchRequest(BaseModel):
    """Request model for research queries."""
    query: str


class ResearchResponse(BaseModel):
    """Response model for research results."""
    job_id: str
    status: str
    report: Optional[str] = None
    sources: Optional[list] = None
    error: Optional[str] = None


async def execute_research(job_id: str, query: str):
    """Execute research in background."""
    try:
        result = await run_research(query)
        research_jobs[job_id] = {
            "status": "complete",
            "result": result
        }
    except Exception as e:
        research_jobs[job_id] = {
            "status": "error",
            "error": str(e)
        }


@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start a new research job."""
    job_id = str(uuid.uuid4())
    research_jobs[job_id] = {"status": "running", "result": None}
    
    background_tasks.add_task(execute_research, job_id, request.query)
    
    return ResearchResponse(job_id=job_id, status="running")


@app.get("/research/{job_id}", response_model=ResearchResponse)
async def get_research_status(job_id: str):
    """Get the status of a research job."""
    if job_id not in research_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = research_jobs[job_id]
    
    if job["status"] == "complete":
        result = job["result"]
        return ResearchResponse(
            job_id=job_id,
            status="complete",
            report=result.get("final_report"),
            sources=result.get("sources", [])
        )
    elif job["status"] == "error":
        return ResearchResponse(
            job_id=job_id,
            status="error",
            error=job.get("error")
        )
    
    return ResearchResponse(job_id=job_id, status="running")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Research Agent API",
        "version": "1.0.0",
        "endpoints": {
            "POST /research": "Start a research job",
            "GET /research/{job_id}": "Get research job status",
            "GET /health": "Health check"
        }
    }

