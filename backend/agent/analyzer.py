from backend.agent.ai_client import AIClient
from backend.agent.utest_client import UTestClient
from backend.agent.deduplicator import get_error_signature, is_duplicate
from backend.database.core import SessionLocal
from backend.database.models import Bug
from typing import Dict, Any, List

def analyze_test_run(run_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyzes the test run result. If failed, uses AI to generate bug reports.
    Checks for duplicates in DB.
    Submits to uTest API.
    Returns a list of bug reports.
    """
    bugs_found = []
    
    if run_result["status"] != "FAILED":
        return bugs_found
        
    report_data = run_result.get("report_data", {})
    tests = report_data.get("tests", [])
    
    client = AIClient()
    utest = UTestClient()
    db = SessionLocal()
    
    try:
        for test in tests:
            if test.get("outcome") == "failed":
                test_name = test.get("nodeid", "Unknown Test")
                call_info = test.get("call", {})
                crash_info = call_info.get("crash", {})
                traceback = call_info.get("longrepr", "")
                error_message = crash_info.get("message", "Unknown Error")
                
                # Check for duplicates
                signature = get_error_signature(test_name, error_message, str(traceback))
                if is_duplicate(db, signature):
                    bugs_found.append({
                        "summary": f"Duplicate: {test_name} - {error_message[:30]}...",
                        "environment": "Existing",
                        "steps": "Duplicate failure detected.",
                        "actual_result": "Duplicate",
                        "expected_result": "Duplicate",
                        "severity": "Low",
                        "status": "DUPLICATE"
                    })
                    continue
                
                # Combine relevant info for AI
                failure_context = [
                    f"Test: {test_name}",
                    f"Error: {error_message}",
                    "Traceback:",
                    str(traceback)
                ]
                
                if "stdout" in test:
                    failure_context.append(f"Stdout: {test['stdout']}")
                if "stderr" in test:
                    failure_context.append(f"Stderr: {test['stderr']}")
                    
                bug_report = client.analyze_failure(failure_context, test_name)
                
                # Submit to uTest
                external_id = utest.submit_bug(bug_report)
                submission_status = "SUBMITTED" if external_id and "ID" in external_id else "NEW"
                
                # Save to DB
                new_bug = Bug(
                    test_name=test_name,
                    summary=bug_report.get("summary", "No Summary"),
                    steps=str(bug_report.get("steps", "")),
                    actual_result=str(bug_report.get("actual_result", "")),
                    expected_result=str(bug_report.get("expected_result", "")),
                    error_signature=signature,
                    severity=bug_report.get("severity", "Medium"),
                    status=submission_status
                )
                db.add(new_bug)
                db.commit()
                db.refresh(new_bug)
                
                bug_report["id"] = new_bug.id
                bug_report["status"] = submission_status
                bugs_found.append(bug_report)
    except Exception as e:
        print(f"Error in analyzer: {e}")
    finally:
        db.close()
            
    return bugs_found
