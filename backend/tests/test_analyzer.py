from backend.agent.analyzer import analyze_test_run
from unittest.mock import patch, MagicMock

def test_analyze_no_failure():
    result = {"status": "COMPLETED"}
    bugs = analyze_test_run(result)
    assert bugs == []

@patch("backend.agent.analyzer.AIClient")
def test_analyze_failure(MockAIClient):
    mock_client = MockAIClient.return_value
    mock_client.analyze_failure.return_value = {"summary": "Bug 1", "severity": "High"}
    
    result = {
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
    
    bugs = analyze_test_run(result)
    assert len(bugs) == 1
    assert bugs[0]["summary"] == "Bug 1"
    mock_client.analyze_failure.assert_called_once()
