from datetime import datetime, date
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import enum


class MemoryType(str, enum.Enum):
    fact = "fact"
    preference = "preference"
    skill = "skill"
    style = "style"
    other = "other"


class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    memory_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    memory_value: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[MemoryType] = mapped_column(Enum(MemoryType), default=MemoryType.fact, index=True)
    importance: Mapped[int] = mapped_column(Integer, default=5, index=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class PeriodType(str, enum.Enum):
    day = "day"
    week = "week"
    month = "month"
    year = "year"


class LearningLog(Base):
    __tablename__ = "learning_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    period_type: Mapped[PeriodType] = mapped_column(Enum(PeriodType), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
