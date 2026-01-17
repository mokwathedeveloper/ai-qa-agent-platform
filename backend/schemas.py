from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Any
import re

class BugSchema(BaseModel):
    id: str
    job_id: str
    test_name: str
    summary: str
    steps: str
    actual_result: str
    expected_result: str
    severity: str
    status: str
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    environment: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class JobSchema(BaseModel):
    id: str
    status: str
    logs: List[Any]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TestRunRequest(BaseModel):
    test_url: str
    cycle_overview: Optional[str] = ""
    testing_instructions: Optional[str] = ""
    provider: Optional[str] = "uTest"
    
    @field_validator('test_url')
    @classmethod
    def validate_url(cls, v):
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v
