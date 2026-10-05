from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.message import MessageRole


class MessageCreate(BaseModel):
    content: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    role: MessageRole
    content: str
    tokens_used: int
    created_at: datetime
