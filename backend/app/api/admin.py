"""
Админ-панель API (только для role=admin / is_unlimited owner).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.chat import Chat
from app.models.project import Project
from app.services.memory import memory_service

router = APIRouter()


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin and not user.is_unlimited:
        raise HTTPException(status_code=403, detail="Только для администратора")
    return user


class GrantUnlimitedRequest(BaseModel):
    user_id: int
    unlimited: bool = True
    daily_limit: Optional[int] = None


@router.get("/users")
def list_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id).all()
    return [
        {
            "id": u.id,
            "external_id": u.external_id,
            "username": u.username,
            "role": u.role.value if hasattr(u.role, "value") else u.role,
            "daily_limit": u.daily_limit,
            "is_unlimited": u.is_unlimited,
            "requests_today": u.requests_today,
        }
        for u in users
    ]


@router.post("/grant-unlimited")
def grant_unlimited(
    payload: GrantUnlimitedRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_unlimited = payload.unlimited
    if payload.daily_limit is not None:
        user.daily_limit = payload.daily_limit
    db.commit()
    return {
        "ok": True,
        "user_id": user.id,
        "is_unlimited": user.is_unlimited,
        "daily_limit": user.daily_limit,
    }


@router.get("/stats")
def stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return {
        "users": db.query(User).count(),
        "chats": db.query(Chat).count(),
        "projects": db.query(Project).count(),
        "memory_items": len(memory_service.get_important(limit=100)),
    }
