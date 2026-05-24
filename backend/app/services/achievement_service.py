from app.main import supabase
from typing import Dict, Any, List, Optional

class AchievementService:
    @staticmethod
    def get_all_achievements() -> List[Dict]:
        res = supabase.table("achievements").select("*").execute()
        return res.data

    @staticmethod
    def get_user_achievements(user_id: str) -> List[int]:
        res = (
            supabase
            .table("user_achievements")
            .select("achievement_id")
            .eq("user_id", user_id)
            .execute()
        )

        return [item["achievement_id"] for item in res.data]

    @staticmethod
    def unlock_achievement(user_id: str, achievement_id: int, xp_reward: int) -> bool:

        print("USER ID:", user_id)
        print("ACHIEVEMENT ID:", achievement_id)

        # Check if already unlocked
        existing = (
            supabase
            .table("user_achievements")
            .select("*")
            .eq("user_id", user_id)
            .eq("achievement_id", achievement_id)
            .execute()
        )

        print("EXISTING:", existing.data)

        if existing.data:
            print("ALREADY UNLOCKED")
            return False

        # Insert achievement unlock
        insert_result = (
            supabase
            .table("user_achievements")
            .insert({
                "user_id": user_id,
                "achievement_id": achievement_id
            })
            .execute()
        )

        print("INSERT RESULT:", insert_result.data)

        # Get current XP
        profile = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .execute()
        )

        print("PROFILE DATA:", profile.data)

        if not profile.data:
            print("PROFILE NOT FOUND")
            return False

        current_xp = profile.data[0].get("xp", 0)

        print("CURRENT XP:", current_xp)

        new_xp = current_xp + xp_reward

        print("NEW XP:", new_xp)

        # Update XP
        update_result = (
            supabase
            .table("profiles")
            .update({
                "xp": new_xp
            })
            .eq("id", user_id)
            .execute()
        )

        print("UPDATE RESULT:", update_result.data)

        return True

    @staticmethod
    def get_unlocked_achievement_ids(user_id: str) -> List[int]:
        res = (
            supabase
            .table("user_achievements")
            .select("achievement_id")
            .eq("user_id", user_id)
            .execute()
        )

        return [r["achievement_id"] for r in res.data]