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

    try:
        print("TOKEN RECEIVED:", token)
        print("DOT COUNT:", token.count("."))

        auth_response = supabase.auth.get_user(token)

        # Supabase v2.x
        auth_user = auth_response.user

        if auth_user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        user_id = auth_user.id

        profile = (
            supabase.table("profiles")
            .select("*")
            .eq("id", user_id)
            .execute()
        )

        # First login → automatically create profile
        if not profile.data:

            username = (
                auth_user.user_metadata.get("username")
                or auth_user.user_metadata.get("full_name")
                or auth_user.email.split("@")[0]
            )

            supabase.table("profiles").insert({
                "id": user_id,
                "username": username,
                "xp": 0,
                "rank": "Scavenger",
                "streak_days": 0
            }).execute()

            profile = (
                supabase.table("profiles")
                .select("*")
                .eq("id", user_id)
                .execute()
            )

        class User:
            pass

        user = User()

        for key, value in profile.data[0].items():
            setattr(user, key, value)

        return user

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("AUTH ERROR:", e)

        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )