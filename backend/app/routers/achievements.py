from app.main import supabase
from fastapi import APIRouter, Depends
from app.services.achievement_service import AchievementService
from app.deps import get_current_user

router = APIRouter(prefix="/achievements", tags=["achievements"])

@router.get("/")
async def list_achievements(user=Depends(get_current_user)):

    # GET ALL ACHIEVEMENTS
    all_ach = AchievementService.get_all_achievements()

    # GET USER UNLOCKED ACHIEVEMENTS
    unlocked_data = (
        supabase
        .table("user_achievements")
        .select("achievement_id, unlocked_at")
        .eq("user_id", user.id)
        .execute()
    )

    # CREATE MAP
    unlocked_map = {
        item["achievement_id"]: item["unlocked_at"]
        for item in unlocked_data.data
    }

    # ADD UNLOCK STATUS
    for ach in all_ach:

        ach["unlocked"] = (
            ach["id"] in unlocked_map
        )

        ach["unlocked_at"] = (
            unlocked_map.get(ach["id"])
        )

    return all_ach

@router.post("/test-unlock")
async def test_unlock():
    AchievementService.unlock_achievement(
        user_id="251b44c9-c31d-4ff0-836e-1407e86c411c",
        achievement_id=1,
        xp_reward=50
    )

    return {"success": True}