"""
DB access for enemy_progress. Server-side source of truth.

CONCURRENCY NOTE (Phase 1 limitation):
persist_defeated_test_ids is a read-modify-write. Two truly-parallel submissions
from the same user on the same mission could race. We mitigate by re-reading
after the write, so the returned state always reflects the database. Full
atomicity (Postgres RPC with SELECT ... FOR UPDATE) is deferred to Phase 2.
"""

import logging
from datetime import datetime, timezone

from app.db import supabase

logger = logging.getLogger(__name__)


def get_defeated_test_ids(user_id: str, mission_id: int) -> list[int]:
    """Returns persisted defeated test IDs, or [] if no row / any error."""
    try:
        res = (
            supabase.table("enemy_progress")
            .select("defeated_test_ids")
            .eq("user_id", str(user_id))
            .eq("mission_id", mission_id)
            .execute()
        )
        if not res.data:
            return []
        raw = res.data[0].get("defeated_test_ids") or []
        out: list[int] = []
        for x in raw:
            try:
                out.append(int(x))
            except (TypeError, ValueError):
                continue
        return out
    except Exception as e:
        logger.warning(f"enemy_progress read failed: {e}")
        return []


def persist_defeated_test_ids(
    user_id: str,
    mission_id: int,
    new_defeated: set[int],
) -> list[int]:
    """
    Merge new defeats into existing set and upsert.
    Returns the canonical set as read back from the database.
    """
    existing = set(get_defeated_test_ids(user_id, mission_id))
    merged_list = sorted(existing | {int(x) for x in new_defeated})

    now = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("enemy_progress").upsert(
            {
                "user_id": str(user_id),
                "mission_id": mission_id,
                "defeated_test_ids": merged_list,
                "updated_at": now,
            },
            on_conflict="user_id,mission_id",
        ).execute()
    except Exception as e:
        logger.error(f"enemy_progress upsert failed: {e}")

    return get_defeated_test_ids(user_id, mission_id)