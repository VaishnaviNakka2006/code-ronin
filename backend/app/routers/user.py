from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_current_user
from supabase import create_client
from dotenv import load_dotenv
from pydantic import BaseModel
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter(prefix="/user", tags=["user"])

class UpdateXP(BaseModel):
    xp_gain: int
    mission_id: int

@router.post("/xp")
async def add_xp(data: UpdateXP, user=Depends(get_current_user)):
    user_id = user.id

    profile = supabase.table("profiles").select("xp").eq("id", user_id).execute()

    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    new_xp = profile.data[0]["xp"] + data.xp_gain

    rank = "Scavenger"

    if new_xp >= 100:
        rank = "Hacker"
    elif new_xp >= 30:
        rank = "Runner"

    supabase.table("profiles").update({
        "xp": new_xp,
        "rank": rank
    }).eq("id", user_id).execute()

    supabase.table("user_progress").insert({
        "user_id": user_id,
        "mission_id": data.mission_id
    }).execute()

    return {
        "xp": new_xp,
        "rank": rank
    }

@router.get("/streak")
async def get_streak(user=Depends(get_current_user)):
    profile = supabase.table("profiles").select(
        "streak_days"
    ).eq("id", user.id).execute()

    return {
        "streak": profile.data[0]["streak_days"]
    }

@router.post("/check-streak")
async def check_streak(user=Depends(get_current_user)):
    from datetime import date, timedelta

    profile = (
        supabase
        .table("profiles")
        .select("last_active, streak_days")
        .eq("id", user.id)
        .execute()
    )

    if not profile.data:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    last_active = profile.data[0]["last_active"]
    streak = profile.data[0]["streak_days"]

    today = date.today()

    # Convert DB string to date
    last_date = date.fromisoformat(last_active)

    if last_date == today - timedelta(days=1):
        streak += 1

    elif last_date < today - timedelta(days=1):
        streak = 1

    # already checked today -> keep same streak

    supabase.table("profiles").update({
        "streak_days": streak,
        "last_active": today.isoformat()
    }).eq("id", user.id).execute()

    return {
        "streak": streak
    }