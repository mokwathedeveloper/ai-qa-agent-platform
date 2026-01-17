from backend.agent.analyzer import analyze_test_run
from unittest.mock import patch, MagicMock

def test_analyze_no_failure():
    result = {"status": "COMPLETED"}
    bugs = analyze_test_run(result)
    assert bugs == []

@patch("backend.agent.analyzer.SessionLocal")
@patch("backend.agent.analyzer.AIClient")
def test_analyze_failure(MockAIClient, MockSessionLocal):
    # Mock AI
    mock_ai = MockAIClient.return_value
    mock_ai.analyze_failure.return_value = {"summary": "Bug 1", "severity": "High"}
    
    # Mock DB
    mock_db = MockSessionLocal.return_value
    # Mock is_duplicate -> False
    # db.query(Bug).filter(...).first() -> None
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
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
    assert bugs[0]["status"] == "NEW" # Verify it defaults to NEW
    
    # Verify DB add was called
    mock_db.add.assert_called()
    mock_db.commit.assert_called()