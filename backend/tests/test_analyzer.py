from backend.agent.analyzer import analyze_test_run
from unittest.mock import patch, MagicMock

def test_analyze_no_failure():
    result = {"status": "COMPLETED"}
    bugs = analyze_test_run("job-123", result, {}, "uTest", MagicMock())
    assert bugs == []

@patch("backend.agent.analyzer.submission_client")
@patch("backend.agent.analyzer.AIClient")
def test_analyze_failure(MockAIClient, mock_submission_client):
    # Mock AI and Submission
    mock_ai = MockAIClient.return_value
    mock_ai.analyze_failure.return_value = {"summary": "Bug 1", "severity": "High"}
    mock_submission_client.submit_bug.return_value = True
    
    # Mock DB session
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    run_result = {
        "status": "FAILED",
        "report_data": {
            "tests": [
                {
                    "outcome": "failed",
                    "nodeid": "test_1",
                    "call": {"crash": {"message": "Error"}, "longrepr": "Traceback"}
                }
            ]
        }
    }
    
    context = {"overview": "Test Context", "instructions": "Do this"}
    job_id = "job-123"
    provider = "uTest"
    
    bugs = analyze_test_run(job_id, run_result, context, provider, mock_db)
    
    assert len(bugs) == 1
    assert bugs[0]["summary"] == "Bug 1"
    assert bugs[0]["status"] == "SUBMITTED" 
    
    mock_ai.analyze_failure.assert_called_once()
    mock_submission_client.submit_bug.assert_called_once()
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()

@patch("backend.agent.analyzer.AIClient")
def test_analyze_duplicate_failure(MockAIClient):
    mock_ai = MockAIClient.return_value
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
    
    run_result = {
        "status": "FAILED",
        "report_data": {
            "tests": [
                {
                    "outcome": "failed",
                    "nodeid": "test_1",
                    "call": {"crash": {"message": "Error"}, "longrepr": "Traceback"}
                }
            ]
        }
    }
    
    context = {"overview": "Test Context", "instructions": "Do this"}
    job_id = "job-123"
    provider = "uTest"
    
    bugs = analyze_test_run(job_id, run_result, context, provider, mock_db)
    
    assert len(bugs) == 1
    assert bugs[0]["status"] == "DUPLICATE"
    
    mock_ai.analyze_failure.assert_not_called()
    mock_db.add.assert_not_called()

