#!/usr/bin/env python3
"""
Simple Backend Test Server
Tests basic FastAPI functionality without complex imports
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
import json

app = FastAPI(title="Test API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TestUser(BaseModel):
    username: str
    password: str

class TestResponse(BaseModel):
    message: str
    status: str

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/test-auth")
def test_auth(user: TestUser):
    if user.username and user.password:
        return TestResponse(message="Authentication successful", status="success")
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")

@app.get("/test-data")
def test_data():
    return {
        "data": ["item1", "item2", "item3"],
        "timestamp": "2024-01-01T00:00:00Z",
        "status": "success"
    }

if __name__ == "__main__":
    print("🚀 Starting test backend server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)