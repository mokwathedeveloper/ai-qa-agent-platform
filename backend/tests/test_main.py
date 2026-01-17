from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("backend.main.run_automation_tests")
def test_run_tests_trigger(mock_runner):
    # Mock runner to avoid actual execution
    mock_runner.return_value = {"status": "COMPLETED", "logs": ["log1"], "exit_code": 0}
    
    response = client.post("/run-tests")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"
    
    # Check status
    job_id = data["job_id"]
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    # We verify the job was created
    assert response.json()["job_id"] == job_id