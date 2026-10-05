from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.models.chat import Chat, ChatType
from app.models.message import Message, MessageRole
from app.schemas.chat import ChatCreate, ChatOut, ChatUpdate, ChatWithMessages
from app.schemas.message import MessageCreate, MessageOut
from app.services.agent import agent_service
from app.services.memory import memory_service

router = APIRouter()


@router.post("/", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
def create_chat(payload: ChatCreate, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Обучающий и админ чаты — только для admin
    if payload.type in (ChatType.training, ChatType.admin) and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create this chat type")

    chat = Chat(
        user_id=user_id,
        title=payload.title or "Новый чат",
        type=payload.type,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/user/{user_id}", response_model=List[ChatOut])
def list_user_chats(user_id: int, db: Session = Depends(get_db)):
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == user_id, Chat.is_archived == False)
        .order_by(Chat.updated_at.desc())
        .all()
    )
    return chats


@router.get("/{chat_id}", response_model=ChatWithMessages)
def get_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.patch("/{chat_id}", response_model=ChatOut)
def update_chat(chat_id: int, payload: ChatUpdate, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if payload.title is not None:
        chat.title = payload.title
    if payload.is_archived is not None:
        chat.is_archived = payload.is_archived

    db.commit()
    db.refresh(chat)
    return chat


@router.post("/{chat_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(chat_id: int, payload: MessageCreate, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user = db.query(User).filter(User.id == chat.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверка лимита
    if not user.can_make_request():
        raise HTTPException(
            status_code=429,
            detail=f"Дневной лимит запросов исчерпан ({user.daily_limit}). Попробуйте завтра."
        )

    # Сохраняем сообщение пользователя
    user_msg = Message(
        chat_id=chat_id,
        role=MessageRole.user,
        content=payload.content,
    )
    db.add(user_msg)
    db.flush()

    # История для контекста
    history_rows = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(20)
        .all()
    )
    history_rows = list(reversed(history_rows))
    llm_messages = [
        {
            "role": m.role.value if hasattr(m.role, "value") else str(m.role),
            "content": m.content,
        }
        for m in history_rows
    ]

    # Обучающий чат → пишем в долгосрочную память
    if chat.type.value == "training" or chat.type == "training":
        memory_service.add(
            db=db,
            key=f"train_{chat_id}_{user_msg.id}",
            value=payload.content,
            memory_type="skill",
            importance=7,
            source="training",
        )

    # Агентный цикл (обычный чат / разработка / zip)
    try:
        result = await agent_service.handle_message(
            db=db,
            user=user,
            chat=chat,
            user_text=payload.content,
            history=llm_messages,
        )
        assistant_content = result.get("content", "")
        if result.get("files_written"):
            assistant_content += f"\n\n📁 Файлы: {', '.join(result['files_written'])}"
        if result.get("zip_ready") and result.get("project_id"):
            assistant_content += (
                f"\n\n⬇️ Скачать: /api/v1/projects/{result['project_id']}/download"
            )
    except Exception as e:
        assistant_content = f"Ошибка агента: {str(e)}"

    assistant_msg = Message(
        chat_id=chat_id,
        role=MessageRole.assistant,
        content=assistant_content,
        tokens_used=0,
    )
    db.add(assistant_msg)

    user.register_request()
    chat.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(assistant_msg)
    return assistant_msg


@router.get("/{chat_id}/messages", response_model=List[MessageOut])
def list_messages(chat_id: int, db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return messages
