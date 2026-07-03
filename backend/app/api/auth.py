import uuid
import time
import logging
from collections import deque
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from app.models.db import a_create_user, a_get_user_by_username, a_update_password
from app.core.auth import hash_password, verify_password, create_token, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

_auth_rate_limit: dict[str, deque] = {}
_AUTH_RATE_LIMIT = 10


def _check_auth_rate_limit(client_ip: str):
    now = time.monotonic()
    bucket = _auth_rate_limit.get(client_ip)
    if bucket is None:
        bucket = deque()
        _auth_rate_limit[client_ip] = bucket
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= _AUTH_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
    bucket.append(now)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    token: str
    user_id: str
    username: str
    is_admin: bool


@router.post("/register")
async def register(req: RegisterRequest, fastapi_request: Request):
    _check_auth_rate_limit(fastapi_request.client.host if fastapi_request.client else "unknown")
    existing = await a_get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    user_id = str(uuid.uuid4())
    hashed = hash_password(req.password)
    await a_create_user(user_id, req.username, hashed)
    token = create_token(user_id, req.username)
    return AuthResponse(token=token, user_id=user_id, username=req.username, is_admin=False)


@router.post("/login")
async def login(req: LoginRequest, fastapi_request: Request):
    _check_auth_rate_limit(fastapi_request.client.host if fastapi_request.client else "unknown")
    user = await a_get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(user["id"], user["username"])
    return AuthResponse(token=token, user_id=user["id"], username=user["username"], is_admin=bool(user["is_admin"]))


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=4, max_length=128)


@router.post("/change-password")
async def change_password(req: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    db_user = await a_get_user_by_username(user["username"])
    if not db_user or not verify_password(req.current_password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    if verify_password(req.new_password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="New password must be different from current password")
    hashed = hash_password(req.new_password)
    await a_update_password(user["id"], hashed)
    return {"success": True, "message": "Password updated"}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["id"],
        "username": user["username"],
        "is_admin": bool(user["is_admin"]),
    }
