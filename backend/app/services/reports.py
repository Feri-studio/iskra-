"""
Автономные отчёты Искры: день / неделя / месяц / год.
Можно вызывать вручную или по cron / фоновой задаче.
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.memory import LearningLog, PeriodType
from app.models.message import Message, MessageRole
from app.services.llm import llm_service
from app.services.memory import memory_service


class ReportsService:
    async def generate(
        self,
        db: Session,
        period_type: str = "day",
    ) -> LearningLog:
        today = date.today()
        if period_type == "day":
            start, end = today, today
            label = "день"
        elif period_type == "week":
            start = today - timedelta(days=today.weekday())
            end = today
            label = "неделю"
        elif period_type == "month":
            start = today.replace(day=1)
            end = today
            label = "месяц"
        else:  # year
            start = today.replace(month=1, day=1)
            end = today
            label = "год"

        # Собираем контекст: важные воспоминания + последние сообщения ассистента
        memories = memory_service.get_important(limit=20)
        mem_text = "\n".join(
            f"- {m.memory_key}: {m.memory_value[:200]}" for m in memories
        ) or "Пока мало данных в памяти."

        recent = (
            db.query(Message)
            .filter(Message.role == MessageRole.assistant)
            .order_by(Message.created_at.desc())
            .limit(30)
            .all()
        )
        recent_text = "\n".join(m.content[:150] for m in reversed(recent)) or "Мало активности."

        prompt = f"""Составь краткий отчёт Искры о том, чему она «научилась» / что делала за {label}
({start} — {end}).

Память:
{mem_text}

Недавние ответы:
{recent_text[:2000]}

Формат отчёта:
1. Краткое резюме (2–3 предложения)
2. Что получилось лучше всего
3. Над чем стоит поработать
4. План на следующий период

Пиши от первого лица как Искра, на русском, спокойно и по делу.
"""

        content = await llm_service.chat(
            [{"role": "user", "content": prompt}],
            system_prompt="Ты — Искра. Пишешь честный отчёт о своём развитии.",
        )

        try:
            ptype = PeriodType(period_type)
        except ValueError:
            ptype = PeriodType.day

        log = LearningLog(
            period_type=ptype,
            period_start=start,
            period_end=end,
            content=content,
            is_sent=False,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def list_reports(self, db: Session, limit: int = 20):
        return (
            db.query(LearningLog)
            .order_by(LearningLog.created_at.desc())
            .limit(limit)
            .all()
        )


reports_service = ReportsService()
