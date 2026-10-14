from pydantic import BaseModel
from typing import Optional, List

from app.schemas.enemy import DamageInfo, EnemyStateInfo


class SubmissionRequest(BaseModel):
    code: str
    mission_id: int


class TestResultDetail(BaseModel):
    test_id: int
    passed: bool
    expected: str
    actual: str
    description: Optional[str]


class SubmissionResponse(BaseModel):
    # ---- existing fields, unchanged ----
    success: bool
    score: float
    xp_gained: int
    tests_passed: int
    total_tests: int
    output: str
    completed: bool
    message: str

    # ---- Phase 1 additions (optional, backward compatible) ----
    damage: Optional[DamageInfo] = None
    enemy_state: Optional[EnemyStateInfo] = None