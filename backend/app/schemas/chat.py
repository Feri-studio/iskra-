from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from app.models.chat import ChatType
from app.schemas.message import MessageOut


class ChatCreate(BaseModel):
    title: Optional[str] = "Новый чат"
    type: ChatType = ChatType.normal


class ChatUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None


class ChatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    type: ChatType
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class ChatWithMessages(ChatOut):
    messages: List[MessageOut] = []
