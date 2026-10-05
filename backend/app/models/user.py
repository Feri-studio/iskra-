from datetime import date, datetime
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user, index=True)
    daily_limit: Mapped[int] = mapped_column(Integer, default=100)
    is_unlimited: Mapped[bool] = mapped_column(Boolean, default=False)
    requests_today: Mapped[int] = mapped_column(Integer, default=0)
    last_request_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

    def can_make_request(self) -> bool:
        """Проверяет, может ли пользователь сделать запрос сегодня."""
        if self.is_unlimited or self.role == UserRole.admin:
            return True
        today = date.today()
        if self.last_request_date != today:
            return True
        return self.requests_today < self.daily_limit

    def register_request(self) -> None:
        """Увеличивает счётчик запросов за сегодня."""
        today = date.today()
        if self.last_request_date != today:
            self.requests_today = 1
            self.last_request_date = today
        else:
            self.requests_today += 1
