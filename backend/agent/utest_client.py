import os
import requests
from typing import Dict, Any

class UTestClient:
    def __init__(self):
        self.api_key = os.getenv("UTEST_API_KEY")
        # Placeholder URL - would be replaced by actual endpoint
        self.base_url = "https://platform.utest.com/api/v1" 
        
    def submit_bug(self, bug_report: Dict[str, Any]) -> str:
        """
        Submits the bug report to uTest API.
        Returns the external bug ID or status.
        """
        if not self.api_key:
            print("Warning: UTEST_API_KEY not set. Skipping submission.")
            return "SKIPPED_NO_KEY"
            
        payload = {
            "title": bug_report.get("summary"),
            "steps": bug_report.get("steps"),
            "actualResult": bug_report.get("actual_result"),
            "expectedResult": bug_report.get("expected_result"),
            "severity": bug_report.get("severity"),
            "environment": bug_report.get("environment")
        }
        
        try:
            # In a real scenario, we would make the request:
            # response = requests.post(
            #     f"{self.base_url}/bugs", 
            #     json=payload, 
            #     headers={"Authorization": f"Bearer {self.api_key}"}
            # )
            # response.raise_for_status()
            # return response.json().get("id")
            
            print(f"Simulating submission to uTest: {payload['title']}")
            return "UTEST-SIMULATED-ID"
            
        except Exception as e:
            print(f"Failed to submit to uTest: {e}")
            return "SUBMISSION_FAILED"
