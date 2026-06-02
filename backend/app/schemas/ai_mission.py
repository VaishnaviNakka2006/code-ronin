from pydantic import BaseModel
from typing import List, Optional

class TestCase(BaseModel):
    input: str = ""
    expected_output: str

class AIMission(BaseModel):
    title: str
    description: str
    difficulty: str
    test_cases: List[TestCase]
    code_stub: Optional[str] = None