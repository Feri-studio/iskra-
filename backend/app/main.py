from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import init_db
from app.api import users, chats, auth, projects, memory, admin, reports

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ИИ-агент Искра — backend (SQLite + Caliby)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(chats.router, prefix="/api/v1/chats", tags=["chats"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])


@app.on_event("startup")
def on_startup():
    init_db()
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} — SQLite + Caliby")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ok",
        "message": "Искра проснулась",
        "storage": "SQLite + Caliby",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
