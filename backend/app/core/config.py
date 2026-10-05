from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Искра"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = True

    # SQLite — пользователи, чаты, проекты (без сервера)
    DATABASE_URL: str = "sqlite:///./data/iskra.db"

    # Caliby — векторная память агента
    CALIBY_PATH: str = "./data/caliby_db"
    CALIBY_BUFFER_GB: float = 0.5
    CALIBY_VECTOR_DIM: int = 384

    SECRET_KEY: str = "change-me-in-production-please-very-long-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    DEFAULT_DAILY_LIMIT: int = 100

    LLM_PROVIDER: str = "groq"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_BASE_URL: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
