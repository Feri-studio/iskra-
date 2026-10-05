from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.api.auth import get_current_user
from app.models.user import User
from app.services.memory import memory_service

router = APIRouter()


class MemoryCreate(BaseModel):
    key: str
    value: str
    memory_type: str = "fact"
    importance: int = 5


class MemoryOut(BaseModel):
    key: str
    value: str
    memory_type: str
    importance: int
    source: Optional[str] = None


@router.post("/", response_model=MemoryOut)
def add_memory(payload: MemoryCreate, current_user: User = Depends(get_current_user)):
    entry = memory_service.add(
        key=payload.key,
        value=payload.value,
        memory_type=payload.memory_type,
        importance=payload.importance,
        source=f"user:{current_user.id}",
    )
    return MemoryOut(
        key=entry["key"],
        value=entry["value"],
        memory_type=entry.get("memory_type", "fact"),
        importance=entry.get("importance", 5),
        source=entry.get("source"),
    )


@router.get("/", response_model=List[MemoryOut])
def list_memory(current_user: User = Depends(get_current_user)):
    items = memory_service.get_important(limit=50)
    return [
        MemoryOut(
            key=m.get("key", ""),
            value=str(m.get("value", "")),
            memory_type=m.get("memory_type", "fact"),
            importance=int(m.get("importance", 5)),
            source=m.get("source"),
        )
        for m in items
    ]


@router.get("/search")
def search_memory(q: str, current_user: User = Depends(get_current_user)):
    items = memory_service.search(q, limit=10)
    return [
        {
            "key": m.get("key", ""),
            "value": m.get("value", ""),
            "type": m.get("memory_type", "fact"),
            "importance": m.get("importance", 5),
            "score": m.get("score"),
        }
        for m in items
    ]
