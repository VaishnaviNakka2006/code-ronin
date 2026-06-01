from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.main import supabase

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"]
)

@router.get("/")
async def get_notifications(
    user=Depends(get_current_user),
    limit: int = 20
):
    res = (
        supabase.table("notifications")
        .select("*")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return res.data


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    user=Depends(get_current_user)
):
    (
        supabase.table("notifications")
        .update({"is_read": True})
        .eq("id", notification_id)
        .eq("user_id", user.id)
        .execute()
    )

    return {"status": "ok"}


@router.get("/unread-count")
async def unread_count(
    user=Depends(get_current_user)
):
    res = (
        supabase.table("notifications")
        .select("*", count="exact")
        .eq("user_id", user.id)
        .eq("is_read", False)
        .execute()
    )

    return {
        "count": res.count or 0
    }