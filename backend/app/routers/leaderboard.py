from fastapi import APIRouter
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get("/")
async def get_leaderboard(limit: int = 10):
    res = (
        supabase
        .table("profiles")
        .select("username, xp, rank")
        .order("xp", desc=True)
        .limit(limit)
        .execute()
    )

    return res.data