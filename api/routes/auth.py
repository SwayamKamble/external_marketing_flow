"""Authentication routes for Creative Manager."""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from contentforge.creative_manager.db import CreativeManagerDB

router = APIRouter(prefix="/creative/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


def _get_db() -> CreativeManagerDB:
    """Create a fresh DB instance per request to avoid cross-thread SQLite errors on Vercel."""
    db_path = "/tmp/creative_manager.db" if os.getenv("VERCEL") == "1" else "data/creative_manager.db"
    db = CreativeManagerDB(db_path=db_path)
    db.initialize()
    return db


# ── Password Hashing Helpers ──

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 100000
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${pw_hash.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        parts = hashed.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        stored_hash = parts[3]
        pw_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations
        )
        return secrets.compare_digest(pw_hash.hex(), stored_hash)
    except Exception:
        return False


# ── Dependency to Get Current User ──

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> str:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    db = _get_db()
    user_id = db.get_user_id_by_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


# ── Schemas ──

class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class AuthResponse(BaseModel):
    token: str
    username: str
    user_id: str


class UserMeResponse(BaseModel):
    user_id: str
    username: str


# ── Endpoints ──

@router.post("/signup", response_model=AuthResponse)
async def signup(req: AuthRequest):
    db = _get_db()
    username = req.username.strip().lower()
    
    # Check if user already exists
    existing = db.get_user_by_username(username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
        
    pw_hash = hash_password(req.password)
    user_id = db.create_user(username, pw_hash)
    
    # Generate session token
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    db.create_user_session(token, user_id, expires_at)
    
    return AuthResponse(token=token, username=username, user_id=user_id)


@router.post("/login", response_model=AuthResponse)
async def login(req: AuthRequest):
    db = _get_db()
    username = req.username.strip().lower()
    
    user = db.get_user_by_username(username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
        
    # Generate session token
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    db.create_user_session(token, user["id"], expires_at)
    
    return AuthResponse(token=token, username=username, user_id=user["id"])


@router.post("/logout")
async def logout(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    if credentials:
        token = credentials.credentials
        db = _get_db()
        db.delete_user_session(token)
    return {"status": "ok", "message": "Logged out successfully"}


@router.get("/me", response_model=UserMeResponse)
async def me(user_id: str = Depends(get_current_user)):
    db = _get_db()
    # Find user info using database-agnostic executor
    rows = db._execute("SELECT username FROM users WHERE id = ?", (user_id,), commit=False)
    if not rows:
        raise HTTPException(status_code=404, detail="User not found")
    return UserMeResponse(user_id=user_id, username=rows[0]["username"])
