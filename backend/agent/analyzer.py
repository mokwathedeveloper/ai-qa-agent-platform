from backend.agent.ai_client import AIClient
from typing import Dict, Any, List

def analyze_test_run(run_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyzes the test run result. If failed, uses AI to generate bug reports.
    Returns a list of bug reports.
    """
    bugs = []
    
    if run_result["status"] != "FAILED":
        return bugs
        
    report_data = run_result.get("report_data", {})
    tests = report_data.get("tests", [])
    
    client = AIClient()
    
    for test in tests:
        if test.get("outcome") == "failed":
            test_name = test.get("nodeid", "Unknown Test")
            # Extract logs/error from the report or use global logs
            # report.json contains "call": {"longrepr": ...} which has the traceback
            call_info = test.get("call", {})
            crash_info = call_info.get("crash", {})
            traceback = call_info.get("longrepr", "")
            
            # Combine relevant info for AI
            failure_context = [
                f"Test: {test_name}",
                f"Error: {crash_info.get('message', 'Unknown Error')}",
                "Traceback:",
                str(traceback)
            ]
            
            # Also attach stdout/stderr from the test capture if available
            if "stdout" in test:
                failure_context.append(f"Stdout: {test['stdout']}")
            if "stderr" in test:
                failure_context.append(f"Stderr: {test['stderr']}")
                
            bug_report = client.analyze_failure(failure_context, test_name)
            bugs.append(bug_report)
            
    return bugs
