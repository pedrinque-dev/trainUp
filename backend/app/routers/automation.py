from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_aluno, require_personal
from app.core.tz import day_bounds_utc
from app.database import get_db
from app.models import AccessLog, Schedule, Turnstile, User
from app.models.user import ROLE_PERSONAL
from app.schemas.progress import CheckinIn, SimulateIn, TurnstileRef
from app.services import turnstile as svc
from app.services.turnstile import Booking, InvalidTransition

router = APIRouter(prefix="/automacao", tags=["Catraca"])


def _turnstile(db: Session, turnstile_id: int | None, lock: bool = False) -> Turnstile:
    """Carrega a catraca. Com lock=True a linha é travada (SELECT ... FOR UPDATE no PostgreSQL) até o
    commit, serializando leituras simultâneas; no SQLite o lock é ignorado."""
    t = svc.get_turnstile(db, turnstile_id)
    if not t:
        raise HTTPException(404, "Catraca não encontrada")
    svc.refresh(db, t)  # pode commitar (timeouts), por isso o lock vem depois
    if lock:
        db.refresh(t, with_for_update=True)
    return t


@router.get("/turnstiles")
def turnstiles(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [{"id": t.id, "name": t.name, "location": t.location, "state": svc.refresh(db, t).state}
            for t in db.query(Turnstile).order_by(Turnstile.id).all()]


@router.get("/status")
def status(turnstile_id: int | None = None, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    t = _turnstile(db, turnstile_id)
    data = {"turnstile": svc.snapshot(t)}
    if me.role == ROLE_PERSONAL:
        data["stats"] = svc.stats_today(db, me.id, t.id)
    return data


@router.post("/checkin")
def checkin(data: CheckinIn, db: Session = Depends(get_db), me: User = Depends(require_aluno)):
    """Valida o agendamento e, se estiver na janela, libera a catraca (TRAVADA -> ... -> AGUARDANDO_PASSAGEM)."""
    t = _turnstile(db, data.turnstile_id, lock=True)
    sched = db.get(Schedule, data.schedule_id)
    booking = None
    if sched and sched.aluno_id == me.id:
        booking = Booking(start=sched.start_time, duration=sched.duration_min, status=sched.status, row=sched)
    return svc.run_cycle(db, t, me, booking, credential_label=f"aluno#{me.id} ({me.name})")


@router.post("/simulate")
def simulate(data: SimulateIn, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    """Simulador de sensores: dispara um cenário de teste sem depender de dados preparados."""
    t = _turnstile(db, data.turnstile_id, lock=True)
    q = db.query(User).filter(User.personal_id == me.id)
    aluno = q.filter(User.id == data.aluno_id).first() if data.aluno_id else q.order_by(User.id).first()
    if not aluno:
        raise HTTPException(400, "Cadastre ao menos um aluno para simular")
    return {"cycles": svc.simulate(db, t, data.scenario, aluno, me.id)}


@router.post("/passagem")
def passagem(data: TurnstileRef, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    t = _turnstile(db, data.turnstile_id, lock=True)
    if t.state == svc.AGUARDANDO:
        # só quem foi liberado (o aluno) ou o personal responsável por ele confirma a passagem
        if me.role == ROLE_PERSONAL:
            allowed = t.last_aluno_id is None or svc.personal_of(db, t.last_aluno_id) == me.id
        else:
            allowed = t.last_aluno_id == me.id
        if not allowed:
            raise HTTPException(403, "Esta liberação pertence a outro usuário")
    try:
        return svc.confirm_passage(db, t, me.id if me.role == ROLE_PERSONAL else None)
    except InvalidTransition as e:
        raise HTTPException(409, f"Sem passagem pendente ({e})")


@router.post("/reset")
def reset(data: TurnstileRef, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    t = _turnstile(db, data.turnstile_id, lock=True)
    try:
        return svc.reset(db, t, me.id)
    except InvalidTransition as e:
        raise HTTPException(409, str(e))


@router.get("/logs")
def logs(turnstile_id: int | None = None, result: str | None = None, event: str | None = None,
         day: date | None = None, limit: int = 50,
         db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    q = db.query(AccessLog)
    if me.role == ROLE_PERSONAL:
        q = q.filter(AccessLog.personal_id == me.id)
    else:
        q = q.filter(AccessLog.aluno_id == me.id)
    if turnstile_id:
        q = q.filter(AccessLog.turnstile_id == turnstile_id)
    if result == "permitido":
        q = q.filter(AccessLog.granted.is_(True))
    elif result == "negado":
        q = q.filter(AccessLog.granted.is_(False))
    if event:
        q = q.filter(AccessLog.event == event)
    if day:
        lo, hi = day_bounds_utc(day)
        q = q.filter(AccessLog.created_at >= lo, AccessLog.created_at < hi)
    return [
        {"id": l.id, "turnstile_id": l.turnstile_id, "aluno_id": l.aluno_id, "aluno_name": l.aluno_name,
         "schedule_id": l.schedule_id, "event": l.event, "granted": l.granted, "reason": l.reason,
         "scenario": l.scenario, "simulated": l.simulated, "cycle_ms": l.cycle_ms,
         "detail": l.detail if me.role == ROLE_PERSONAL else "", "created_at": l.created_at}
        for l in q.order_by(AccessLog.id.desc()).limit(min(limit, 200)).all()
    ]
