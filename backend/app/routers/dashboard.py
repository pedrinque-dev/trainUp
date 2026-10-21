from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_personal
from app.core.tz import day_bounds_utc, now_utc, today_local
from app.database import get_db
from app.models import LinkRequest, Schedule, User
from app.models.link import PENDENTE
from app.models.schedule import AGENDADO, CANCELADO, CHECKIN
from app.schemas.schedule import ScheduleOut
from app.services import analytics

router = APIRouter(prefix="/dashboard", tags=["Painel"])


@router.get("/personal")
def personal_overview(db: Session = Depends(get_db), me: User = Depends(require_personal)):
    alunos = db.query(User).filter(User.personal_id == me.id).all()
    lo, hi = day_bounds_utc(today_local())
    today = db.query(Schedule).filter(
        Schedule.personal_id == me.id, Schedule.start_time >= lo, Schedule.start_time < hi,
        Schedule.status != CANCELADO,
    ).order_by(Schedule.start_time).all()
    now = now_utc()
    upcoming = [s for s in db.query(Schedule).filter(
        Schedule.personal_id == me.id, Schedule.status.in_([AGENDADO, CHECKIN]), Schedule.start_time >= now - timedelta(hours=1)
    ).order_by(Schedule.start_time).limit(6)]
    alerts = [a for al in alunos for a in analytics.stagnation(db, al, settings.STAGNATION_N)]
    pending = db.query(LinkRequest).filter(LinkRequest.personal_id == me.id, LinkRequest.status == PENDENTE).count()
    return {
        "alunos_ativos": len(alunos),
        "aulas_hoje": len(today),
        "alertas": len(alerts),
        "pendentes": pending,
        "alertas_lista": sorted(alerts, key=lambda a: -a["sessions"])[:5],
        "proximas": [ScheduleOut.model_validate(s) for s in upcoming],
    }
