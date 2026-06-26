from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_current_user
from app.db import supabase

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/request/{target_user_id}")
async def send_friend_request(target_user_id: str, user=Depends(get_current_user)):
    try:

        print("CURRENT USER:", user.id)
        print("TARGET USER:", target_user_id)

        if user.id == target_user_id:
            raise HTTPException(400, "Cannot friend yourself")

        existing = (
            supabase.table("friend_requests")
            .select("*")
            .or_(
                f"and(from_user_id.eq.{user.id},to_user_id.eq.{target_user_id}),and(from_user_id.eq.{target_user_id},to_user_id.eq.{user.id})"
            )
            .execute()
        )

        print("EXISTING:", existing.data)

        if existing.data:
            raise HTTPException(
                400,
                "Friend request already sent or pending"
            )

        result = (
            supabase.table("friend_requests")
            .insert({
                "from_user_id": user.id,
                "to_user_id": target_user_id,
                "status": "pending"
            })
            .execute()
        )

        print("INSERT:", result.data)

        request_id = result.data[0]["id"]

        notification = (
            supabase.table("notifications")
            .insert({
                "user_id": target_user_id,
                "type": "friend_request",
                "content": f"{user.id} sent you a friend request",
                "related_id": request_id
            })
            .execute()
        )

        print("NOTIFICATION:", notification.data)

        return {
            "message": "Friend request sent"
        }

    except Exception as e:
        print("ERROR:", repr(e))
        raise

@router.post("/accept/{request_id}")
async def accept_friend_request(
    request_id: int,
    user=Depends(get_current_user)
):
    req_res = (
        supabase.table("friend_requests")
        .select("*")
        .eq("id", request_id)
        .execute()
    )

    if not req_res.data:
        raise HTTPException(404, "Request not found")

    req = req_res.data[0]

    if req["to_user_id"] != user.id:
        raise HTTPException(403, "Not authorized")

    supabase.table("friend_requests") \
        .update({"status": "accepted"}) \
        .eq("id", request_id) \
        .execute()
    
    supabase.table("notifications").insert({
        "user_id": req["from_user_id"],
        "type": "friend_accepted",
        "content": f"{user.id} accepted your friend request",
        "related_id": request_id
    }).execute()

    return {
        "message": "Friend request accepted"
    }

@router.get("/requests")
async def get_pending_requests(user=Depends(get_current_user)):
    print("CURRENT USER:", user.id)
    res = (
        supabase.table("friend_requests")
        .select("id, from_user_id, created_at")
        .eq("to_user_id", user.id)
        .eq("status", "pending")
        .execute()
    )
    print("RAW DB RESULT:", res.data)

    requests = []

    for req in res.data:

        sender = (
            supabase.table("profiles")
            .select("id, username, xp")
            .eq("id", req["from_user_id"])
            .execute()
        )

        if sender.data:

            requests.append({
                "id": req["id"],
    
                "from_user": sender.data[0],
                "created_at": req["created_at"]
            })

    print("CURRENT USER:", user.id)
    print("REQUESTS:", requests)

    return requests

@router.get("/search")
async def search_users(
    q: str,
    limit: int = 10
):

    res = (
        supabase.table("profiles")
        .select("id, username, xp, rank")
        .ilike("username", f"%{q}%")
        .limit(limit)
        .execute()
    )

    return res.data

@router.get("/")
async def list_friends(user=Depends(get_current_user)):

    res = (
        supabase.table("friend_requests")
        .select("from_user_id, to_user_id")
        .eq("status", "accepted")
        .or_(
            f"from_user_id.eq.{user.id},to_user_id.eq.{user.id}"
        )
        .execute()
    )

    friend_ids = set()

    for row in res.data:

        if row["from_user_id"] == user.id:
            friend_ids.add(row["to_user_id"])
        else:
            friend_ids.add(row["from_user_id"])

    if not friend_ids:
        return []

    profiles = (
        supabase.table("profiles")
        .select(
            "id, username, xp, rank, last_active"
        )
        .in_("id", list(friend_ids))
        .execute()
    )

    return profiles.data