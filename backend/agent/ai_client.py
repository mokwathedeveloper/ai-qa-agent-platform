import json
from openai import OpenAI
from typing import Dict, Any
from backend.config import settings
from backend.logger import logger

class AIClient:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set. AI analysis will be unavailable.")
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def analyze_failure(self, logs: list[str], test_name: str, context: Dict[str, str]) -> Dict[str, Any]:
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
        
        # Extract context
        overview = context.get("overview", "N/A")
        instructions = context.get("instructions", "N/A")

        prompt = f"""
        You are a Senior QA Automation Engineer. Analyze the following Playwright test failure logs and generate a professional bug report in uTest standard format.
        
        **TEST CYCLE CONTEXT:**
        Overview: {overview}
        Instructions: {instructions}
        
        **TEST EXECUTION DATA:**
        Test Name: {test_name}
        Logs:
        {logs_text}
        
        **INSTRUCTIONS:**
        1. Analyze the logs to identify the failure.
        2. Cross-reference with the Cycle Overview and Instructions to determine if this is out of scope (if applicable) or a valid bug.
        3. Return the response strictly in JSON format with the following keys:
        - summary (Clear and concise title)
        - environment (Browser/OS details inferred from logs)
        - preconditions (What must be done before steps)
        - steps (Numbered list of reproduction steps)
        - actual_result (What actually happened)
        - expected_result (What should have happened based on standard behavior or instructions)
        - severity (Critical, High, Medium, Low)
        """
        
        try:
            logger.info(f"Sending request to OpenAI for test: {test_name}")
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
            logger.error(f"AI Analysis failed for test {test_name}: {e}", exc_info=True)
            return {
                "summary": "AI Analysis Failed",
                "environment": "Unknown",
                "preconditions": "Unknown",
                "steps": "Unknown",
                "actual_result": f"Error: {str(e)}",
                "expected_result": "Unknown",
                "severity": "Medium"
            }
