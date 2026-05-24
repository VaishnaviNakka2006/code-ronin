from fastapi import APIRouter, Depends, HTTPException
from app.schemas.submission import (
    SubmissionRequest,
    SubmissionResponse
)
from app.services.mission_engine import MissionEngine
from app.deps import get_current_user
from app.db import supabase

import random

router = APIRouter(
    prefix="/missions",
    tags=["missions"]
)


@router.post("/{mission_id}/submit", response_model=SubmissionResponse)
async def submit_mission(
    mission_id: int,
    req: SubmissionRequest,
    user=Depends(get_current_user)
):

    # FETCH MISSION
    mission_res = (
        supabase
        .table("missions")
        .select("*")
        .eq("id", mission_id)
        .execute()
    )

    if not mission_res.data:

        raise HTTPException(
            status_code=404,
            detail="Mission not found"
        )

    mission = mission_res.data[0]

    # RUN TESTS
    test_result = MissionEngine.run_tests(
        mission_id,
        req.code
    )

    # RECORD USER ATTEMPT
    try:

        supabase.table(
            "user_code_attempts"
        ).insert({

            "user_id": str(user.id),

            "mission_id": mission_id,

            "code": req.code,

            "output": test_result["output"],

            "passed_tests":
            test_result["tests_passed"],

            "total_tests":
            test_result["total_tests"]

        }).execute()

    except Exception as e:

        print(
            "Attempt logging failed:",
            e
        )

    # XP SYSTEM
    xp_gained = 0
    completed = False

    if test_result["success"]:

        try:

            progress_res = (
                supabase
                .table("user_progress")
                .select("*")
                .eq("user_id", str(user.id))
                .eq("mission_id", mission_id)
                .execute()
            )

            # FIRST TIME COMPLETION ONLY
            if not progress_res.data:

                completed = True

                xp_base = mission.get(
                    "xp_base",
                    10
                )

                difficulty_mult = {

                    "easy": 1,

                    "medium": 1.5,

                    "hard": 2,

                    "boss": 3
                }

                mult = difficulty_mult.get(
                    mission.get(
                        "difficulty",
                        "easy"
                    ),
                    1
                )

                xp_gained = int(
                    xp_base * mult
                )

                # STORE PROGRESS
                supabase.table(
                    "user_progress"
                ).insert({

                    "user_id":
                    str(user.id),

                    "mission_id":
                    mission_id,

                    "xp_earned":
                    xp_gained,

                    "best_score":
                    test_result["score"]

                }).execute()

                # UPDATE USER XP
                profile = (
                    supabase
                    .table("profiles")
                    .select("xp")
                    .eq("id", str(user.id))
                    .execute()
                )

                current_xp = profile.data[0]["xp"]

                supabase.table(
                    "profiles"
                ).update({

                    "xp":
                    current_xp + xp_gained

                }).eq(
                    "id",
                    str(user.id)
                ).execute()

                print(
                    "XP UPDATED:",
                    current_xp + xp_gained
                )

        except Exception as e:

            print(
                "Progress tracking failed:",
                e
            )

    # FINAL RESPONSE
    return SubmissionResponse(

        success=test_result["success"],

        score=test_result["score"],

        xp_gained=xp_gained,

        tests_passed=
        test_result["tests_passed"],

        total_tests=
        test_result["total_tests"],

        output=test_result["output"],

        completed=completed,

        message=(
            "Mission completed!"
            if test_result["success"]
            else
            "Some tests failed. Try again."
        )
    )


@router.get("/generate")
async def generate_mission(
    difficulty: str = "easy"
):

    templates = {

        "easy": [

            {

                "title":
                "Variable Initialization",

                "description":
                "Create a variable x = 5 and print it.",

                "xp":
                10
            },

            {

                "title":
                "Basic Function",

                "description":
                "Write a function add(a, b) that returns the sum.",

                "xp":
                15
            }
        ],

        "medium": [

            {

                "title":
                "Loop Scanner",

                "description":
                "Use a for loop to print numbers 1 to 5.",

                "xp":
                25
            },

            {

                "title":
                "List Processor",

                "description":
                "Loop through a list and print each item.",

                "xp":
                30
            }
        ],

        "hard": [

            {

                "title":
                "Recursive Core",

                "description":
                "Create a recursive factorial function.",

                "xp":
                50
            }
        ]
    }

    if difficulty not in templates:

        difficulty = "easy"

    mission = random.choice(
        templates[difficulty]
    )

    return {

        "title":
        mission["title"],

        "description":
        mission["description"],

        "difficulty":
        difficulty,

        "xp_reward":
        mission["xp"]
    }


@router.get("/test")
async def test_route():
    return {"message": "missions router works"}






