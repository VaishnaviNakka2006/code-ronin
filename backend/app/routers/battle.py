import asyncio
import json
import uuid
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.deps import get_current_user
from app.db import supabase
import logging
import traceback
from app.services.mission_engine import MissionEngine

logger = logging.getLogger(__name__)

# ---------- Problem pool ----------
PROBLEMS = {
    "easy": [
        {
            "title": "Sum of Two Numbers",
            "description": "Write a function `add(a, b)` that returns the sum of two integers.",
            "starter_code": "def add(a, b):\n    # Your code here\n    pass",
            "test_cases": [
                {"input": "add(2,3)", "expected": "5"},
                {"input": "add(-1,1)", "expected": "0"}
            ]
        },
        {
            "title": "Even or Odd",
            "description": "Write a function `is_even(n)` that returns True if n is even, else False.",
            "starter_code": "def is_even(n):\n    # Your code here\n    pass",
            "test_cases": [
                {"input": "is_even(4)", "expected": "True"},
                {"input": "is_even(7)", "expected": "False"}
            ]
        }
    ],
    "medium": [
        {
            "title": "Factorial",
            "description": "Write a function `factorial(n)` that returns n! (n factorial).",
            "starter_code": "def factorial(n):\n    # Your code here\n    pass",
            "test_cases": [
                {"input": "factorial(5)", "expected": "120"},
                {"input": "factorial(0)", "expected": "1"}
            ]
        }
    ],
    "hard": [
        {
            "title": "Fibonacci",
            "description": "Write a function `fib(n)` that returns the nth Fibonacci number.",
            "starter_code": "def fib(n):\n    # Your code here\n    pass",
            "test_cases": [
                {"input": "fib(6)", "expected": "8"},
                {"input": "fib(1)", "expected": "1"}
            ]
        }
    ]
}

def get_problem_for_difficulty(difficulty: str, seed: str) -> dict:
    import hashlib

    problems = PROBLEMS.get(difficulty, PROBLEMS["easy"])
    idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(problems)
    return problems[idx]

def _convert_test_cases(test_cases):
    """Convert battle test cases for MissionEngine."""
    return [
        {
            "input": tc.get("input", ""),
            "expected_output": tc.get("expected", ""),
        }
        for tc in test_cases
    ]

def run_battle_tests(test_cases, user_code):
    passed = 0
    total = len(test_cases)
    details = []

    namespace = {}

    try:
        exec(user_code, namespace, namespace)

    except Exception as e:
        return {
            "success": False,
            "score": 0,
            "tests_passed": 0,
            "total_tests": total,
            "output": f"Code error: {str(e)}",
            "details": []
        }

    for index, tc in enumerate(test_cases):

        test_input = tc.get("input", "")
        expected = str(tc.get("expected", "")).strip()

        try:
            actual_result = eval(
                test_input,
                namespace,
                namespace
            )

            actual = str(actual_result).strip()

            is_pass = actual == expected

        except Exception as e:

            actual = str(e)

            is_pass = False

        if is_pass:
            passed += 1

        details.append({
            "test_id": index + 1,
            "passed": is_pass,
            "expected": expected,
            "actual": actual
        })

    score = passed / total if total > 0 else 0

    return {
        "success": passed == total,
        "score": score,
        "tests_passed": passed,
        "total_tests": total,
        "output": "\n".join(
            [
                f"{'✓' if d['passed'] else '✗'} "
                f"Test {d['test_id']}: "
                f"expected '{d['expected']}', "
                f"got '{d['actual']}'"
                for d in details
            ]
        ),
        "details": details
    }

router = APIRouter(prefix="/battle", tags=["battle"])

# ---------- In‑memory state ----------
active_connections: dict[str, WebSocket] = {}
queues: dict[str, list[str]] = {
    "easy": [],
    "medium": [],
    "hard": []
}
rooms: dict[str, dict] = {}
# Track which room each user is currently in (for broadcasting)
user_room: dict[str, str] = {}

# Locks for thread safety
queue_lock = asyncio.Lock()
room_lock = asyncio.Lock()


# ---------- Helper functions ----------
async def get_user_from_token(token: str):
    """Validate JWT and return user dict using the existing Supabase client."""
    try:
        user = supabase.auth.get_user(token)
        return user.user
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return None


async def send_to_user(user_id: str, message: dict):
    print("=" * 60)
    print("SEND_TO_USER")
    print("TARGET:", user_id)
    print("CONNECTED USERS:", list(active_connections.keys()))
    print("MESSAGE:", message)
    print("=" * 60)

    ws = active_connections.get(user_id)

    if ws:
        try:
            await ws.send_json(message)
            print("MESSAGE SENT")
        except Exception as e:
            print("SEND ERROR:", e)
            active_connections.pop(user_id, None)
    else:
        print("NO WEBSOCKET FOUND")


async def send_room_state(room_id: str):
    """Broadcast the current room state to both players."""
    async with room_lock:
        room = rooms.get(room_id)
        if not room:
            return
        state = {
            "type": "room_state",
            "room_id": room_id,
            "status": room["status"],
            "player1_id": room["player1_id"],
            "player1_ready": room.get("player1_ready", False),
            "player2_id": room["player2_id"],
            "player2_ready": room.get("player2_ready", False),
            "difficulty": room["difficulty"]
        }
    # Send to both players
    await send_to_user(room["player1_id"], state)
    await send_to_user(room["player2_id"], state)

async def send_countdown_update(room_id: str, countdown: int):
    """Send countdown to both players."""

    async with room_lock:
        room = rooms.get(room_id)

        if not room:
            return

    await send_to_user(
        room["player1_id"],
        {
            "type": "countdown_update",
            "room_id": room_id,
            "countdown": countdown
        }
    )

    await send_to_user(
        room["player2_id"],
        {
            "type": "countdown_update",
            "room_id": room_id,
            "countdown": countdown
        }
    )

async def start_countdown(room_id: str):

    try:

        async with room_lock:

            room = rooms.get(room_id)

            if not room:
                return

            room["status"] = "countdown"

        await send_room_state(room_id)

        for i in [3, 2, 1]:

            await send_countdown_update(room_id, i)

            await asyncio.sleep(1)

        async with room_lock:

            room = rooms.get(room_id)

            if not room:
                return

            difficulty = room["difficulty"]

            problem = get_problem_for_difficulty(
                difficulty,
                room_id
            )

            room["problem"] = problem
            room["status"] = "active"
            room["countdown_task"] = None

        await send_to_user(
            room["player1_id"],
            {
                "type": "battle_start",
                "room_id": room_id,
                "problem": problem
            }
        )

        await send_to_user(
            room["player2_id"],
            {
                "type": "battle_start",
                "room_id": room_id,
                "problem": problem
            }
        )

        await start_battle_timer(room_id)

        await send_room_state(room_id)

        logger.info(
            f"Battle started in room {room_id} with problem: {problem['title']}"
        )

    except asyncio.CancelledError:

        logger.info(f"Countdown cancelled for {room_id}")


async def start_battle_timer(room_id: str):
    """Run a 15‑minute battle timer, sending updates every second."""
    async with room_lock:
        room = rooms.get(room_id)
        if not room:
            return
        # Cancel any existing timer task
        if room.get("timer_task") and not room["timer_task"].done():
            room["timer_task"].cancel()
        room["time_remaining"] = 900  # 15 minutes
        room["timer_task"] = asyncio.create_task(_tick_timer(room_id))
        # Send initial timer update immediately
        await send_timer_update(room_id, room["time_remaining"])

async def _tick_timer(room_id: str):
    """Internal function that ticks the timer every second."""
    while True:
        await asyncio.sleep(1)
        async with room_lock:
            room = rooms.get(room_id)
            if not room:
                return
            if "time_remaining" not in room:
                return
            room["time_remaining"] -= 1
            remaining = room["time_remaining"]
        # Broadcast update
        await send_timer_update(room_id, remaining)
        if remaining <= 0:
            # Timer ended
            await on_timer_end(room_id)
            return

async def send_timer_update(room_id: str, seconds: int):
    """Send a timer_update event to both players."""
    async with room_lock:
        room = rooms.get(room_id)
        if not room:
            return
    await send_to_user(room["player1_id"], {"type": "timer_update", "seconds": seconds, "room_id": room_id})
    await send_to_user(room["player2_id"], {"type": "timer_update", "seconds": seconds, "room_id": room_id})

async def on_timer_end(room_id: str):
    """Handle timer expiration – broadcast event and update room status."""
    async with room_lock:
        room = rooms.get(room_id)
        if not room:
            return
        # Set status to 'finished' (we'll use this later for winner detection)
        room["status"] = "finished"
        if room.get("timer_task"):
            room["timer_task"] = None
    # Broadcast timer_end event
    await send_to_user(room["player1_id"], {"type": "timer_end", "room_id": room_id})
    await send_to_user(room["player2_id"], {"type": "timer_end", "room_id": room_id})
    logger.info(f"Timer ended in room {room_id}")




# ---------- REST endpoints ----------
@router.get("/room/{room_id}")
async def get_room_info(room_id: str):
    import os

    print("=" * 60)
    print("PID:", os.getpid())
    print("GET ROOM:", room_id)
    print("ROOMS:", list(rooms.keys()))
    print("=" * 60)
    """Get basic room info for the battle page."""
    async with room_lock:
        room = rooms.get(room_id)
        if not room:
            raise HTTPException(404, "Room not found")
    # Fetch usernames
    p1 = supabase.table("profiles").select("username").eq("id", room["player1_id"]).execute()
    p2 = supabase.table("profiles").select("username").eq("id", room["player2_id"]).execute()
    return {
        "room_id": room_id,
        "player1_id": room["player1_id"],
        "player1_username": p1.data[0]["username"] if p1.data else "Unknown",
        "player2_id": room["player2_id"],
        "player2_username": p2.data[0]["username"] if p2.data else "Unknown",
        "difficulty": room["difficulty"],
        "status": room["status"]
    }


# ---------- WebSocket endpoint ----------
@router.websocket("/ws")
async def websocket_battle(websocket: WebSocket, token: str):
    """WebSocket endpoint for battle matchmaking and battle room communication."""
    # Authenticate
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=1008, reason="Invalid token")
        return
    user_id = user.id
    username = user.user_metadata.get("username", user.email)

    await websocket.accept()
    active_connections[user_id] = websocket
    # Restore room after reconnect
    existing_room = user_room.get(user_id)

    if existing_room:
        await websocket.send_json({
            "type": "room_joined",
            "room_id": existing_room
        })

        await send_room_state(existing_room)
    logger.info(f"User {username} connected to battle WebSocket")

    try:
        await websocket.send_json({"type": "connected", "user_id": user_id})

        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                msg_type = data.get("type")

                # ---------- Matchmaking commands ----------
                if msg_type == "join_queue":
                    print(f"JOIN_QUEUE: {username} ({user_id})")
                    difficulty = data.get("difficulty", "easy")
                    if difficulty not in queues:
                        await websocket.send_json({"type": "error", "message": "Invalid difficulty"})
                        continue
                    async with queue_lock:
                        print("================================================")
                        print("BEFORE:", queues)

                        for diff in queues:
                            if user_id in queues[diff]:
                                queues[diff].remove(user_id)

                        queues[difficulty].append(user_id)

                        print("AFTER:", queues)
                        print("QUEUE LENGTH:", len(queues[difficulty]))

                        # ADD THESE LINES
                        print("=" * 60)
                        print("PID:", os.getpid())
                        print("QUEUE:", queues[difficulty])
                        print("QUEUE LENGTH:", len(queues[difficulty]))
                        print("=" * 60)

                        print("================================================")
                    await websocket.send_json({"type": "queue_joined", "difficulty": difficulty})
                    logger.info(f"{username} joined {difficulty} queue")

                    # Check for match
                    async with queue_lock:
                        q = queues[difficulty]

                        print(f"Queue length for {difficulty}: {len(q)}")

                        # ADD THESE LINES
                        print("=" * 60)
                        print("PID:", os.getpid())
                        print("MATCH CHECK")
                        print("QUEUE:", q)
                        print("LENGTH:", len(q))
                        print("=" * 60)

                        if len(q) >= 2:
                            p1 = q.pop(0)
                            p2 = q.pop(0)
                            room_id = str(uuid.uuid4())
                            async with room_lock:
                                rooms[room_id] = {
                                    "player1_id": p1,
                                    "player2_id": p2,
                                    "difficulty": difficulty,
                                    "status": "waiting",
                                    "player1_ready": False,
                                    "player2_ready": False,
                                    "countdown_task": None,
                                    "problem": None,
                                    "timer_task": None,
                                    "timer_remaining":900,
                                }

                
                           

                                print("=" * 60)
                                print("PID:", os.getpid())
                                print("ROOM CREATED:", room_id)
                                print("ROOMS:", list(rooms.keys()))
                                print("=" * 60)
                            # Fetch usernames
                            p1_user = supabase.table("profiles").select("username").eq("id", p1).execute()
                            p2_user = supabase.table("profiles").select("username").eq("id", p2).execute()
                            p1_name = p1_user.data[0]["username"] if p1_user.data else "Player1"
                            p2_name = p2_user.data[0]["username"] if p2_user.data else "Player2"

                            await send_to_user(p1, {
                                "type": "battle_found",
                                "room_id": room_id,
                                "opponent_username": p2_name,
                                "difficulty": difficulty
                            })
                            await send_to_user(p2, {
                                "type": "battle_found",
                                "room_id": room_id,
                                "opponent_username": p1_name,
                                "difficulty": difficulty
                            })
                            logger.info(f"Match found: {p1_name} vs {p2_name} in room {room_id}")

                elif msg_type == "leave_queue":
                    print("=" * 60)
                    print("LEAVE_QUEUE RECEIVED")
                    print("USER:", username)
                    print("USER ID:", user_id)
                    print("PID:", os.getpid())
                    print("DATA:", data)
                    print("=" * 60)

                    async with queue_lock:
                        for diff in queues:
                            if user_id in queues[diff]:
                                queues[diff].remove(user_id)

                    await websocket.send_json({
                        "type": "queue_left"
                    })

                    logger.info(f"{username} left queue")

                # ---------- Battle room commands ----------
                elif msg_type == "join_room":
                    room_id = data.get("room_id")
                    if not room_id:
                        await websocket.send_json({"type": "error", "message": "Missing room_id"})
                        continue
                    async with room_lock:
                        room = rooms.get(room_id)
                        if not room:
                            await websocket.send_json({"type": "error", "message": "Room not found"})
                            continue
                        # Verify user is part of this room
                        if user_id not in (room["player1_id"], room["player2_id"]):
                            await websocket.send_json({"type": "error", "message": "You are not in this room"})
                            continue
                        # Store room mapping
                        # Store room mapping
                        user_room[user_id] = room_id

                        logger.info(f"{username} joined room {room_id}")

                        # Tell this client the join succeeded
                        await websocket.send_json({
                            "type": "room_joined",
                            "room_id": room_id
                        })

                    # Send current room state
                    await send_room_state(room_id)

                elif msg_type == "ready":
                    room_id = user_room.get(user_id)
                    if not room_id:
                        await websocket.send_json({"type": "error", "message": "Not in a room"})
                        continue
                    async with room_lock:
                        room = rooms.get(room_id)
                        if not room:
                            await websocket.send_json({"type": "error", "message": "Room not found"})
                            continue
                        if room["status"] not in ("waiting", "ready"):
                            await websocket.send_json({"type": "error", "message": "Cannot ready now"})
                            continue
                        # Set user ready
                        if room["player1_id"] == user_id:
                            room["player1_ready"] = True
                        elif room["player2_id"] == user_id:
                            room["player2_ready"] = True
                        # Update room status
                        if room.get("player1_ready") and room.get("player2_ready"):

                            room["status"] = "ready"

                            if (
                                room.get("countdown_task") is None
                                or room["countdown_task"].done()
                            ):

                                task = asyncio.create_task(start_countdown(room_id))

                                room["countdown_task"] = task

                        else:

                            room["status"] = "waiting"
                    await send_room_state(room_id)

                elif msg_type == "not_ready":
                    room_id = user_room.get(user_id)
                    if not room_id:
                        await websocket.send_json({"type": "error", "message": "Not in a room"})
                        continue
                    async with room_lock:
                        room = rooms.get(room_id)
                        if not room:
                            await websocket.send_json({"type": "error", "message": "Room not found"})
                            continue
                        if room["status"] not in ("waiting", "ready"):
                            await websocket.send_json({"type": "error", "message": "Cannot change ready now"})
                            continue
                        # Unset user ready
                        if room["player1_id"] == user_id:
                            room["player1_ready"] = False
                        elif room["player2_id"] == user_id:
                            room["player2_ready"] = False
                        room["status"] = "waiting"
                        if (
                            room.get("countdown_task")
                            and not room["countdown_task"].done()
                        ):
                            room["countdown_task"].cancel()
                            room["countdown_task"] = None
                    await send_room_state(room_id)


                elif msg_type == "submit_code":
                    room_id = user_room.get(user_id)

                    if not room_id:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Not in a room"
                        })
                        continue

                    code = data.get("code", "")

                    if not code.strip():
                        await websocket.send_json({
                            "type": "error",
                            "message": "Code is empty"
                        })
                        continue

                    async with room_lock:
                        room = rooms.get(room_id)

                        if not room:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Room not found"
                            })
                            continue

                        if room["status"] != "active":
                            await websocket.send_json({
                                "type": "error",
                                "message": "Battle not active"
                            })
                            continue

                        problem = room.get("problem")

                        if not problem:
                            await websocket.send_json({
                                "type": "error",
                                "message": "No problem assigned"
                            })
                            continue

                        test_cases = problem.get("test_cases", [])

                    converted_test_cases = _convert_test_cases(test_cases)

                    try:
                        result = MissionEngine.run_tests_from_list(
                            converted_test_cases,
                            code
                        )

                        await websocket.send_json({
                            "type": "code_result",
                            "room_id": room_id,
                            "success": result["success"],
                            "score": result["score"],
                            "tests_passed": result["tests_passed"],
                            "total_tests": result["total_tests"],
                            "output": result["output"],
                            "details": result["details"]
                        })

                    except Exception as e:
                        logger.error(
                            f"Code execution error for {user_id}: {e}"
                        )

                        await websocket.send_json({
                            "type": "code_result",
                            "room_id": room_id,
                            "success": False,
                            "error": str(e),
                            "output": "Execution failed"
                        })
                

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                else:
                    await websocket.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        # Clean up: remove from queue and active connections
        async with queue_lock:
            for diff in queues:
                if user_id in queues[diff]:
                    queues[diff].remove(user_id)
        # Remove from room if any, and broadcast updated room state
        room_id = user_room.get(user_id)
        if room_id:
            async with room_lock:
                room = rooms.get(room_id)
                if room:
                    # Cancel countdown if running
                    if (
                        room.get("countdown_task")
                        and not room["countdown_task"].done()
                    ):
                        room["countdown_task"].cancel()
                        room["countdown_task"] = None

                    if (
                        room.get("timer_task")
                        and not room["timer_task"].done()
                    ):
                        room["timer_task"].cancel()
                        room["timer_task"] = None
                    # Mark this user as not ready if they were
                    if room.get("player1_id") == user_id:
                        room["player1_ready"] = False
                    elif room.get("player2_id") == user_id:
                        room["player2_ready"] = False
                    # If both players are disconnected, we could delete the room, but we'll keep it.
                    # Update room status to waiting (since one player may still be there)
                    room["status"] = "waiting"
            # Broadcast updated state to the other player if they are still connected
            await send_room_state(room_id)
        active_connections.pop(user_id, None)
        logger.info(f"User {username} disconnected")

    except Exception as e:
        logger.error(traceback.format_exc())
        # Clean up
        active_connections.pop(user_id, None)
        room_id = user_room.get(user_id)
        if room_id:
            # Optionally broadcast state change
            async with room_lock:
                room = rooms.get(room_id)
                if room:
                    # Cancel countdown if running
                    if (
                        room.get("countdown_task")
                        and not room["countdown_task"].done()
                    ):
                        room["countdown_task"].cancel()
                        room["countdown_task"] = None
                    if (
                        room.get("timer_task")
                        and not room["timer_task"].done()
                    ):
                        room["timer_task"].cancel()
                        room["timer_task"] = None
                    if room.get("player1_id") == user_id:
                        room["player1_ready"] = False
                    elif room.get("player2_id") == user_id:
                        room["player2_ready"] = False
                    room["status"] = "waiting"
            await send_room_state(room_id)
        await websocket.close(code=1011, reason="Internal error")