from pydantic import BaseModel
from typing import Dict, Any

class AIMissionSubmissionRequest(BaseModel):
    mission: Dict[str, Any]
    code: str

class AIMissionSubmissionResponse(BaseModel):
    success: bool
    xp_gained: int
    tests_passed: int
    total_tests: int
    output: str
    message: str