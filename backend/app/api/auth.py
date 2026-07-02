import uuid
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.models.db import a_create_user, a_get_user_by_username, get_user_by_username
from app.core.auth import hash_password, verify_password, create_token, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


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
async def register(req: RegisterRequest):
    existing = await a_get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    user_id = str(uuid.uuid4())
    hashed = hash_password(req.password)
    await a_create_user(user_id, req.username, hashed)
    token = create_token(user_id, req.username)
    return AuthResponse(token=token, user_id=user_id, username=req.username, is_admin=False)


@router.post("/login")
async def login(req: LoginRequest):
    user = await a_get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(user["id"], user["username"])
    return AuthResponse(token=token, user_id=user["id"], username=user["username"], is_admin=bool(user["is_admin"]))


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["id"],
        "username": user["username"],
        "is_admin": bool(user["is_admin"]),
    }
