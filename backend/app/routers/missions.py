from fastapi import APIRouter, Depends, HTTPException, Request
from app.rate_limiter import limiter
from app.schemas.submission import SubmissionRequest, SubmissionResponse
from app.services.mission_engine import MissionEngine
from app.deps import get_current_user
from app.services.ai_mission_generator import generate_mission as generate_ai_service_mission
from app.db import supabase
from app.services.achievement_service import AchievementService
from app.schemas.ai_submission import (
    AIMissionSubmissionRequest,
    AIMissionSubmissionResponse
)
from app.services.proficiency_service import ProficiencyService

# ---------- Phase 1 imports ----------
from app.services.enemy_service import (
    get_enemy_def,
    compute_enemy_state,
    compute_damage_and_new_defeats,
    is_enabled as enemy_battle_enabled,
)
from app.services.enemy_progress_service import (
    get_defeated_test_ids,
    persist_defeated_test_ids,
)
from app.schemas.enemy import EnemyPublicInfo
# ---------- end Phase 1 imports ----------

import random
from datetime import date, timedelta

router = APIRouter(prefix="/missions", tags=["missions"])

@router.post("/ai/submit", response_model=AIMissionSubmissionResponse)
async def submit_ai_mission(
    submission: AIMissionSubmissionRequest,
    user=Depends(get_current_user)
):
    mission = submission.mission
    test_cases = mission.get("test_cases", [])
    difficulty = mission.get("difficulty", "easy")

    test_result = MissionEngine.run_tests_from_list(
        test_cases,
        submission.code
    )

    xp_map = {
        "easy": 10,
        "medium": 20,
        "hard": 30
    }

    xp_reward = (
        xp_map.get(difficulty, 10)
        if test_result["success"]
        else 0
    )

    if test_result["success"] and xp_reward > 0:

        profile = (
            supabase.table("profiles")
            .select("*")
            .eq("id", str(user.id))
            .execute()
        )

        current_xp = profile.data[0].get("xp", 0)

        supabase.table("profiles").update(
            {
                "xp": current_xp + xp_reward
            }
        ).eq(
            "id",
            str(user.id)
        ).execute()

    supabase.table("user_code_attempts").insert(
        {
            "user_id": str(user.id),
            "mission_id": None,
            "code": submission.code,
            "output": test_result["output"],
            "passed_tests": test_result["tests_passed"],
            "total_tests": test_result["total_tests"]
        }
    ).execute()

    return AIMissionSubmissionResponse(
        success=test_result["success"],
        xp_gained=xp_reward,
        tests_passed=test_result["tests_passed"],
        total_tests=test_result["total_tests"],
        output=test_result["output"],
        message=(
            "Mission completed!"
            if test_result["success"]
            else "Some tests failed. Try again."
        )
    )


@router.post("/{mission_id}/submit", response_model=SubmissionResponse)
async def submit_mission(
    mission_id: int, req: SubmissionRequest, user=Depends(get_current_user)
):

    # FETCH MISSION
    mission_res = supabase.table("missions").select("*").eq("id", mission_id).execute()

    if not mission_res.data:

        raise HTTPException(status_code=404, detail="Mission not found")

    mission = mission_res.data[0]

    # RUN TESTS
    test_result = MissionEngine.run_tests(mission_id, req.code)

    # RECORD USER ATTEMPT
    try:

        supabase.table("user_code_attempts").insert(
            {
                "user_id": str(user.id),
                "mission_id": mission_id,
                "code": req.code,
                "output": test_result["output"],
                "passed_tests": test_result["tests_passed"],
                "total_tests": test_result["total_tests"],
            }
        ).execute()

    except Exception as e:

        print("Attempt logging failed:", e)

    # ---------- Phase 1: enemy battle state ----------
    damage_payload = None
    enemy_payload = None

    if enemy_battle_enabled():
        try:
            enemy_def = get_enemy_def(mission_id, mission.get("difficulty"))

            tc_res = (
                supabase.table("test_cases")
                .select("id, weight")
                .eq("mission_id", mission_id)
                .execute()
            )
            test_cases_for_weights = tc_res.data or []

            already_defeated = get_defeated_test_ids(user.id, mission_id)

            state_before = compute_enemy_state(
                enemy_def, test_cases_for_weights, already_defeated
            )
            hp_before = state_before["current_hp"]

            details = test_result.get("details", [])
            damage_dict, newly_defeated = compute_damage_and_new_defeats(
                enemy_def=enemy_def,
                test_cases=test_cases_for_weights,
                details=details,
                already_defeated_ids=already_defeated,
                hp_before=hp_before,
            )

            canonical_defeated = persist_defeated_test_ids(
                user.id, mission_id, newly_defeated
            )
            state_after = compute_enemy_state(
                enemy_def, test_cases_for_weights, canonical_defeated
            )

            damage_payload = damage_dict
            enemy_payload = {
                "name": enemy_def["name"],
                "sprite_key": enemy_def["sprite_key"],
                "max_hp": enemy_def["max_hp"],
                "hp_before": hp_before,
                "hp_after": state_after["current_hp"],
                "hp_percent": state_after["hp_percent"],
                "defeated": state_after["defeated"],
                "is_boss": enemy_def["is_boss"],
            }
        except Exception as e:
            print("Enemy battle computation failed:", e)
    # ---------- end Phase 1 ----------

    # XP SYSTEM
    xp_gained = 0
    completed = False

    if test_result["success"]:

        try:

            progress_res = (
                supabase.table("user_progress")
                .select("*")
                .eq("user_id", str(user.id))
                .eq("mission_id", mission_id)
                .execute()
            )

            print("PROGRESS DATA:", progress_res.data)

            # FIRST TIME COMPLETION ONLY
            if not progress_res.data:

                completed = True

                xp_base = mission.get("xp_base", 10)

                difficulty_mult = {"easy": 1, "medium": 1.5, "hard": 2, "boss": 3}

                mult = difficulty_mult.get(mission.get("difficulty", "easy"), 1)

                xp_gained = int(xp_base * mult)

                # STORE PROGRESS
                supabase.table("user_progress").insert(
                    {
                        "user_id": str(user.id),
                        "mission_id": mission_id,
                        "xp_earned": xp_gained,
                        "best_score": test_result["score"],
                    }
                ).execute()

                # UPDATE USER XP
                profile = (
                    supabase.table("profiles")
                    .select("*")
                    .eq("id", str(user.id))
                    .execute()
                )

                print("PROFILE DATA:", profile.data)

                current_xp = profile.data[0].get("xp", 0)

                new_xp = current_xp + xp_gained

                # Determine rank
                new_rank = "Scavenger"

                if new_xp >= 100:
                    new_rank = "Hacker"
                elif new_xp >= 30:
                    new_rank = "Runner"

                print("CURRENT XP:", current_xp)
                print("XP GAINED:", xp_gained)
                print("NEW XP:", new_xp)
                print("NEW RANK:", new_rank)

                from datetime import date

                today = date.today()

                current_streak = profile.data[0].get("streak_days", 0)
                last_active = profile.data[0].get("last_active")

                if not last_active:

                    new_streak = 1

                else:

                    last_date = date.fromisoformat(last_active)

                    if last_date == today:

                        new_streak = current_streak

                    elif last_date == today - timedelta(days=1):

                        new_streak = current_streak + 1

                    else:

                        new_streak = 1

                update_res = (
                    supabase.table("profiles")
                    .update({
                        "xp": new_xp,
                        "rank": new_rank,
                        "streak_days": new_streak,
                        "last_active": today.isoformat()
                    })
                    .eq("id", str(user.id))
                    .execute()
                )

                print("UPDATE RESULT:", update_res)

                print("XP UPDATED:", current_xp + xp_gained)

                # ACHIEVEMENT EVALUATION
                AchievementService.evaluate_and_unlock(
                    user.id, "mission_complete", {"mission_id": mission_id}
                )

                # BOSS ACHIEVEMENT
                if mission["is_boss"] == True:
                    print("BOSS MISSION DETECTED")
                    AchievementService.evaluate_and_unlock(user.id, "boss_defeated", {})

                # PERFECT SCORE ACHIEVEMENT
                if test_result["score"] >= 1.0:

                    AchievementService.evaluate_and_unlock(user.id, "perfect_score", {})

                # XP MILESTONE ACHIEVEMENTS
                AchievementService.evaluate_and_unlock(user.id, "xp_milestone", {})

        except Exception as e:

            print("Progress tracking failed:", e)

    # FINAL RESPONSE
    return SubmissionResponse(
        success=test_result["success"],
        score=test_result["score"],
        xp_gained=xp_gained,
        tests_passed=test_result["tests_passed"],
        total_tests=test_result["total_tests"],
        output=test_result["output"],
        completed=completed,
        message=(
            "Mission completed!"
            if test_result["success"]
            else "Some tests failed. Try again."
        ),
        damage=damage_payload,
        enemy_state=enemy_payload,
    )


@router.get("/progress/me")
async def get_my_mission_progress(user=Depends(get_current_user)):
    """Return completed mission IDs for the authenticated player."""
    try:
        result = (
            supabase.table("user_progress")
            .select("mission_id")
            .eq("user_id", str(user.id))
            .execute()
        )

        completed_ids = sorted({
            int(row["mission_id"])
            for row in (result.data or [])
            if row.get("mission_id") is not None
        })

        return {"completed_mission_ids": completed_ids}

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to load mission progress",
        )


@router.get("/{mission_id}")
async def get_mission(mission_id: int):

    res = (
        supabase.table("missions")
        .select("*")
        .eq("id", mission_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(
            status_code=404,
            detail="Mission not found"
        )

    return res.data[0]

@router.get("/generate")
async def generate_mission(difficulty: str = "easy"):

    templates = {
        "easy": [
            {
                "title": "Variable Initialization",
                "description": "Create a variable x = 5 and print it.",
                "xp": 10,
            },
            {
                "title": "Basic Function",
                "description": "Write a function add(a, b) that returns the sum.",
                "xp": 15,
            },
        ],
        "medium": [
            {
                "title": "Loop Scanner",
                "description": "Use a for loop to print numbers 1 to 5.",
                "xp": 25,
            },
            {
                "title": "List Processor",
                "description": "Loop through a list and print each item.",
                "xp": 30,
            },
        ],
        "hard": [
            {
                "title": "Recursive Core",
                "description": "Create a recursive factorial function.",
                "xp": 50,
            }
        ],
    }

    if difficulty not in templates:

        difficulty = "easy"

    mission = random.choice(templates[difficulty])

    return {
        "title": mission["title"],
        "description": mission["description"],
        "difficulty": difficulty,
        "xp_reward": mission["xp"],
    }


@router.get("/test")
async def test_route():
    return {"message": "missions router works"}

@router.post("/generate-ai")
@limiter.limit("1000 per hour")
async def generate_ai_mission(
    request: Request,
    difficulty: str = "easy",
    topic: str = "general",
    adaptive: bool = False,
    user=Depends(get_current_user)
):
    if adaptive:
        proficiency = await ProficiencyService.get_user_proficiency(user.id)

        if proficiency:
            weakest_topic = min(
                proficiency.items(),
                key=lambda x: x[1]
            )

            topic = weakest_topic[0]
            score = weakest_topic[1]

            if score < 0.5:
                difficulty = "easy"

            elif score < 0.8:
                difficulty = "medium"

            else:
                difficulty = "hard"
    try:
        mission = await generate_ai_service_mission(
            difficulty,
            topic
        )

        return mission

    except Exception as e:
        raise HTTPException(
            500,
            f"AI generation failed: {str(e)}"
        )


# ---------- Phase 1: enemy state endpoint ----------
@router.get("/{mission_id}/enemy", response_model=EnemyPublicInfo)
async def get_mission_enemy(
    mission_id: int,
    user=Depends(get_current_user),
):
    """
    Return current enemy state for this user/mission.
    Server-derived HP from persisted defeated_test_ids.
    """
    mission_res = (
        supabase.table("missions").select("*").eq("id", mission_id).execute()
    )
    if not mission_res.data:
        raise HTTPException(status_code=404, detail="Mission not found")
    mission = mission_res.data[0]

    enemy_def = get_enemy_def(mission_id, mission.get("difficulty"))

    tc_res = (
        supabase.table("test_cases")
        .select("id, weight")
        .eq("mission_id", mission_id)
        .execute()
    )
    test_cases = tc_res.data or []

    defeated = get_defeated_test_ids(user.id, mission_id)
    state = compute_enemy_state(enemy_def, test_cases, defeated)
    return EnemyPublicInfo(**state)