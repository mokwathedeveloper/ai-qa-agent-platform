#!/usr/bin/env python3
"""
Minimal Working Backend for Testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta

app = FastAPI(title="AI QA Agent Platform API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# In-memory storage for testing
users_db = {}
jobs_db = {}
bugs_db = {}
active_connections = {}

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TestRunRequest(BaseModel):
    test_url: str
    cycle_overview: Optional[str] = ""
    testing_instructions: Optional[str] = ""
    provider: str = "uTest"

class Job(BaseModel):
    id: str
    status: str
    logs: List[str]
    created_at: str

class Bug(BaseModel):
    id: str
    job_id: str
    summary: str
    test_name: str
    severity: str
    status: str
    steps: str
    actual_result: str
    expected_result: str
    created_at: str

def create_token(username: str) -> str:
    return f"token_{username}_{int(time.time())}"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    for username, user_data in users_db.items():
        if user_data.get("token") == token:
            return username
    raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/register", response_model=Token)
def register(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    token = create_token(user.username)
    users_db[user.username] = {
        "email": user.email,
        "password": user.password,  # In real app, hash this
        "token": token
    }
    
    return Token(access_token=token, token_type="bearer")

@app.post("/login", response_model=Token)
def login(user: UserLogin):
    if user.username not in users_db:
        raise HTTPException(status_code=401, detail="User not found")
    
    stored_user = users_db[user.username]
    if stored_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    token = create_token(user.username)
    users_db[user.username]["token"] = token
    
    return Token(access_token=token, token_type="bearer")

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    if job_id not in active_connections:
        active_connections[job_id] = []
    active_connections[job_id].append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[job_id].remove(websocket)
        if not active_connections[job_id]:
            del active_connections[job_id]

async def send_websocket_update(job_id: str, message: dict):
    if job_id in active_connections:
        disconnected = []
        for connection in active_connections[job_id]:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            active_connections[job_id].remove(conn)

async def simulate_test_execution(job_id: str, test_url: str):
    """Simulate test execution with WebSocket updates"""
    
    # Update job status to RUNNING
    jobs_db[job_id]["status"] = "RUNNING"
    jobs_db[job_id]["logs"].append("Starting test execution...")
    
    await send_websocket_update(job_id, {
        "status": "RUNNING",
        "logs": jobs_db[job_id]["logs"],
        "message": "Tests are running..."
    })
    
    # Simulate test steps
    await asyncio.sleep(2)
    jobs_db[job_id]["logs"].append(f"Testing URL: {test_url}")
    await send_websocket_update(job_id, {
        "status": "RUNNING",
        "logs": jobs_db[job_id]["logs"],
        "message": "Running automated tests..."
    })
    
    await asyncio.sleep(3)
    jobs_db[job_id]["logs"].append("Test execution completed")
    
    # Simulate finding a bug
    bug_id = str(uuid.uuid4())
    bug = Bug(
        id=bug_id,
        job_id=job_id,
        summary="Login button not responsive on mobile",
        test_name="Mobile Login Test",
        severity="High",
        status="Open",
        steps="1. Open mobile browser\n2. Navigate to login page\n3. Tap login button",
        actual_result="Button does not respond to touch",
        expected_result="Button should respond and show loading state",
        created_at=datetime.now().isoformat()
    )
    
    bugs_db[bug_id] = bug
    jobs_db[job_id]["status"] = "FAILED"
    jobs_db[job_id]["logs"].append("Found 1 potential bug")
    
    await send_websocket_update(job_id, {
        "status": "FAILED",
        "logs": jobs_db[job_id]["logs"],
        "bugs": [bug.dict()],
        "message": "Tests completed - 1 bug found"
    })

@app.post("/run-tests", response_model=Job)
async def trigger_tests(background_tasks: BackgroundTasks, request: TestRunRequest, username: str = Depends(verify_token)):
    job_id = str(uuid.uuid4())
    
    job = Job(
        id=job_id,
        status="PENDING",
        logs=["Job created successfully"],
        created_at=datetime.now().isoformat()
    )
    
    jobs_db[job_id] = job.dict()
    
    # Add background task
    background_tasks.add_task(simulate_test_execution, job_id, request.test_url)
    
    return job

@app.get("/jobs/{job_id}", response_model=Job)
def get_job_status(job_id: str, username: str = Depends(verify_token)):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return Job(**jobs_db[job_id])

@app.get("/bugs", response_model=List[Bug])
def list_bugs(username: str = Depends(verify_token)):
    return [Bug(**bug) for bug in bugs_db.values()]

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI QA Agent Platform Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000)