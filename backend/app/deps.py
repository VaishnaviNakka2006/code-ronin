from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    print("TOKEN:", token)

    class User:
        id = "251b44c9-c31d-4ff0-836e-1407e86c411c"

    return User()