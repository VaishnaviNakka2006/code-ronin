from fastapi import APIRouter, Depends
from app.services.achievement_service import AchievementService
from app.deps import get_current_user

router = APIRouter(prefix="/achievements", tags=["achievements"])

@router.get("/")
async def list_achievements(user=Depends(get_current_user)):
    all_ach = AchievementService.get_all_achievements()
    unlocked_ids = AchievementService.get_user_achievements(user.id)
    for ach in all_ach:
        ach["unlocked"] = ach["id"] in unlocked_ids
    return all_ach

@router.post("/test-unlock")
async def test_unlock():
    AchievementService.unlock_achievement(
        user_id="251b44c9-c31d-4ff0-836e-1407e86c411c",
        achievement_id=1,
        xp_reward=50
    )

    return {"success": True}