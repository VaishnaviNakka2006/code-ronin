import asyncio
import json
import uuid
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.deps import get_current_user
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
    """Send a JSON message to a specific user if connected."""
    ws = active_connections.get(user_id)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            active_connections.pop(user_id, None)


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
                        print("================================================")
                    await websocket.send_json({"type": "queue_joined", "difficulty": difficulty})
                    logger.info(f"{username} joined {difficulty} queue")

                    # Check for match
                    async with queue_lock:
                        q = queues[difficulty]
                        print(f"Queue length for {difficulty}: {len(q)}")
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
                    async with queue_lock:
                        for diff in queues:
                            if user_id in queues[diff]:
                                queues[diff].remove(user_id)
                    await websocket.send_json({"type": "queue_left"})
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
                    await send_room_state(room_id)

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
        room_id = user_room.pop(user_id, None)
        if room_id:
            async with room_lock:
                room = rooms.get(room_id)
                if room:
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
        logger.error(f"WebSocket error: {e}")
        # Clean up
        active_connections.pop(user_id, None)
        room_id = user_room.pop(user_id, None)
        if room_id:
            # Optionally broadcast state change
            async with room_lock:
                room = rooms.get(room_id)
                if room:
                    if room.get("player1_id") == user_id:
                        room["player1_ready"] = False
                    elif room.get("player2_id") == user_id:
                        room["player2_ready"] = False
                    room["status"] = "waiting"
            await send_room_state(room_id)
        await websocket.close(code=1011, reason="Internal error")