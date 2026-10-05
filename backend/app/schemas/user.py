from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    username: Optional[str] = None
    external_id: Optional[str] = None


class UserCreate(UserBase):
    external_id: str
    username: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    daily_limit: Optional[int] = None
    is_unlimited: Optional[bool] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    daily_limit: int
    is_unlimited: bool
    requests_today: int
    last_request_date: Optional[date] = None
    created_at: datetime
