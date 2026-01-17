from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.agent.runner import run_automation_tests
from backend.agent.analyzer import analyze_test_run
from backend.database.core import init_db, get_db, SessionLocal
from backend.database.models import Job, Bug
from backend.schemas import BugSchema, TestRunRequest, JobSchema
from backend.config import settings
from backend.websocket import manager
from pydantic import BaseModel, ConfigDict, ValidationError
from typing import List, Optional, Dict, Any
import uuid
import os
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="AI QA Agent Platform API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount artifacts directory for static file serving
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_DIR), name="artifacts")

class JobStatusResponse(JobSchema):
    bugs: List[BugSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    try:
        # Keep connection alive - no need to process incoming messages
        while True:
            await websocket.receive_text()  # Just consume ping/pong messages
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
    except Exception as e:
        print(f"WebSocket error for job {job_id}: {e}")
        manager.disconnect(websocket, job_id)

async def execute_tests_task(job_id: str, test_url: str, provider: str, context: Dict[str, str]):
    db = SessionLocal()
    try:
        # Fetch the job and set status to RUNNING
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        
        job.status = "RUNNING"
        job.logs.append("Starting Playwright tests...")
        db.commit()
        
        # Send WebSocket update
        await manager.send_job_update(job_id, {
            "status": "RUNNING",
            "logs": job.logs,
            "message": "Tests are running..."
        })

        # Run the tests
        result = run_automation_tests(test_url)
        
        # Update job with results
        job.status = result.get("status", "ERROR")
        job.logs.extend(result.get("logs", []))
        
        # Analyze failures
        bugs = []
        if job.status == "FAILED":
            bugs = analyze_test_run(job_id, result, context, provider, db)
            job.logs.append(f"Found {len(bugs)} potential bugs.")
        
        db.commit()
        
        # Send final WebSocket update
        await manager.send_job_update(job_id, {
            "status": job.status,
            "logs": job.logs,
            "bugs": bugs,
            "message": f"Tests completed with status: {job.status}"
        })
             
    except Exception as e:
        # Ensure job status is updated on unexpected error
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "ERROR"
            error_msg = f"An unexpected error occurred: {str(e)}"
            job.logs.append(error_msg)
            db.commit()
            
            # Send error WebSocket update
            await manager.send_job_update(job_id, {
                "status": "ERROR",
                "logs": job.logs,
                "message": error_msg
            })
    finally:
        db.close()

@app.post("/run-tests", response_model=JobSchema)
async def trigger_tests(background_tasks: BackgroundTasks, request: TestRunRequest, db: Session = Depends(get_db)):
    try:
        # Create a new job record in the database
        new_job = Job(status="PENDING", logs=["Job accepted."])
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        context = {
            "overview": request.cycle_overview or "",
            "instructions": request.testing_instructions or ""
        }
        
        # Add async task to background tasks
        background_tasks.add_task(
            execute_tests_task, 
            new_job.id, 
            request.test_url, 
            request.provider, 
            context
        )
        
        return new_job
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/bugs", response_model=List[BugSchema])
def list_bugs(db: Session = Depends(get_db)):
    return db.query(Bug).order_by(Bug.created_at.desc()).all()
