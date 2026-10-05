"""
Агентный цикл Искры.
- Обычный чат
- Режим разработки: создаёт проект, пишет файлы по шагам, предлагает изменения, собирает zip
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import json
import re

from app.services.llm import llm_service, SYSTEM_PROMPT
from app.services.memory import memory_service
from app.services.projects import project_service
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message, MessageRole
from app.models.project import Project, ProjectStatus


DEV_KEYWORDS = [
    "создай", "сделай", "напиши", "сгенерируй", "разработай",
    "сайт", "бот", "приложение", "мод", "игру", "презентац",
    "скрипт", "api", "telegram", "discord", "minecraft",
    "create", "make", "build", "generate", "code",
]


class AgentService:
    def is_dev_request(self, text: str) -> bool:
        t = text.lower()
        return any(k in t for k in DEV_KEYWORDS)

    async def handle_message(
        self,
        db: Session,
        user: User,
        chat: Chat,
        user_text: str,
        history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Главная точка входа.
        Возвращает: {content, project_id?, files_written?, zip_ready?}
        """
        memory_block = memory_service.build_context_block(query=user_text, limit=8)
        system = SYSTEM_PROMPT
        if memory_block:
            system += "\n\n" + memory_block

        # Режим разработки
        if self.is_dev_request(user_text) or self._has_active_project(db, chat.id):
            return await self._dev_mode(db, user, chat, user_text, history, system)

        # Обычный ответ
        content = await llm_service.chat(history, system_prompt=system)
        return {"content": content}

    def _has_active_project(self, db: Session, chat_id: int) -> bool:
        return (
            db.query(Project)
            .filter(
                Project.chat_id == chat_id,
                Project.status.in_([ProjectStatus.draft, ProjectStatus.in_progress]),
            )
            .first()
            is not None
        )

    async def _dev_mode(
        self,
        db: Session,
        user: User,
        chat: Chat,
        user_text: str,
        history: List[Dict[str, str]],
        system: str,
    ) -> Dict[str, Any]:
        """
        Пошаговая генерация:
        1. Если нет проекта — создаём
        2. Просим LLM вернуть JSON с файлами + пояснением
        3. Пишем файлы
        4. Предлагаем изменения / собрать zip
        """
        project = (
            db.query(Project)
            .filter(
                Project.chat_id == chat.id,
                Project.status.in_([ProjectStatus.draft, ProjectStatus.in_progress]),
            )
            .order_by(Project.id.desc())
            .first()
        )

        if not project:
            title = self._extract_title(user_text)
            project = project_service.create_project(
                db=db,
                user=user,
                title=title,
                description=user_text[:500],
                chat_id=chat.id,
            )

        existing_files = project_service.list_files(project.id)

        dev_system = system + f"""

## Режим разработки (активен)
Текущий проект id={project.id}, название: «{project.title}».
Уже есть файлы: {existing_files or 'пока пусто'}.

Когда генерируешь код, отвечай СТРОГО в таком формате (можно добавить текст до/после):

<<<FILES>>>
{{
  "path/to/file1.py": "содержимое файла 1",
  "path/to/file2.html": "содержимое файла 2"
}}
<<<END_FILES>>>

Потом обычным текстом:
- Кратко что сделал
- Что можно изменить
- Спроси: «Собрать zip?» или предложи следующий шаг

Если пользователь просит собрать/скачать — напиши: <<<BUILD_ZIP>>>
"""

        content = await llm_service.chat(history, system_prompt=dev_system)

        files = self._extract_files(content)
        files_written = []
        if files:
            project_service.write_files(project.id, files)
            files_written = list(files.keys())

        zip_ready = False
        if "<<<BUILD_ZIP>>>" in content or any(
            w in user_text.lower() for w in ["собери", "zip", "скачать", "архив", "build"]
        ):
            try:
                project_service.build_zip(db, project.id)
                zip_ready = True
                content = content.replace("<<<BUILD_ZIP>>>", "")
                content += f"\n\n✅ Архив проекта «{project.title}» готов. Можешь скачать (project_id={project.id})."
            except Exception as e:
                content += f"\n\n⚠️ Не удалось собрать zip: {e}"

        # Убираем служебные блоки из ответа пользователю
        clean = re.sub(
            r"<<<FILES>>>.*?<<<END_FILES>>>",
            f"\n📎 Записано файлов: {len(files_written)}\n" if files_written else "",
            content,
            flags=re.DOTALL,
        )
        clean = clean.replace("<<<BUILD_ZIP>>>", "").strip()

        return {
            "content": clean,
            "project_id": project.id,
            "files_written": files_written,
            "zip_ready": zip_ready,
        }

    def _extract_title(self, text: str) -> str:
        text = text.strip()
        if len(text) > 60:
            return text[:57] + "..."
        return text or "Новый проект"

    def _extract_files(self, content: str) -> Dict[str, str]:
        match = re.search(r"<<<FILES>>>\s*(\{.*?\})\s*<<<END_FILES>>>", content, re.DOTALL)
        if not match:
            # Попробуем найти просто JSON-блок с путями
            match2 = re.search(r'\{[^{}]*"[^"]+\.[a-zA-Z0-9]+"[^{}]*\}', content, re.DOTALL)
            if not match2:
                return {}
            raw = match2.group(0)
        else:
            raw = match.group(1)

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except json.JSONDecodeError:
            pass
        return {}


agent_service = AgentService()
