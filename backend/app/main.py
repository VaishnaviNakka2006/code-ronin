from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.db import supabase
from dotenv import load_dotenv
import os

from app.routers.user import router as user_router
from app.routers.leaderboard import router as leaderboard_router
from app.routers.missions import router as missions_router
from app.routers.ai import router as ai_router
from app.routers import achievements
from fastapi.security import HTTPBearer
from fastapi import Security
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from app.routers import friends
from app.routers import profile
from app.routers import notifications

from app.websocket import manager

load_dotenv()

app = FastAPI(title="NEXUS Code Ronin API")
security = HTTPBearer()


app.include_router(user_router)
app.include_router(leaderboard_router)
app.include_router(missions_router)
app.include_router(ai_router)
app.include_router(achievements.router)
app.include_router(friends.router)
app.include_router(profile.router)
app.include_router(notifications.router)



# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase
# Root
@app.get("/")
async def root():
    return {
        "message": "NEXUS backend online"
    }

# Health
@app.get("/health")
async def health():
    return {
        "status": "NEXUS API online"
    }

# User
@app.get("/user/{user_id}")
async def get_user(user_id: str):
    try:
        res = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .execute()
        )

        if not res.data:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return res.data[0]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    

@app.websocket("/ws/pvp")
async def websocket_endpoint(
    websocket: WebSocket
):

    await manager.connect(
        websocket
    )

    try:

        while True:

            data = await websocket.receive_text()

            await manager.broadcast(
                f"⚔️ {data}"
            )

    except WebSocketDisconnect:

        manager.disconnect(
            websocket
        )
