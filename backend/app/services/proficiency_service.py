from app.db import supabase
from collections import defaultdict

class ProficiencyService:
    @staticmethod
    async def get_user_proficiency(user_id: str) -> dict:
        # Fetch all user progress (missions completed with best_score)
        progress_res = supabase.table("user_progress") \
            .select("mission_id, best_score") \
            .eq("user_id", user_id) \
            .execute()
        
        if not progress_res.data:
            return {}
        
        # Fetch mission topics
        mission_ids = list(set([p["mission_id"] for p in progress_res.data]))
        missions_res = supabase.table("missions") \
            .select("id, topic") \
            .in_("id", mission_ids) \
            .execute()
        topic_map = {m["id"]: m["topic"] for m in missions_res.data}
        
        # Aggregate scores per topic
        topic_scores = defaultdict(list)
        for prog in progress_res.data:
            mission_id = prog["mission_id"]
            topic = topic_map.get(mission_id, "general")
            topic_scores[topic].append(prog["best_score"])
        
        # Compute average score per topic
        proficiency = {}
        for topic, scores in topic_scores.items():
            avg = sum(scores) / len(scores)
            proficiency[topic] = round(avg, 2)
        return proficiency