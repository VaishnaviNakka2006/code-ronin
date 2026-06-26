import asyncio
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.db import supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/battle", tags=["battle"])

# ---------- In‑memory state ----------
active_connections: dict[str, WebSocket] = {}
queues: dict[str, list[str]] = {
    "easy": [],
    "medium": [],
    "hard": []
}
rooms: dict[str, dict] = {}
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
    ws = active_connections.get(user_id)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            active_connections.pop(user_id, None)

# ---------- REST endpoints ----------
@router.get("/room/{room_id}")
async def get_room_info(room_id: str):
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
    """WebSocket endpoint for battle matchmaking."""
    # Authenticate
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=1008, reason="Invalid token")
        return
    user_id = user.id
    username = user.user_metadata.get("username", user.email)

    await websocket.accept()
    active_connections[user_id] = websocket
    logger.info(f"User {username} connected to battle WebSocket")

    try:
        await websocket.send_json({"type": "connected", "user_id": user_id})

        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                msg_type = data.get("type")
                if msg_type == "join_queue":
                    difficulty = data.get("difficulty", "easy")
                    if difficulty not in queues:
                        await websocket.send_json({"type": "error", "message": "Invalid difficulty"})
                        continue
                    async with queue_lock:
                        for diff in queues:
                            if user_id in queues[diff]:
                                queues[diff].remove(user_id)
                        queues[difficulty].append(user_id)
                    await websocket.send_json({"type": "queue_joined", "difficulty": difficulty})
                    logger.info(f"{username} joined {difficulty} queue")

                    # Check for match
                    async with queue_lock:
                        q = queues[difficulty]
                        if len(q) >= 2:
                            p1 = q.pop(0)
                            p2 = q.pop(0)
                            room_id = str(uuid.uuid4())
                            async with room_lock:
                                rooms[room_id] = {
                                    "player1_id": p1,
                                    "player2_id": p2,
                                    "difficulty": difficulty,
                                    "status": "pending"
                                }
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
                    async with queue_lock:
                        for diff in queues:
                            if user_id in queues[diff]:
                                queues[diff].remove(user_id)
                    await websocket.send_json({"type": "queue_left"})
                    logger.info(f"{username} left queue")

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                else:
                    await websocket.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        async with queue_lock:
            for diff in queues:
                if user_id in queues[diff]:
                    queues[diff].remove(user_id)
        active_connections.pop(user_id, None)
        logger.info(f"User {username} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        active_connections.pop(user_id, None)
        await websocket.close(code=1011, reason="Internal error")