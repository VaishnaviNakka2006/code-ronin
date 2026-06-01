from app.main import supabase

class LeaderboardService:
    @staticmethod
    def get_global_leaderboard(limit: int = 50):
        res = supabase.table("profiles") \
            .select("id, username, xp, rank") \
            .order("xp", desc=True) \
            .limit(limit) \
            .execute()
        return res.data

    @staticmethod
    def get_friends_leaderboard(user_id: str, limit: int = 50):
        # Fetch accepted friend IDs
        friend_req = supabase.table("friend_requests") \
            .select("from_user_id, to_user_id") \
            .eq("status", "accepted") \
            .or_(f"from_user_id.eq.{user_id},to_user_id.eq.{user_id}") \
            .execute()
        friend_ids = set()
        for row in friend_req.data:
            if row["from_user_id"] == user_id:
                friend_ids.add(row["to_user_id"])
            else:
                friend_ids.add(row["from_user_id"])
        if not friend_ids:
            return []
        # Fetch profiles of those friends
        res = supabase.table("profiles") \
            .select("id, username, xp, rank") \
            .in_("id", list(friend_ids)) \
            .order("xp", desc=True) \
            .limit(limit) \
            .execute()
        return res.data