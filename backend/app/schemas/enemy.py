from pydantic import BaseModel


class EnemyPublicInfo(BaseModel):
    """Returned by GET /missions/{id}/enemy. No hidden test info."""
    name: str
    sprite_key: str
    max_hp: int
    current_hp: int
    hp_percent: float
    defeated: bool
    is_boss: bool


class DamageInfo(BaseModel):
    total: int
    newly_defeated_count: int
    critical: bool
    narrative: str


class EnemyStateInfo(BaseModel):
    name: str
    sprite_key: str
    max_hp: int
    hp_before: int
    hp_after: int
    hp_percent: float
    defeated: bool
    is_boss: bool