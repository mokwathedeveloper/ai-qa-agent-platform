import subprocess
import os
from typing import Dict, Any

def run_automation_tests() -> Dict[str, Any]:
    """
    Runs pytest on the automation_tests directory.
    Returns a dictionary with status and logs.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(base_dir, "automation_tests")
    artifact_dir = os.path.join(base_dir, "artifacts")
    
    # Ensure artifact dir exists
    os.makedirs(artifact_dir, exist_ok=True)
    
    cmd = [
        "pytest", 
        test_dir, 
        "-v",
        f"--output={artifact_dir}",
        "--screenshot=only-on-failure",
        "--video=retain-on-failure"
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    logs = result.stdout.splitlines()
    if result.stderr:
        logs.extend(result.stderr.splitlines())
        
    status = "COMPLETED" if result.returncode == 0 else "FAILED"
    
    return {
        "status": status,
        "logs": logs,
        "exit_code": result.returncode
    }
