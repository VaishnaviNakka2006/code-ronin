from pydantic import BaseModel
from typing import Optional


class Mission(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    difficulty: str
    xp_base: int
    is_boss: bool = False
    language: str = "python"


class TestCase(BaseModel):
    input: str
    expected_output: str
    is_hidden: bool = False