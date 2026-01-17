import time
from typing import Dict, Any
from backend.logger import logger

class SubmissionClient:
    """
    A mock client to simulate submitting bug reports to an external API like uTest or Test IO.
    """
    def submit_bug(self, bug_details: Dict[str, Any], provider: str) -> bool:
        """
        Simulates submitting a bug report.
        In a real implementation, this would make an HTTP request to the provider's API.
        """
        logger.info(f"Preparing to submit bug to {provider}...")
        logger.info(f"Payload: {bug_details}")
        
        # Simulate network latency
        time.sleep(2) 
        
        # In a real scenario, you would check the response from the API.
        # Here, we'll just assume it's always successful.
        is_successful = True
        
        if is_successful:
            logger.info(f"Successfully submitted bug '{bug_details.get('summary')}' to {provider}.")
        else:
            logger.error(f"Failed to submit bug '{bug_details.get('summary')}' to {provider}.")
            
        return is_successful

submission_client = SubmissionClient()
