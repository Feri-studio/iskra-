"""
Сервис для работы с бесплатными LLM (Groq / OpenRouter и т.д.)
"""

from typing import List, Dict, Optional
import httpx
from app.core.config import get_settings

settings = get_settings()


SYSTEM_PROMPT = """Ты — Искра.

Характер: спокойная, профессиональная, чуть дерзкая и с лёгким юмором. Стиль общения можно менять по просьбе пользователя.

Ты умеешь:
- Создавать сайты, приложения, презентации
- Писать ботов: Telegram, VK, Max, Discord
- Делать моды, текстуры, ресурспаки и датапаки для Minecraft
- Создавать 2D-игры и текстовые игры
- Писать музыку и генерировать изображения (описывать промпты)
- Помогать с повседневными вопросами, учёбой, идеями заработка
- Глубоко работать с кодом на Python, Java, C++, JavaScript, TypeScript, Kotlin, HTML/CSS, Pascal, C#, SQL и других языках

Как ты работаешь:
- Почти автономно: сама предлагаешь варианты и улучшения прямо во время процесса
- Разбиваешь сложные задачи на шаги
- Спрашиваешь подтверждение перед большими изменениями
- В конце можешь собрать готовую папку/проект

Правила:
- Всегда отвечай на русском языке
- Будь полезной, конкретной и честной
- Если чего-то не знаешь — говори прямо
- При генерации кода сразу давай готовый рабочий вариант + краткие пояснения
"""


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Отправляет сообщения в LLM и возвращает ответ ассистента.
        messages: [{"role": "user"|"assistant"|"system", "content": "..."}]
        """
        if not self.api_key:
            return (
                "⚠️ LLM_API_KEY не задан.\n\n"
                "Добавь ключ в файл .env:\n"
                "1. Зайди на https://console.groq.com (бесплатно)\n"
                "2. Создай API Key\n"
                "3. В .env пропиши:\n"
                "   LLM_PROVIDER=groq\n"
                "   LLM_API_KEY=твой_ключ\n"
                "   LLM_MODEL=llama-3.3-70b-versatile\n\n"
                f"Пока я вижу твоё сообщение: «{messages[-1]['content'][:200] if messages else '...'}»"
            )

        full_messages = []
        sys = system_prompt or SYSTEM_PROMPT
        full_messages.append({"role": "system", "content": sys})
        full_messages.extend(messages)

        try:
            if self.provider == "groq":
                return await self._call_groq(full_messages)
            elif self.provider == "openrouter":
                return await self._call_openrouter(full_messages)
            else:
                return await self._call_openai_compatible(full_messages)
        except Exception as e:
            return f"Ошибка при обращении к модели ({self.provider}): {str(e)}"

    async def _call_groq(self, messages: List[Dict[str, str]]) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model or "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_openrouter(self, messages: List[Dict[str, str]]) -> str:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://iskra.app",
            "X-Title": "Iskra Agent",
        }
        payload = {
            "model": self.model or "qwen/qwen3-coder:free",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_openai_compatible(self, messages: List[Dict[str, str]]) -> str:
        base_url = getattr(settings, "LLM_BASE_URL", "https://api.groq.com/openai/v1")
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]


# Синглтон
llm_service = LLMService()
