from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_current_user
from app.services.proficiency_service import ProficiencyService
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

    from datetime import date

    today = date.today()

    supabase.table("profiles").update({
        "xp": new_xp,
        "rank": rank,
        "last_active": today.isoformat()
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


from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.main import supabase
from datetime import date

router = APIRouter(prefix="/user", tags=["user"])


# existing routes here...

@router.get("/streak")
async def get_streak():
    pass


# PASTE NEW CODE BELOW THIS

from datetime import date, timedelta
from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.main import supabase
from app.services.achievement_service import AchievementService

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/check-streak")
async def check_streak(user=Depends(get_current_user)):

    user_id = user.id

    print("USER ID:", user_id)

    profile = (
        supabase
        .table("profiles")
        .select("*")
        .eq("id", user_id)
        .execute()
    )

    print("PROFILE:", profile.data)

    if not profile.data:
        return {"error": "Profile not found"}

    profile_data = profile.data[0]

    current_streak = profile_data.get("streak_days", 0)

    last_active = profile_data.get("last_active")

    today = date.today()

    # FIRST TIME
    if not last_active:

        new_streak = 1

    else:

        last_active_date = date.fromisoformat(last_active)

        # SAME DAY → DO NOT INCREASE
        if last_active_date == today:

            return {
                "success": True,
                "message": "Already checked today",
                "current_streak": current_streak
            }

        # NEXT DAY → INCREASE
        elif last_active_date == today - timedelta(days=1):

            new_streak = current_streak + 1

        # MISSED DAYS → RESET
        else:

            new_streak = 1

    # UPDATE DATABASE
    supabase.table("profiles").update({
        "streak_days": new_streak,
        "last_active": str(today)
    }).eq("id", user_id).execute()

    # CHECK STREAK ACHIEVEMENTS
    unlocked = AchievementService.evaluate_and_unlock(
        user.id,
        "daily_streak",
        {}
    )

    return {
        "success": True,
        "new_streak": new_streak,
        "new_achievements": unlocked
    }

@router.get("/proficiency")
async def get_proficiency(
    user=Depends(get_current_user)
):
    prof = await ProficiencyService.get_user_proficiency(
        user.id
    )
    return prof
