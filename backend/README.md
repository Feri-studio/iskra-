# Искра Backend

**БД:** SQLite (структура) + **Caliby** (память агента)

## Установка
```bash
pip install -r requirements.txt
pip install caliby          # векторная память
# опционально: pip install sentence-transformers
```

## .env
```
DATABASE_URL=sqlite:///./data/iskra.db
CALIBY_PATH=./data/caliby_db
SECRET_KEY=длинный-секрет
LLM_PROVIDER=groq
LLM_API_KEY=ключ
LLM_MODEL=llama-3.3-70b-versatile
```

## Запуск
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

При старте автоматически создаётся SQLite-схема.  
Caliby откроется в `./data/caliby_db`. Если пакета нет — память на JSON.

## API
См. http://localhost:8000/docs
