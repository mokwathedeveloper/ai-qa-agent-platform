from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from backend.agent.runner import run_automation_tests
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid

app = FastAPI(title="AI QA Agent Platform API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory state
job_store: Dict[str, Any] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str
    logs: List[str] = []
    exit_code: Optional[int] = None

@app.get("/health")
def health_check():
    return {"status": "ok"}

def execute_tests_task(job_id: str):
    job_store[job_id]["status"] = "RUNNING"
    try:
        result = run_automation_tests()
        job_store[job_id].update(result) # status, logs, exit_code
    except Exception as e:
        job_store[job_id]["status"] = "ERROR"
        job_store[job_id]["logs"].append(str(e))

@app.post("/run-tests")
def trigger_tests(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"job_id": job_id, "status": "PENDING", "logs": []}
    background_tasks.add_task(execute_tests_task, job_id)
    return {"job_id": job_id, "status": "PENDING"}

@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    return job_store.get(job_id, {"job_id": job_id, "status": "NOT_FOUND", "logs": []})