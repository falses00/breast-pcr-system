"""系统管理员用户管理接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.services.auth import hash_password, require_roles


router = APIRouter(prefix="/admin/users", tags=["用户管理"])


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": user.role,
        "department": user.department,
        "is_active": user.is_active,
    }


@router.get("")
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_roles("系统管理员"))):
    return [user_payload(u) for u in db.query(User).order_by(User.id.asc()).all()]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require_roles("系统管理员"))):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="用户名已存在")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
        department=payload.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_payload(user)


@router.patch("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), admin: User = Depends(require_roles("系统管理员"))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.password_hash = hash_password(data.pop("password"))
    for key, value in data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user_payload(user)
