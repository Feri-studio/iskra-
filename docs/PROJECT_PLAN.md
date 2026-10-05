# Искра — План

**Хранилище (актуально):**
- **SQLite** — пользователи, чаты, сообщения, проекты, лимиты
- **Caliby** — долгосрочная векторная память агента (hybrid search)
- Без Supabase, без TiDB

## Стек
- Android: Kotlin + Compose
- Backend: FastAPI
- Structured DB: SQLite
- Agent memory: Caliby (fallback JSON)
- LLM: Groq / OpenRouter

## Готово
- [x] Auth, лимиты, чаты
- [x] LLM + агентный режим разработки + zip
- [x] Память на Caliby
- [x] Admin API, отчёты
- [x] Android: чаты + проекты

## Запуск backend
```bash
cd backend
pip install -r requirements.txt
pip install caliby   # опционально, для векторной памяти
# .env: LLM_API_KEY, SECRET_KEY
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Данные появятся в `./data/iskra.db` и `./data/caliby_db/`
