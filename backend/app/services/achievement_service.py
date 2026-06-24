from app.db import supabase
from typing import Dict, Any, List, Optional
from datetime import date, timedelta

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
    
    @staticmethod
    def evaluate_and_unlock(user_id: str, trigger_event: str, context: Dict = None) -> List[int]:
        """
        trigger_event: 'mission_complete', 'boss_defeated', 'perfect_score', 'xp_milestone', 'daily_streak'
        context: {'mission_id', 'score', 'xp_before', 'xp_after', 'streak_days', etc.}
        Returns list of newly unlocked achievement ids.
        """
        # Fetch all achievements matching trigger type
        res = supabase.table("achievements").select("*").eq("trigger_type", trigger_event).execute()
        achievements = res.data

        unlocked_ids = AchievementService.get_unlocked_achievement_ids(user_id)
        newly_unlocked = []

        for ach in achievements:
            if ach["id"] in unlocked_ids:
                continue
            config = ach["trigger_config"]
            if AchievementService._check_condition(user_id, ach, config, context):
                # Unlock it
                AchievementService.unlock_achievement(user_id, ach["id"], ach["xp_reward"])
                newly_unlocked.append(ach["id"])
        return newly_unlocked

    @staticmethod
    def _check_condition(user_id: str, achievement: Dict, config: Dict, context: Dict) -> bool:
        trigger = achievement["trigger_type"]
        if trigger == "mission_complete":
            required = config.get("required_count", 1)
            # Count distinct missions completed by user
            res = supabase.table("user_progress").select("mission_id", count="exact").eq("user_id", user_id).execute()
            return res.count >= required
        elif trigger == "boss_defeated":
            required = config.get("required_count", 1)
            # Count boss missions completed (missions where is_boss = True)
            # Join with missions table
            res = supabase.table("user_progress").select("mission_id").eq("user_id", user_id).execute()
            mission_ids = [p["mission_id"] for p in res.data]
            if not mission_ids:
                return False
            # Fetch boss missions from missions table
            boss_res = supabase.table("missions").select("id").in_("id", mission_ids).eq("is_boss", True).execute()
            return len(boss_res.data) >= required
        elif trigger == "perfect_score":
            required = config.get("required_count", 1)
            # Count missions where best_score = 1.0
            res = supabase.table("user_progress").select("mission_id", count="exact").eq("user_id", user_id).eq("best_score", 1.0).execute()
            return res.count >= required
        elif trigger == "xp_milestone":
            required_xp = config.get("required_xp", 0)
            # Get current XP from profiles
            profile_res = supabase.table("profiles").select("xp").eq("id", user_id).execute()
            current_xp = profile_res.data[0]["xp"] if profile_res.data else 0
            return current_xp >= required_xp
        elif trigger == "daily_streak":
            required_days = config.get("required_days", 7)
            # Get streak from profiles
            profile_res = supabase.table("profiles").select("streak_days").eq("id", user_id).execute()
            streak = profile_res.data[0]["streak_days"] if profile_res.data else 0
            return streak >= required_days
        # Add more triggers as needed
        return False
    

