from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import os
from dotenv import load_dotenv
from backend.core.parser import analyze_repo
from backend.core.llm import generate_architecture_summary, generate_mermaid

from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="AutoArchitect API", description="GenAI-powered Repo Architecture Analyzer")

# Configure CORS
# In dev we allow localhost ports; in prod we optionally read allowed origins
# from FRONTEND_ORIGINS env var (comma-separated), e.g.
# FRONTEND_ORIGINS="https://autoarchitect-1.onrender.com"
default_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
]

frontend_origins_env = os.getenv("FRONTEND_ORIGINS")
if frontend_origins_env:
    allowed_origins = default_origins + [o.strip() for o in frontend_origins_env.split(",") if o.strip()]
else:
    allowed_origins = default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store for MVP
jobs: Dict[str, Dict[str, Any]] = {}

class AnalyzeRequest(BaseModel):
    repo_url: str
    github_token: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str # "queued", "processing", "completed", "failed"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def process_repo_task(job_id: str, repo_url: str, github_token: Optional[str]):
    try:
        jobs[job_id]["status"] = "processing"
        
        # Use provided token or fall back to environment variable
        token = github_token or os.getenv("GITHUB_TOKEN")
        
        # 1. Deterministic Analysis
        print(f"[{job_id}] Starting analysis for {repo_url}")
        graph_data = analyze_repo(repo_url, token)
        
        # 2. GenAI Reasoning
        print(f"[{job_id}] Generating summary and diagrams")
        summary = generate_architecture_summary(graph_data)
        mermaid_code = generate_mermaid(graph_data)
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = {
            "graph": graph_data,
            "summary": summary,
            "mermaid": mermaid_code
        }
        print(f"[{job_id}] Completed")
        
    except Exception as e:
        print(f"[{job_id}] Failed: {str(e)}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.post("/analyze", response_model=JobStatus)
async def analyze_repository(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "repo_url": request.repo_url
    }
    background_tasks.add_task(process_repo_task, job_id, request.repo_url, request.github_token)
    return JobStatus(**jobs[job_id])

@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(**jobs[job_id])

@app.get("/")
async def root():
    return {"message": "AutoArchitect API is running on Port 8001. Use /analyze to start a job."}
