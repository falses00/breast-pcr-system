"""认证接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest
from app.services.auth import create_token, get_current_user, verify_password


router = APIRouter(prefix="/auth", tags=["认证"])


def user_payload(user: User) -> dict:
    return {"id": user.id, "username": user.username, "name": user.name, "role": user.role, "department": user.department}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"access_token": create_token(user), "token_type": "bearer", "user": user_payload(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_payload(user)
