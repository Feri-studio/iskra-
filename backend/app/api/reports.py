from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.api.admin import require_admin
from app.models.user import User
from app.services.reports import reports_service

router = APIRouter()


@router.post("/generate")
async def generate_report(
    period: str = "day",
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Сгенерировать отчёт (day/week/month/year). Только админ."""
    if period not in ("day", "week", "month", "year"):
        raise HTTPException(status_code=400, detail="period: day|week|month|year")
    log = await reports_service.generate(db, period_type=period)
    return {
        "id": log.id,
        "period_type": log.period_type.value,
        "period_start": str(log.period_start),
        "period_end": str(log.period_end),
        "content": log.content,
        "is_sent": log.is_sent,
    }


@router.get("/")
def list_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logs = reports_service.list_reports(db)
    return [
        {
            "id": l.id,
            "period_type": l.period_type.value,
            "period_start": str(l.period_start),
            "period_end": str(l.period_end),
            "content": l.content,
            "is_sent": l.is_sent,
            "created_at": str(l.created_at),
        }
        for l in logs
    ]
