from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from backend.agent.runner import run_automation_tests
from backend.agent.analyzer import analyze_test_run
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
    bugs: List[Dict[str, Any]] = []

@app.get("/health")
def health_check():
    return {"status": "ok"}

def execute_tests_task(job_id: str):
    job_store[job_id]["status"] = "RUNNING"
    try:
        result = run_automation_tests()
        job_store[job_id].update(result) # status, logs, exit_code, report_data, report_file
        
        # Analyze failures
        if result["status"] == "FAILED":
             # We might want to set status to "ANALYZING" but let's keep it simple
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
