import subprocess
import os
import json
from typing import Dict, Any
from backend.config import settings

def run_automation_tests() -> Dict[str, Any]:
    """
    Runs pytest on the automation_tests directory.
    Returns a dictionary with status and logs.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(base_dir, "automation_tests")
    artifact_dir = os.path.join(base_dir, "artifacts")
    report_file = os.path.join(artifact_dir, "report.json")
    
    # Ensure artifact dir exists
    os.makedirs(artifact_dir, exist_ok=True)
    
    cmd = [
        "pytest", 
        test_dir, 
        "-v",
        f"--output={artifact_dir}",
        "--screenshot=only-on-failure",
        "--video=retain-on-failure",
        "--json-report",
        f"--json-report-file={report_file}"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.TEST_TIMEOUT_SECONDS # Prevents infinite hangs
        )
        
        logs = result.stdout.splitlines()
        if result.stderr:
            logs.extend(result.stderr.splitlines())
            
        status = "COMPLETED" if result.returncode == 0 else "FAILED"
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        logs = ["Tests timed out after {} seconds.".format(settings.TEST_TIMEOUT_SECONDS)]
        status = "FAILED"
        exit_code = -1
    except Exception as e:
        logs = [f"Execution failed: {e}"]
        status = "ERROR"
        exit_code = -1
    
    # Read the JSON report if available
    report_data = {}
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r') as f:
                report_data = json.load(f)
        except Exception:
            pass

    return {
        "status": status,
        "logs": logs,
        "exit_code": exit_code,
        "report_file": report_file,
        "report_data": report_data
    }
