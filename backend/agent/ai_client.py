import json
from openai import OpenAI
from typing import Dict, Any
from backend.config import settings

class AIClient:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not set.")
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def analyze_failure(self, logs: list[str], test_name: str) -> Dict[str, Any]:
        if not self.client:
            return {
                "summary": "AI Analysis Unavailable (No API Key)",
                "environment": "Unknown",
                "preconditions": "Unknown",
                "steps": "Unknown",
                "actual_result": "Unknown",
                "expected_result": "Unknown",
                "severity": "Low"
            }

        logs_text = "\n".join(logs[-50:]) # Send last 50 lines
        
        prompt = f"""
        You are a Senior QA Automation Engineer. Analyze the following Playwright test failure logs and generate a professional bug report in uTest standard format.
        
        Test Name: {test_name}
        Logs:
        {logs_text}
        
        Return the response strictly in JSON format with the following keys:
        - summary
        - environment
        - preconditions
        - steps
        - actual_result
        - expected_result
        - severity (Critical, High, Medium, Low)
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful QA assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"AI Analysis failed: {e}")
            return {
                "summary": "AI Analysis Failed",
                "environment": "Unknown",
                "preconditions": "Unknown",
                "steps": "Unknown",
                "actual_result": f"Error: {str(e)}",
                "expected_result": "Unknown",
                "severity": "Medium"
            }