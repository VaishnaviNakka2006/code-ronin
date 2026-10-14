"""
Enemy layer for Code Ronin Phase 1.

Pure logic — no DB access.
- HP is derived from defeated_test_ids (single source of truth).
- Damage is computed from actual test weights.
- Cumulative rounding ensures Σ(per_test_damage) == max_hp exactly.
"""

from typing import Any

ENEMY_BATTLE_ENABLED = True

# Known enemy definitions by mission_id.
KNOWN_ENEMIES: dict[int, dict[str, Any]] = {
    1: {"name": "FIREWALL SENTINEL", "sprite_key": "sentinel", "max_hp": 1000, "is_boss": False},
    2: {"name": "LOOP WRAITH",       "sprite_key": "wraith",   "max_hp": 1200, "is_boss": False},
    3: {"name": "CORRUPTED CORE",    "sprite_key": "core",     "max_hp": 1500, "is_boss": True},
}

FALLBACK_HP_BY_DIFFICULTY = {
    "easy": 800,
    "medium": 1000,
    "hard": 1200,
    "boss": 1500,
}
FALLBACK_HP_DEFAULT = 1000
FALLBACK_SPRITE = "guardian"


def get_enemy_def(mission_id: int, difficulty: str | None = None) -> dict[str, Any]:
    """Deterministic enemy definition for any mission ID."""
    if mission_id in KNOWN_ENEMIES:
        return dict(KNOWN_ENEMIES[mission_id])

    hp = FALLBACK_HP_BY_DIFFICULTY.get((difficulty or "easy").lower(), FALLBACK_HP_DEFAULT)
    return {
        "name": f"GUARDIAN-{mission_id:03d}",
        "sprite_key": FALLBACK_SPRITE,
        "max_hp": hp,
        "is_boss": (difficulty or "").lower() == "boss",
    }


def compute_per_test_damage(
    test_cases: list[dict],
    max_hp: int,
) -> dict[int, int]:
    """
    Returns {test_id: damage} such that sum of ALL damages equals max_hp exactly.
    Uses cumulative rounding to eliminate drift (e.g. 3 tests / 1000 HP → 333, 333, 334).
    """
    if not test_cases or max_hp <= 0:
        return {}

    test_ids = [int(tc["id"]) for tc in test_cases]
    weights = [float(tc.get("weight", 1.0) or 1.0) for tc in test_cases]
    total_weight = sum(weights)

    if total_weight <= 0:
        result = {tid: 0 for tid in test_ids}
        result[test_ids[-1]] = max_hp
        return result

    result: dict[int, int] = {}
    cum_weight = 0.0
    cum_damage_prev = 0
    last_index = len(test_ids) - 1

    for i, (tid, w) in enumerate(zip(test_ids, weights)):
        cum_weight += w
        if i == last_index:
            cum_damage = max_hp  # last test absorbs rounding residue
        else:
            cum_damage = int(round((cum_weight / total_weight) * max_hp))
        result[tid] = cum_damage - cum_damage_prev
        cum_damage_prev = cum_damage

    return result


def compute_enemy_state(
    enemy_def: dict[str, Any],
    test_cases: list[dict],
    defeated_test_ids: list[int],
) -> dict[str, Any]:
    """Derive current HP from defeated_test_ids."""
    per_test = compute_per_test_damage(test_cases, enemy_def["max_hp"])
    valid_ids = {int(tc["id"]) for tc in test_cases}

    damage_taken = 0
    for tid in defeated_test_ids:
        try:
            tid_int = int(tid)
        except (TypeError, ValueError):
            continue
        if tid_int in valid_ids:
            damage_taken += per_test.get(tid_int, 0)

    damage_taken = min(damage_taken, enemy_def["max_hp"])
    current_hp = max(0, enemy_def["max_hp"] - damage_taken)
    hp_percent = (
        (current_hp / enemy_def["max_hp"] * 100.0) if enemy_def["max_hp"] > 0 else 0.0
    )

    return {
        "name": enemy_def["name"],
        "sprite_key": enemy_def["sprite_key"],
        "max_hp": enemy_def["max_hp"],
        "current_hp": current_hp,
        "hp_percent": round(hp_percent, 2),
        "defeated": current_hp == 0,
        "is_boss": enemy_def["is_boss"],
    }


def _narrative(newly_defeated_count: int, hp_after: int, total_damage: int, max_hp: int) -> str:
    if hp_after == 0 and newly_defeated_count > 0:
        return "CRITICAL HIT — All defenses breached!"
    if newly_defeated_count == 0:
        return "DEFENSES ALREADY BREACHED — Improve your code to break through the remaining defenses."
    ratio = (total_damage / max_hp) if max_hp > 0 else 0.0
    if ratio < 0.25:
        return "GLANCING BLOW — Barely scratched the target."
    if ratio < 0.6:
        return "SOLID HIT — The enemy staggers."
    return "HEAVY DAMAGE — The enemy reels!"


def compute_damage_and_new_defeats(
    enemy_def: dict[str, Any],
    test_cases: list[dict],
    details: list[dict],
    already_defeated_ids: list[int],
    hp_before: int,
) -> tuple[dict[str, Any], set[int]]:
    """
    Returns (damage_dict, newly_defeated_test_id_set).
    Only newly defeated tests contribute damage.
    Damage is clamped to hp_before. Never negative, never overkill.
    """
    per_test = compute_per_test_damage(test_cases, enemy_def["max_hp"])

    already: set[int] = set()
    for x in already_defeated_ids:
        try:
            already.add(int(x))
        except (TypeError, ValueError):
            continue

    newly_defeated: set[int] = set()
    for d in details:
        try:
            tid = int(d.get("test_id"))
        except (TypeError, ValueError):
            continue
        if d.get("passed") and tid not in already:
            newly_defeated.add(tid)

    raw_damage = sum(per_test.get(tid, 0) for tid in newly_defeated)
    total_damage = max(0, min(raw_damage, hp_before))
    hp_after = max(0, hp_before - total_damage)
    critical = (hp_before > 0 and hp_after == 0 and len(newly_defeated) > 0)

    damage = {
        "total": total_damage,
        "newly_defeated_count": len(newly_defeated),
        "critical": critical,
        "narrative": _narrative(len(newly_defeated), hp_after, total_damage, enemy_def["max_hp"]),
    }
    return damage, newly_defeated


def is_enabled() -> bool:
    return ENEMY_BATTLE_ENABLED