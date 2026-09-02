import asyncio
import json
import logging
import traceback
import uuid
import os

import httpx
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.db import supabase


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/battle", tags=["battle"])


# ============================================================
# PROBLEM POOL
# ============================================================

PROBLEMS = {
    "easy": [
        {
            "title": "Sum of Two Numbers",
            "description": (
                "Write a function `add(a, b)` that returns "
                "the sum of two integers."
            ),
            "starter_code": (
                "def add(a, b):\n"
                "    # Your code here\n"
                "    pass"
            ),
            "test_cases": [
                {"input": "add(2, 3)", "expected": "5"},
                {"input": "add(-1, 1)", "expected": "0"},
            ],
        },
        {
            "title": "Even or Odd",
            "description": (
                "Write a function `is_even(n)` that returns "
                "True if n is even, otherwise False."
            ),
            "starter_code": (
                "def is_even(n):\n"
                "    # Your code here\n"
                "    pass"
            ),
            "test_cases": [
                {"input": "is_even(4)", "expected": "True"},
                {"input": "is_even(7)", "expected": "False"},
            ],
        },
    ],
    "medium": [
        {
            "title": "Factorial",
            "description": (
                "Write a function `factorial(n)` that returns n factorial."
            ),
            "starter_code": (
                "def factorial(n):\n"
                "    # Your code here\n"
                "    pass"
            ),
            "test_cases": [
                {"input": "factorial(5)", "expected": "120"},
                {"input": "factorial(0)", "expected": "1"},
            ],
        }
    ],
    "hard": [
        {
            "title": "Fibonacci",
            "description": (
                "Write a function `fib(n)` that returns "
                "the nth Fibonacci number."
            ),
            "starter_code": (
                "def fib(n):\n"
                "    # Your code here\n"
                "    pass"
            ),
            "test_cases": [
                {"input": "fib(6)", "expected": "8"},
                {"input": "fib(1)", "expected": "1"},
            ],
        }
    ],
}

# ============================================================
# PROBLEM ROTATION STATE
# ============================================================

problem_indexes = {
    difficulty: 0
    for difficulty in PROBLEMS
}

problem_lock = asyncio.Lock()


# ============================================================
# IN-MEMORY STATE
# ============================================================

active_connections: dict[str, WebSocket] = {}

queues: dict[str, list[str]] = {
    "easy": [],
    "medium": [],
    "hard": [],
}

rooms: dict[str, dict] = {}

user_room: dict[str, str] = {}

queue_lock = asyncio.Lock()
room_lock = asyncio.Lock()


# ============================================================
# PROBLEM HELPERS
# ============================================================

async def get_problem_for_difficulty(
    difficulty: str
) -> dict:
    api_key = os.getenv("OLLAMA_API_KEY")

    if not api_key:
        logger.error("OLLAMA_API_KEY is not configured")

        return PROBLEMS["easy"][0]

    prompt = f"""
Generate ONE completely new Python coding challenge.

Difficulty: {difficulty}

The challenge must:
- Have a different programming logic from common recent questions
- Be suitable for a coding battle
- Require a Python function
- Include 2 to 4 simple test cases
- Be solvable in a reasonable time
- Not include the solution
- Return ONLY valid JSON
- Do not use markdown
- Do not add ```json

Return exactly this structure:

{{
    "title": "Problem title",
    "description": "Clear problem description",
    "starter_code": "def function_name(...):\\n    # Your code here\\n    pass",
    "test_cases": [
        {{
            "input": "function_name(...)",
            "expected": "..."
        }},
        {{
            "input": "function_name(...)",
            "expected": "..."
        }}
    ]
}}
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-oss:120b-cloud",
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:

            response = await client.post(
                "https://ollama.com/api/chat",
                headers=headers,
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        content = data["message"]["content"]

        problem = json.loads(content)

        return problem

    except Exception as exc:
        logger.error(
            "AI problem generation failed: %s",
            exc,
        )

        return PROBLEMS.get(
            difficulty,
            PROBLEMS["easy"]
        )[0]

# ============================================================
# AI PROBLEM GENERATION
# ============================================================

async def generate_ai_problem(
    difficulty: str,
    room_id: str,
) -> dict:
    """
    Generate a problem for the battle.
    Falls back to predefined problems if AI generation fails.
    """

    logger.info(
        "Generating problem for room %s with difficulty %s",
        room_id,
        difficulty,
    )

    problem = await get_problem_for_difficulty(
        difficulty
    )

    if not problem:
        logger.error(
            "Problem generation returned None for room %s",
            room_id,
        )

        problem = PROBLEMS.get(
            difficulty,
            PROBLEMS["easy"]
        )[0]

    logger.info(
        "Problem generated for room %s: %s",
        room_id,
        problem.get("title"),
    )

    return problem


# ============================================================
# CODE EXECUTION
# ============================================================

def run_battle_tests(test_cases: list, user_code: str) -> dict:
    """
    Execute submitted Python code against battle test cases.

    MVP implementation.
    """

    passed = 0
    total = len(test_cases)
    details = []

    namespace = {}

    try:
        # Same namespace is important for recursive functions.
        exec(user_code, namespace, namespace)

    except Exception as exc:
        return {
            "success": False,
            "score": 0.0,
            "tests_passed": 0,
            "total_tests": total,
            "output": f"Code error: {str(exc)}",
            "details": [],
        }

    for index, test_case in enumerate(test_cases):
        test_input = test_case.get("input", "")
        expected = str(
            test_case.get("expected", "")
        ).strip()

        try:
            actual_result = eval(
                test_input,
                namespace,
                namespace,
            )

            actual = str(actual_result).strip()

            is_pass = actual == expected

        except Exception as exc:
            actual = str(exc)
            is_pass = False

        if is_pass:
            passed += 1

        details.append(
            {
                "test_id": index + 1,
                "passed": is_pass,
                "expected": expected,
                "actual": actual,
            }
        )

    score = passed / total if total > 0 else 0.0

    output_lines = []

    for detail in details:
        symbol = "✓" if detail["passed"] else "✗"

        output_lines.append(
            f"{symbol} Test {detail['test_id']}: "
            f"expected '{detail['expected']}', "
            f"got '{detail['actual']}'"
        )

    return {
        "success": passed == total,
        "score": score,
        "tests_passed": passed,
        "total_tests": total,
        "output": "\n".join(output_lines),
        "details": details,
    }


# ============================================================
# AUTH HELPERS
# ============================================================

async def get_user_from_token(token: str):
    """
    Validate Supabase JWT and return the user.
    """

    try:
        response = supabase.auth.get_user(token)

        return response.user

    except Exception as exc:
        logger.error(
            "WebSocket authentication error: %s",
            exc,
        )

        return None


# ============================================================
# WEBSOCKET HELPERS
# ============================================================

async def send_to_user(
    user_id: str,
    message: dict,
):
    websocket = active_connections.get(user_id)

    if websocket is None:
        return

    try:
        await websocket.send_json(message)

    except Exception as exc:
        logger.error(
            "Failed to send message to user %s: %s",
            user_id,
            exc,
        )

        active_connections.pop(user_id, None)


async def send_room_state(room_id: str):
    async with room_lock:
        room = rooms.get(room_id)

        if not room:
            return

        player1_id = room["player1_id"]
        player2_id = room["player2_id"]

        state = {
            "type": "room_state",
            "room_id": room_id,
            "status": room["status"],
            "player1_id": player1_id,
            "player1_ready": room.get(
                "player1_ready",
                False,
            ),
            "player2_id": player2_id,
            "player2_ready": room.get(
                "player2_ready",
                False,
            ),
            "difficulty": room["difficulty"],
            "problem": room.get("problem"),
        }

    await send_to_user(player1_id, state)
    await send_to_user(player2_id, state)


async def send_countdown_update(
    room_id: str,
    countdown: int,
):
    async with room_lock:
        room = rooms.get(room_id)

        if not room:
            return

        player1_id = room["player1_id"]
        player2_id = room["player2_id"]

    event = {
        "type": "countdown_update",
        "room_id": room_id,
        "countdown": countdown,
    }

    await send_to_user(player1_id, event)
    await send_to_user(player2_id, event)


async def send_timer_update(
    room_id: str,
    seconds: int,
):
    async with room_lock:
        room = rooms.get(room_id)

        if not room:
            return

        player1_id = room["player1_id"]
        player2_id = room["player2_id"]

    event = {
        "type": "timer_update",
        "room_id": room_id,
        "seconds": seconds,
    }

    await send_to_user(player1_id, event)
    await send_to_user(player2_id, event)


# ============================================================
# COUNTDOWN
# ============================================================

async def start_countdown(room_id: str):
    try:
        async with room_lock:
            room = rooms.get(room_id)

            if not room:
                return

            if room["status"] not in (
                "waiting",
                "ready",
            ):
                return

            room["status"] = "countdown"

        await send_room_state(room_id)

        for number in [3, 2, 1]:
            await send_countdown_update(
                room_id,
                number,
            )

            await asyncio.sleep(1)

        async with room_lock:
            room = rooms.get(room_id)

            if not room:
                return

            difficulty = room["difficulty"]


        problem = await generate_ai_problem(
            difficulty,
            room_id,
        )
        if not problem:
            logger.error(
                "Failed to generate problem for room %s",
                room_id,
            )

            async with room_lock:
                room = rooms.get(room_id)

                if room:
                    room["status"] = "waiting"
                    room["countdown_task"] = None

            await send_room_state(room_id)

            return


        async with room_lock:
            room = rooms.get(room_id)

            if not room:
                return

            room["problem"] = problem
            room["status"] = "active"

            room["started_at"] = (
                datetime.now(timezone.utc).isoformat()
            )

            room["countdown_task"] = None

            player1_id = room["player1_id"]
            player2_id = room["player2_id"]

        logger.info(
           "Sending battle_start for room %s with problem %s",
            room_id,
            problem.get("title"),
        )
        
        battle_start_event = {
            "type": "battle_start",
            "room_id": room_id,
            "problem": problem,
        }

        await send_to_user(
            player1_id,
            battle_start_event,
        )

        await send_to_user(
            player2_id,
            battle_start_event,
        )

        await start_battle_timer(room_id)

        await send_room_state(room_id)

        logger.info(
            "Battle started in room %s",
            room_id,
        )

    except asyncio.CancelledError:
        logger.info(
            "Countdown cancelled for room %s",
            room_id,
        )


# ============================================================
# TIMER
# ============================================================

async def start_battle_timer(room_id: str):
    async with room_lock:
        room = rooms.get(room_id)

        if not room:
            return

        existing_task = room.get("timer_task")

        if (
            existing_task is not None
            and not existing_task.done()
        ):
            existing_task.cancel()

        room["time_remaining"] = 900

        room["timer_task"] = asyncio.create_task(
            tick_timer(room_id)
        )

    await send_timer_update(
        room_id,
        900,
    )


async def tick_timer(room_id: str):
    try:
        while True:
            await asyncio.sleep(1)

            async with room_lock:
                room = rooms.get(room_id)

                if not room:
                    return

                if room.get("status") != "active":
                    return

                remaining = max(
                    0,
                    room.get("time_remaining", 0) - 1,
                )

                room["time_remaining"] = remaining

            await send_timer_update(
                room_id,
                remaining,
            )

            if remaining <= 0:
                await on_timer_end(room_id)
                return

    except asyncio.CancelledError:
        logger.info(
            "Timer cancelled for room %s",
            room_id,
        )


# ============================================================
# BATTLE FINALIZATION
# ============================================================

async def finalize_battle(room_id: str):
    """
    Finalize the battle exactly once.

    Winner rules:
    1. Higher score wins.
    2. If scores are equal, faster final submission wins.
    3. If both are equal, battle is a draw.
    """

    async with room_lock:
        room = rooms.get(room_id)

        if not room:
            return

        if room.get("finalized"):
            return

        room["finalized"] = True

        room["status"] = "finished"

        player1_id = room["player1_id"]
        player2_id = room["player2_id"]

        player1_score = room.get(
            "player1_final_score",
            0.0,
        )

        player2_score = room.get(
            "player2_final_score",
            0.0,
        )

        player1_time = room.get(
            "player1_final_time"
        )

        player2_time = room.get(
            "player2_final_time"
        )

        difficulty = room.get("difficulty")
        problem = room.get("problem")
        started_at = room.get("started_at")

        winner_id = None

        # Higher score wins.
        if player1_score > player2_score:
            winner_id = player1_id

        elif player2_score > player1_score:
            winner_id = player2_id

        # Equal score: faster submission wins.
        else:
            if (
                player1_time is not None
                and player2_time is not None
            ):
                if player1_time < player2_time:
                    winner_id = player1_id

                elif player2_time < player1_time:
                    winner_id = player2_id

            elif (
                player1_time is not None
                and player2_time is None
            ):
                winner_id = player1_id

            elif (
                player2_time is not None
                and player1_time is None
            ):
                winner_id = player2_id

        result_event = {
            "type": "battle_finished",
            "room_id": room_id,
            "winner_id": winner_id,
            "player1_id": player1_id,
            "player2_id": player2_id,
            "player1_score": player1_score,
            "player2_score": player2_score,
            "player1_time": player1_time,
            "player2_time": player2_time,
            "draw": winner_id is None,
            "difficulty": difficulty,
            "problem_title": (
                problem.get("title")
                if problem
                else None
            ),
        }

    # --------------------------------------------------------
    # DATABASE PERSISTENCE
    # Do not hold room_lock during database work.
    # --------------------------------------------------------

    try:
        now = datetime.now(timezone.utc).isoformat()

        supabase.table("battles").insert(
            {
                "room_id": room_id,
                "player1_id": player1_id,
                "player2_id": player2_id,
                "winner_id": winner_id,
                "difficulty": difficulty,
                "problem": problem,
                "player1_score": player1_score,
                "player2_score": player2_score,
                "player1_completion_time": (
                    player1_time
                ),
                "player2_completion_time": (
                    player2_time
                ),
                "status": "finished",
                "started_at": started_at,
                "finished_at": now,
            }
        ).execute()

    except Exception as exc:
        logger.error(
            "Failed to save battle %s: %s",
            room_id,
            exc,
        )

    # --------------------------------------------------------
    # BROADCAST RESULT
    # --------------------------------------------------------

    await send_to_user(
        player1_id,
        result_event,
    )

    await send_to_user(
        player2_id,
        result_event,
    )

    await send_room_state(room_id)

    logger.info(
        "Battle %s finalized. Winner: %s",
        room_id,
        winner_id,
    )


async def on_timer_end(room_id: str):
    """
    Handle timer expiration.
    """

    async with room_lock:
        room = rooms.get(room_id)

        if not room:
            return

        if room.get("finalized"):
            return

        player1_id = room["player1_id"]
        player2_id = room["player2_id"]

        room["time_remaining"] = 0
        room["timer_task"] = None

    timer_end_event = {
        "type": "timer_end",
        "room_id": room_id,
    }

    await send_to_user(
        player1_id,
        timer_end_event,
    )

    await send_to_user(
        player2_id,
        timer_end_event,
    )

    await finalize_battle(room_id)


# ============================================================
# REST ENDPOINTS
# ============================================================

@router.get("/room/{room_id}")
async def get_room_info(room_id: str):
    async with room_lock:
        room = rooms.get(room_id)

        if not room:
            raise HTTPException(
                status_code=404,
                detail="Room not found",
            )

        player1_id = room["player1_id"]
        player2_id = room["player2_id"]

        difficulty = room["difficulty"]
        status = room["status"]

    try:
        player1_response = (
            supabase
            .table("profiles")
            .select("username")
            .eq("id", player1_id)
            .execute()
        )

        player2_response = (
            supabase
            .table("profiles")
            .select("username")
            .eq("id", player2_id)
            .execute()
        )

        player1_username = (
            player1_response.data[0]["username"]
            if player1_response.data
            else "Player 1"
        )

        player2_username = (
            player2_response.data[0]["username"]
            if player2_response.data
            else "Player 2"
        )

    except Exception as exc:
        logger.error(
            "Failed to load player names: %s",
            exc,
        )

        player1_username = "Player 1"
        player2_username = "Player 2"

    return {
        "room_id": room_id,
        "player1_id": player1_id,
        "player1_username": player1_username,
        "player2_id": player2_id,
        "player2_username": player2_username,
        "difficulty": difficulty,
        "status": status,
    }


# ============================================================
# WEBSOCKET ENDPOINT
# ============================================================

@router.websocket("/ws")
async def websocket_battle(
    websocket: WebSocket,
    token: str,
):
    user = await get_user_from_token(token)

    if not user:
        await websocket.close(
            code=1008,
            reason="Invalid token",
        )

        return

    user_id = str(user.id)

    username = (
        user.user_metadata.get(
            "username",
            user.email or "Player",
        )
    )

    await websocket.accept()

    active_connections[user_id] = websocket

    logger.info(
        "Battle WebSocket connected: %s",
        username,
    )

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "user_id": user_id,
            }
        )

        # ----------------------------------------------------
        # Restore existing room after reconnect
        # ----------------------------------------------------

        existing_room = user_room.get(user_id)

        if existing_room:
            async with room_lock:
                room = rooms.get(existing_room)

            if room:
                await websocket.send_json(
                    {
                        "type": "room_joined",
                        "room_id": existing_room,
                    }
                )

                await send_room_state(
                    existing_room
                )

        # ====================================================
        # MAIN MESSAGE LOOP
        # ====================================================

        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)

            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Invalid JSON",
                    }
                )

                continue

            msg_type = data.get("type")

            # =================================================
            # JOIN QUEUE
            # =================================================

            if msg_type == "join_queue":
                difficulty = data.get(
                    "difficulty",
                    "easy",
                )

                if difficulty not in queues:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": (
                                "Invalid difficulty"
                            ),
                        }
                    )

                    continue

                async with queue_lock:
                    for queue in queues.values():
                        if user_id in queue:
                            queue.remove(user_id)

                    queues[difficulty].append(
                        user_id
                    )

                    queue = queues[difficulty]

                    if len(queue) < 2:
                        matched = False

                    else:
                        player1_id = queue.pop(0)
                        player2_id = queue.pop(0)

                        matched = True

                if not matched:
                    await websocket.send_json(
                        {
                            "type": "queue_joined",
                            "difficulty": difficulty,
                        }
                    )

                    continue

                room_id = str(uuid.uuid4())

                async with room_lock:
                    rooms[room_id] = {
                        "player1_id": player1_id,
                        "player2_id": player2_id,
                        "difficulty": difficulty,
                        "status": "waiting",

                        "player1_ready": False,
                        "player2_ready": False,

                        "countdown_task": None,

                        "problem": None,

                        "timer_task": None,
                        "time_remaining": 900,

                        "started_at": None,

                        "player1_final_submitted": False,
                        "player2_final_submitted": False,

                        "player1_final_score": 0.0,
                        "player2_final_score": 0.0,

                        "player1_final_time": None,
                        "player2_final_time": None,

                        "finalized": False,
                    }

                    user_room[
                        player1_id
                    ] = room_id

                    user_room[
                        player2_id
                    ] = room_id

                try:
                    player1_response = (
                        supabase
                        .table("profiles")
                        .select("username")
                        .eq(
                            "id",
                            player1_id,
                        )
                        .execute()
                    )

                    player2_response = (
                        supabase
                        .table("profiles")
                        .select("username")
                        .eq(
                            "id",
                            player2_id,
                        )
                        .execute()
                    )

                    player1_name = (
                        player1_response.data[0][
                            "username"
                        ]
                        if player1_response.data
                        else "Player 1"
                    )

                    player2_name = (
                        player2_response.data[0][
                            "username"
                        ]
                        if player2_response.data
                        else "Player 2"
                    )

                except Exception:
                    player1_name = "Player 1"
                    player2_name = "Player 2"

                await send_to_user(
                    player1_id,
                    {
                        "type": "battle_found",
                        "room_id": room_id,
                        "opponent_username": (
                            player2_name
                        ),
                        "difficulty": difficulty,
                    },
                )

                await send_to_user(
                    player2_id,
                    {
                        "type": "battle_found",
                        "room_id": room_id,
                        "opponent_username": (
                            player1_name
                        ),
                        "difficulty": difficulty,
                    },
                )

                logger.info(
                    "Battle found: %s vs %s",
                    player1_name,
                    player2_name,
                )

            # =================================================
            # LEAVE QUEUE
            # =================================================

            elif msg_type == "leave_queue":
                async with queue_lock:
                    for queue in queues.values():
                        if user_id in queue:
                            queue.remove(user_id)

                await websocket.send_json(
                    {
                        "type": "queue_left",
                    }
                )

            # =================================================
            # JOIN ROOM
            # =================================================

            elif msg_type == "join_room":
                room_id = data.get("room_id")

                if not room_id:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Missing room_id",
                        }
                    )

                    continue

                async with room_lock:
                    room = rooms.get(room_id)

                    if not room:
                        room_exists = False

                    else:
                        room_exists = True

                        if user_id not in (
                            room["player1_id"],
                            room["player2_id"],
                        ):
                            authorized = False

                        else:
                            authorized = True

                            user_room[
                                user_id
                            ] = room_id

                if not room_exists:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Room not found",
                        }
                    )

                    continue

                if not authorized:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": (
                                "You are not in this room"
                            ),
                        }
                    )

                    continue

                await websocket.send_json(
                    {
                        "type": "room_joined",
                        "room_id": room_id,
                    }
                )

                await send_room_state(room_id)

            # =================================================
            # READY
            # =================================================

            elif msg_type == "ready":
                room_id = user_room.get(user_id)

                if not room_id:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Not in a room",
                        }
                    )

                    continue

                should_start_countdown = False

                async with room_lock:
                    room = rooms.get(room_id)

                    if not room:
                        room_found = False

                    else:
                        room_found = True

                        if room["status"] not in (
                            "waiting",
                            "ready",
                        ):
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": (
                                        "Battle already started "
                                        "or finished"
                                    ),
                                }
                            )

                            continue

                        if (
                            user_id
                            == room["player1_id"]
                        ):
                            room[
                                "player1_ready"
                            ] = True

                        elif (
                            user_id
                            == room["player2_id"]
                        ):
                            room[
                                "player2_ready"
                            ] = True

                        if (
                            room[
                                "player1_ready"
                            ]
                            and room[
                                "player2_ready"
                            ]
                        ):
                            room["status"] = "ready"

                            existing_task = room.get(
                                "countdown_task"
                            )

                            if (
                                existing_task is None
                                or existing_task.done()
                            ):
                                should_start_countdown = (
                                    True
                                )

                        else:
                            room["status"] = "waiting"

                if not room_found:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Room not found",
                        }
                    )

                    continue

                await send_room_state(room_id)

                if should_start_countdown:
                    task = asyncio.create_task(
                        start_countdown(room_id)
                    )

                    async with room_lock:
                        room = rooms.get(room_id)

                        if room:
                            room[
                                "countdown_task"
                            ] = task

            # =================================================
            # NOT READY
            # =================================================

            elif msg_type == "not_ready":
                room_id = user_room.get(user_id)

                if not room_id:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Not in a room",
                        }
                    )

                    continue

                async with room_lock:
                    room = rooms.get(room_id)

                    if not room:
                        room_found = False

                    else:
                        room_found = True

                        if room["status"] not in (
                            "waiting",
                            "ready",
                        ):
                            continue

                        if (
                            user_id
                            == room["player1_id"]
                        ):
                            room[
                                "player1_ready"
                            ] = False

                        elif (
                            user_id
                            == room["player2_id"]
                        ):
                            room[
                                "player2_ready"
                            ] = False

                        room["status"] = "waiting"

                        countdown_task = room.get(
                            "countdown_task"
                        )

                        if (
                            countdown_task is not None
                            and not countdown_task.done()
                        ):
                            countdown_task.cancel()

                        room[
                            "countdown_task"
                        ] = None

                if room_found:
                    await send_room_state(
                        room_id
                    )

            # =================================================
            # RUN CODE
            # =================================================

            elif msg_type == "submit_code":
                room_id = user_room.get(user_id)

                if not room_id:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Not in a room",
                        }
                    )

                    continue

                code = data.get("code", "")

                if not code.strip():
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Code is empty",
                        }
                    )

                    continue

                async with room_lock:
                    room = rooms.get(room_id)

                    if not room:
                        problem = None
                        active = False

                    else:
                        active = (
                            room["status"]
                            == "active"
                        )

                        problem = room.get(
                            "problem"
                        )

                if not active:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": (
                                "Battle not active"
                            ),
                        }
                    )

                    continue

                if not problem:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": (
                                "No problem assigned"
                            ),
                        }
                    )

                    continue

                try:
                    result = run_battle_tests(
                        problem.get(
                            "test_cases",
                            [],
                        ),
                        code,
                    )

                    await websocket.send_json(
                        {
                            "type": "code_result",
                            "room_id": room_id,
                            "success": result[
                                "success"
                            ],
                            "score": result[
                                "score"
                            ],
                            "tests_passed": result[
                                "tests_passed"
                            ],
                            "total_tests": result[
                                "total_tests"
                            ],
                            "output": result[
                                "output"
                            ],
                            "details": result[
                                "details"
                            ],
                        }
                    )

                except Exception as exc:
                    logger.error(
                        "Code execution error: %s",
                        exc,
                    )

                    await websocket.send_json(
                        {
                            "type": "code_result",
                            "room_id": room_id,
                            "success": False,
                            "error": str(exc),
                            "output": (
                                "Execution failed"
                            ),
                        }
                    )

            # =================================================
            # SUBMIT FINAL SOLUTION
            # =================================================

            elif msg_type == "submit_final":
                room_id = user_room.get(user_id)

                if not room_id:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Not in a room",
                        }
                    )

                    continue

                code = data.get("code", "")

                if not code.strip():
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Code is empty",
                        }
                    )

                    continue

                async with room_lock:
                    room = rooms.get(room_id)

                    if not room:
                        room_valid = False
                        problem = None
                        is_player1 = False

                    else:
                        room_valid = True

                        if (
                            room["status"]
                            != "active"
                        ):
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": (
                                        "Battle not active"
                                    ),
                                }
                            )

                            continue

                        if room.get("finalized"):
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": (
                                        "Battle already "
                                        "finished"
                                    ),
                                }
                            )

                            continue

                        problem = room.get(
                            "problem"
                        )

                        is_player1 = (
                            user_id
                            == room["player1_id"]
                        )

                        already_submitted = (
                            room[
                                "player1_final_submitted"
                            ]
                            if is_player1
                            else room[
                                "player2_final_submitted"
                            ]
                        )

                        if already_submitted:
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": (
                                        "You already submitted "
                                        "your final solution"
                                    ),
                                }
                            )

                            continue

                if not room_valid:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Room not found",
                        }
                    )

                    continue

                if not problem:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": (
                                "No problem assigned"
                            ),
                        }
                    )

                    continue

                # Execute outside lock.
                try:
                    result = run_battle_tests(
                        problem.get(
                            "test_cases",
                            [],
                        ),
                        code,
                    )

                except Exception as exc:
                    logger.error(
                        "Final submission error: %s",
                        exc,
                    )

                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": (
                                f"Execution error: "
                                f"{str(exc)}"
                            ),
                        }
                    )

                    continue

                should_finalize = False
                opponent_id = None

                async with room_lock:
                    room = rooms.get(room_id)

                    if not room:
                        continue

                    if room.get("finalized"):
                        await websocket.send_json(
                            {
                                "type": "error",
                                "message": (
                                    "Battle already "
                                    "finished"
                                ),
                            }
                        )

                        continue

                    if (
                        room["status"]
                        != "active"
                    ):
                        await websocket.send_json(
                            {
                                "type": "error",
                                "message": (
                                    "Battle not active"
                                ),
                            }
                        )

                        continue

                    current_time = (
                        datetime.now(timezone.utc)
                    )

                    started_at_value = room.get(
                        "started_at"
                    )

                    elapsed = None

                    if started_at_value:
                        started_at = (
                            datetime.fromisoformat(
                                started_at_value
                            )
                        )

                        elapsed = (
                            current_time
                            - started_at
                        ).total_seconds()

                    if is_player1:
                        if room[
                            "player1_final_submitted"
                        ]:
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": (
                                        "You already submitted "
                                        "your final solution"
                                    ),
                                }
                            )

                            continue

                        room[
                            "player1_final_submitted"
                        ] = True

                        room[
                            "player1_final_score"
                        ] = result["score"]

                        room[
                            "player1_final_time"
                        ] = elapsed

                        opponent_id = room[
                            "player2_id"
                        ]

                    else:
                        if room[
                            "player2_final_submitted"
                        ]:
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": (
                                        "You already submitted "
                                        "your final solution"
                                    ),
                                }
                            )

                            continue

                        room[
                            "player2_final_submitted"
                        ] = True

                        room[
                            "player2_final_score"
                        ] = result["score"]

                        room[
                            "player2_final_time"
                        ] = elapsed

                        opponent_id = room[
                            "player1_id"
                        ]

                    should_finalize = (
                        room[
                            "player1_final_submitted"
                        ]
                        and room[
                            "player2_final_submitted"
                        ]
                    )

                # --------------------------------------------------------
                # SAVE USER SUBMISSION
                # --------------------------------------------------------

                try:
                    supabase.table("battle_submissions").insert(
                        {
                            "battle_id": room_id,
                            "user_id": user_id,
                            "code": code,
                            "score": result["score"],
                            "tests_passed": result["tests_passed"],
                            "total_tests": result["total_tests"],
                        }
                    ).execute()

                    logger.info(
                        "Saved battle submission: user=%s room=%s",
                        user_id,
                        room_id,
                    )

                except Exception as exc:
                    logger.error(
                        "Failed to save battle submission: %s",
                        exc,
                    )
                
                # Send acknowledgement.
                await websocket.send_json(
                    {
                        "type": "final_submission_ack",
                        "room_id": room_id,
                        "score": result["score"],
                        "tests_passed": result[
                            "tests_passed"
                        ],
                        "total_tests": result[
                            "total_tests"
                        ],
                        "message": (
                            "Final solution submitted."
                        ),
                    }
                )

                # Notify opponent.
                if opponent_id:
                    await send_to_user(
                        opponent_id,
                        {
                            "type": (
                                "opponent_submitted"
                            ),
                            "room_id": room_id,
                            "player_id": user_id,
                        },
                    )

                # Finalize only after lock is released.
                if should_finalize:
                    await finalize_battle(
                        room_id
                    )

            # =================================================
            # PING
            # =================================================

            elif msg_type == "ping":
                await websocket.send_json(
                    {
                        "type": "pong",
                    }
                )

            # =================================================
            # UNKNOWN MESSAGE
            # =================================================

            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": (
                            "Unknown message type: "
                            f"{msg_type}"
                        ),
                    }
                )

    # ========================================================
    # DISCONNECT
    # ========================================================

    except WebSocketDisconnect:
        logger.info(
            "Battle WebSocket disconnected: %s",
            username,
        )

    except Exception:
        logger.error(
            traceback.format_exc()
        )

    finally:
        active_connections.pop(
            user_id,
            None,
        )

        # Remove only from matchmaking queues.
        async with queue_lock:
            for queue in queues.values():
                if user_id in queue:
                    queue.remove(user_id)

        logger.info(
            "Battle WebSocket cleanup complete "
            "for user %s",
            username,
        )