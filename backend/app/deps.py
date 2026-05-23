from fastapi import Header, HTTPException
async def get_current_user(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing token"
        )

    # Fake local user
    class User:
        id = "251b44c9-c31d-4ff0-836e-1407e86c411c"

    return User()