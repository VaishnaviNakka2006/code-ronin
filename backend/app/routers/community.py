from fastapi import APIRouter
from app.db import supabase

router = APIRouter(
    prefix="/community",
    tags=["community"]
)

MILESTONES = [
    100000,
    500000,
    1000000
]


@router.get("/goal")
async def get_community_goal():

    res = (
        supabase.table("profiles")
        .select("xp")
        .execute()
    )

    total_xp = sum(
        user.get("xp", 0)
        for user in res.data
    )

    next_target = MILESTONES[-1]

    for milestone in MILESTONES:
        if total_xp < milestone:
            next_target = milestone
            break

    progress_percentage = round(
        (total_xp / next_target) * 100,
        2
    )

    return {
        "current_total": total_xp,
        "next_target": next_target,
        "progress_percentage": progress_percentage,
        "reward": "🔥 Double XP Weekend"
    }