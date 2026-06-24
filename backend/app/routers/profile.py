from fastapi import APIRouter, HTTPException
from app.db import supabase

router = APIRouter(
    prefix="",
    tags=["profile"]
)

@router.get("/profile/{user_id}")
async def get_profile(user_id: str):

    res = (
        supabase.table("profiles")
        .select("id, username, xp, rank, streak_days")
        .eq("username", user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(404, "User not found")

    return res.data[0]