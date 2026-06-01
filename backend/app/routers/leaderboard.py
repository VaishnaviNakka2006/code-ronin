from fastapi import APIRouter, Depends
from supabase import create_client
from dotenv import load_dotenv
from app.deps import get_current_user
from app.services.leaderboard_service import LeaderboardService
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter(
    prefix="/leaderboard",
    tags=["leaderboard"]
)

# =========================
# GLOBAL LEADERBOARD
# =========================
@router.get("/global")
async def global_leaderboard(limit: int = 10):

    res = (
        supabase
        .table("profiles")
        .select("username, xp, rank")
        .order("xp", desc=True)
        .limit(limit)
        .execute()
    )

    return res.data


# =========================
# FRIENDS LEADERBOARD
# =========================
@router.get("/friends")
async def friends_leaderboard(
    user = Depends(get_current_user)
):

    return LeaderboardService.get_friends_leaderboard(
        str(user.id)
    )