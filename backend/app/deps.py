from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db import supabase

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )

    token = credentials.credentials

    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "")


    try:
        

        print("TOKEN RECEIVED:", token)
        print("DOT COUNT:", token.count("."))
        auth_user = supabase.auth.get_user(token)

        if not auth_user.user:
            raise HTTPException(401, "Invalid token")

        user_id = auth_user.user.id

        profile = (
            supabase.table("profiles")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )

        if not profile.data:
            raise HTTPException(404, "Profile not found")

        class User:
            pass

        user = User()

        for key, value in profile.data.items():
            setattr(user, key, value)

        return user

    except Exception as e:
        print("AUTH ERROR:", e)
        raise HTTPException(401, "Authentication failed")