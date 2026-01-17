"""
Test Analyzer Module
Analyzes test failures and generates bug reports using AI
"""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import Bug
import openai
import os

logger = logging.getLogger(__name__)

class TestAnalyzer:
    def __init__(self):
        self.openai_client = None
        self.setup_openai()
    
    def setup_openai(self):
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                openai.api_key = api_key
                self.openai_client = openai
            else:
                logger.warning("OpenAI API key not found. Bug analysis will be limited.")
        except Exception as e:
            logger.error(f"Failed to setup OpenAI: {e}")
    
    def generate_bug_report(self, failure: Dict[str, Any], context: Dict[str, str], provider: str) -> Dict[str, Any]:
        """Generate a detailed bug report from test failure"""
        
        # Basic bug report structure
        bug_report = {
            "summary": f"Test Failure: {failure.get('test', 'Unknown Test')}",
            "test_name": failure.get('test', 'Unknown Test'),
            "severity": self.determine_severity(failure),
            "status": "Open",
            "steps": self.generate_steps(failure, context),
            "actual_result": failure.get('error', 'Test failed'),
            "expected_result": self.generate_expected_result(failure),
            "environment": {
                "browser": "Chrome",
                "os": "Linux",
                "viewport": "1280x720"
            }
        }
        
        # Enhance with AI if available
        if self.openai_client:
            try:
                enhanced_report = self.enhance_with_ai(bug_report, context, provider)
                if enhanced_report:
                    bug_report.update(enhanced_report)
            except Exception as e:
                logger.error(f"Failed to enhance bug report with AI: {e}")
        
        return bug_report
    
    def determine_severity(self, failure: Dict[str, Any]) -> str:
        """Determine bug severity based on failure type"""
        test_name = failure.get('test', '').lower()
        error = failure.get('error', '').lower()
        
        # Critical issues
        if any(keyword in test_name for keyword in ['load', 'crash', 'security']):
            return "Critical"
        
        if any(keyword in error for keyword in ['timeout', 'connection', 'network']):
            return "High"
        
        # High priority issues
        if any(keyword in test_name for keyword in ['login', 'payment', 'checkout']):
            return "High"
        
        # Medium priority by default
        return "Medium"
    
    def generate_steps(self, failure: Dict[str, Any], context: Dict[str, str]) -> str:
        """Generate reproduction steps"""
        test_name = failure.get('test', '')
        
        base_steps = [
            "1. Open web browser",
            "2. Navigate to the test URL",
        ]
        
        if 'load' in test_name.lower():
            base_steps.extend([
                "3. Wait for page to load completely",
                "4. Observe the loading behavior"
            ])
        elif 'title' in test_name.lower():
            base_steps.extend([
                "3. Check the page title in browser tab",
                "4. Verify title content"
            ])
        elif 'elements' in test_name.lower():
            base_steps.extend([
                "3. Inspect page elements",
                "4. Look for missing or broken elements"
            ])
        elif 'interactive' in test_name.lower():
            base_steps.extend([
                "3. Try to interact with buttons, links, and form elements",
                "4. Check if elements respond to user input"
            ])
        elif 'console' in test_name.lower():
            base_steps.extend([
                "3. Open browser developer tools (F12)",
                "4. Check the Console tab for errors"
            ])
        else:
            base_steps.extend([
                "3. Perform the test action",
                "4. Observe the result"
            ])
        
        return "\n".join(base_steps)
    
    def generate_expected_result(self, failure: Dict[str, Any]) -> str:
        """Generate expected result description"""
        test_name = failure.get('test', '').lower()
        
        if 'load' in test_name:
            return "Page should load successfully without errors and display content within reasonable time"
        elif 'title' in test_name:
            return "Page should have a meaningful, non-empty title that describes the page content"
        elif 'elements' in test_name:
            return "Page should contain basic HTML structure with proper elements"
        elif 'interactive' in test_name:
            return "Page should have interactive elements (buttons, links, forms) that users can interact with"
        elif 'console' in test_name:
            return "Page should load without JavaScript console errors"
        else:
            return "Test should pass without errors"
    
    def enhance_with_ai(self, bug_report: Dict[str, Any], context: Dict[str, str], provider: str) -> Dict[str, Any]:
        """Enhance bug report using AI analysis"""
        try:
            prompt = self.build_ai_prompt(bug_report, context, provider)
            
            response = self.openai_client.ChatCompletion.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are a QA expert who writes detailed bug reports."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            ai_content = response.choices[0].message.content.strip()
            
            # Parse AI response and enhance bug report
            enhanced = self.parse_ai_response(ai_content)
            return enhanced
            
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            return {}
    
    def build_ai_prompt(self, bug_report: Dict[str, Any], context: Dict[str, str], provider: str) -> str:
        """Build prompt for AI enhancement"""
        return f"""
Please enhance this bug report for {provider} platform:

Test Failure: {bug_report['test_name']}
Error: {bug_report['actual_result']}
Severity: {bug_report['severity']}

Context:
- Overview: {context.get('overview', 'N/A')}
- Instructions: {context.get('instructions', 'N/A')}

Please provide:
1. An improved summary (max 100 chars)
2. More detailed steps to reproduce
3. Better description of expected vs actual results
4. Any additional insights about the issue

Format your response as JSON with keys: summary, steps, actual_result, expected_result, insights
"""
    
    def parse_ai_response(self, ai_content: str) -> Dict[str, Any]:
        """Parse AI response and extract enhancements"""
        try:
            # Try to parse as JSON first
            if ai_content.strip().startswith('{'):
                return json.loads(ai_content)
            
            # If not JSON, extract key information
            enhanced = {}
            lines = ai_content.split('\n')
            
            for line in lines:
                if line.startswith('Summary:'):
                    enhanced['summary'] = line.replace('Summary:', '').strip()
                elif line.startswith('Steps:'):
                    enhanced['steps'] = line.replace('Steps:', '').strip()
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {}

def analyze_test_run(job_id: str, test_results: Dict[str, Any], context: Dict[str, str], provider: str, db: Session) -> List[Dict[str, Any]]:
    """
    Analyze test run results and generate bug reports
    """
    analyzer = TestAnalyzer()
    bugs = []
    
    try:
        failures = test_results.get('failures', [])
        
        for failure in failures:
            # Generate bug report
            bug_data = analyzer.generate_bug_report(failure, context, provider)
            
            # Create bug record in database
            bug = Bug(
                job_id=job_id,
                summary=bug_data['summary'],
                test_name=bug_data['test_name'],
                severity=bug_data['severity'],
                status=bug_data['status'],
                steps=bug_data['steps'],
                actual_result=bug_data['actual_result'],
                expected_result=bug_data['expected_result'],
                environment=json.dumps(bug_data.get('environment', {}))
            )
            
            db.add(bug)
            bugs.append(bug_data)
        
        db.commit()
        logger.info(f"Generated {len(bugs)} bug reports for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error analyzing test run: {e}")
        db.rollback()
    
    return bugs