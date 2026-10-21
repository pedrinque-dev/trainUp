from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user, resolve_aluno
from app.database import get_db
from app.models import Schedule, User
from app.models.schedule import AGENDADO, CANCELADO, CHECKIN, CONCLUIDO
from app.models.user import ROLE_ALUNO, ROLE_PERSONAL
from app.schemas.schedule import ScheduleIn, ScheduleOut, ScheduleStatusIn

router = APIRouter(prefix="/schedules", tags=["Agendamentos"])

# Transições válidas. CHECKIN só é alcançado pela catraca (/automacao/checkin).
TRANSITIONS = {AGENDADO: {CHECKIN, CANCELADO}, CHECKIN: {CONCLUIDO}, CONCLUIDO: set(), CANCELADO: set()}


def _conflict(db: Session, personal_id: int, start: datetime, minutes: int) -> bool:
    end = start + timedelta(minutes=minutes)
    active = db.query(Schedule).filter(
        Schedule.personal_id == personal_id, Schedule.status.in_([AGENDADO, CHECKIN])
    )
    return any(start < s.start_time + timedelta(minutes=s.duration_min) and s.start_time < end for s in active)


def _get(db: Session, me: User, schedule_id: int) -> Schedule:
    s = db.get(Schedule, schedule_id)
    if not s or me.id not in (s.aluno_id, s.personal_id):
        raise HTTPException(404, "Agendamento não encontrado")
    return s


@router.post("", response_model=ScheduleOut, status_code=201)
def create_schedule(data: ScheduleIn, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    aluno = resolve_aluno(db, me, data.aluno_id)
    personal_id = me.id if me.role == ROLE_PERSONAL else aluno.personal_id
    if personal_id is None:
        raise HTTPException(400, "Vincule-se a um personal antes de agendar")
    start = data.start_time if data.start_time.tzinfo else data.start_time.replace(tzinfo=timezone.utc)
    if start < datetime.now(timezone.utc) - timedelta(minutes=5):
        raise HTTPException(400, "Escolha um horário futuro")
    if _conflict(db, personal_id, start, data.duration_min):
        raise HTTPException(409, "Horário indisponível para este personal")
    s = Schedule(personal_id=personal_id, aluno_id=aluno.id, start_time=start, duration_min=data.duration_min)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("", response_model=list[ScheduleOut])
def list_schedules(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    col = Schedule.personal_id if me.role == ROLE_PERSONAL else Schedule.aluno_id
    return db.query(Schedule).filter(col == me.id).order_by(Schedule.start_time).all()


@router.patch("/{schedule_id}/status", response_model=ScheduleOut)
def update_status(schedule_id: int, data: ScheduleStatusIn, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    s = _get(db, me, schedule_id)
    if me.role == ROLE_ALUNO and data.status != CANCELADO:
        raise HTTPException(403, "O aluno só pode cancelar a própria aula")
    if data.status not in TRANSITIONS[s.status]:
        raise HTTPException(409, f"Transição inválida: {s.status} → {data.status}")
    s.status = data.status
    db.commit()
    db.refresh(s)
    return s
