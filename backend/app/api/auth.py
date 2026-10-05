"""
Простая авторизация по external_id + выдача токена.
Пока без JWT-сложности: токен = base64(user_id:external_id:secret_hash)
Для MVP достаточно. Потом легко заменить на настоящий JWT.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import hashlib
import base64
from app.core.database import get_db
from app.core.config import get_settings
from app.models.user import User, UserRole
from app.schemas.user import UserOut

router = APIRouter()
settings = get_settings()


class LoginRequest(BaseModel):
    external_id: str
    username: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def _make_token(user_id: int, external_id: str) -> str:
    raw = f"{user_id}:{external_id}:{settings.SECRET_KEY}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    token_str = f"{user_id}:{external_id}:{digest}"
    return base64.urlsafe_b64encode(token_str.encode()).decode()


def _parse_token(token: str) -> tuple[int, str]:
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        parts = decoded.split(":")
        if len(parts) != 3:
            raise ValueError("bad format")
        user_id = int(parts[0])
        external_id = parts[1]
        # Проверяем подпись
        expected = _make_token(user_id, external_id)
        if token != expected:
            raise ValueError("invalid signature")
        return user_id, external_id
    except Exception:
        raise HTTPException(status_code=401, detail="Неверный или просроченный токен")


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    token = authorization.replace("Bearer ", "").strip()
    user_id, _ = _parse_token(token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Войти или зарегистрироваться по external_id.
    Возвращает токен + данные пользователя.
    """
    user = db.query(User).filter(User.external_id == payload.external_id).first()
    if not user:
        # Первый вход — создаём
        is_owner = payload.external_id == "owner"
        user = User(
            external_id=payload.external_id,
            username=payload.username or payload.external_id,
            role=UserRole.admin if is_owner else UserRole.user,
            daily_limit=999999 if is_owner else 100,
            is_unlimited=is_owner,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = _make_token(user.id, user.external_id or "")
    return LoginResponse(access_token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
