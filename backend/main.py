from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.agent.runner import run_automation_tests
from backend.agent.analyzer import analyze_test_run
from backend.database.core import init_db, get_db
from backend.database.models import Bug
from backend.schemas import BugSchema
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import os
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="AI QA Agent Platform API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount artifacts directory for static file serving
# Ensure the directory exists
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_DIR), name="artifacts")

# Simple in-memory state
job_store: Dict[str, Any] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str
    logs: List[str] = []
    exit_code: Optional[int] = None
    bugs: List[Dict[str, Any]] = []

@app.get("/health")
def health_check():
    return {"status": "ok"}

def execute_tests_task(job_id: str):
    job_store[job_id]["status"] = "RUNNING"
    try:
        result = run_automation_tests()
        job_store[job_id].update(result)
        
        # Analyze failures
        if result["status"] == "FAILED":
             bugs = analyze_test_run(result)
             job_store[job_id]["bugs"] = bugs
        else:
             job_store[job_id]["bugs"] = []
             
    except Exception as e:
        job_store[job_id]["status"] = "ERROR"
        job_store[job_id]["logs"].append(str(e))

@app.post("/run-tests")
def trigger_tests(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"job_id": job_id, "status": "PENDING", "logs": [], "bugs": []}
    background_tasks.add_task(execute_tests_task, job_id)
    return {"job_id": job_id, "status": "PENDING"}

@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    return job_store.get(job_id, {"job_id": job_id, "status": "NOT_FOUND", "logs": [], "bugs": []})

@app.get("/bugs", response_model=List[BugSchema])
def list_bugs(db: Session = Depends(get_db)):
    return db.query(Bug).order_by(Bug.created_at.desc()).all()
