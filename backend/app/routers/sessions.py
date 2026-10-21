from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_aluno, resolve_aluno
from app.core.tz import now_utc
from app.database import get_db
from app.models import Exercise, Progress, User, Workout, WorkoutSession
from app.schemas.progress import SessionOut, SessionStartIn, SetBatch
from app.services.sessions import session_summary

router = APIRouter(prefix="/sessions", tags=["Sessões de treino"])


def _own_session(db: Session, me: User, session_id: int) -> WorkoutSession:
    s = db.get(WorkoutSession, session_id)
    if not s or s.aluno_id != me.id:
        raise HTTPException(404, "Sessão não encontrada")
    return s


@router.post("", response_model=SessionOut, status_code=201)
def start_session(data: SessionStartIn, db: Session = Depends(get_db), me: User = Depends(require_aluno)):
    if data.workout_id:
        w = db.get(Workout, data.workout_id)
        if not w or w.aluno_id != me.id:
            raise HTTPException(404, "Treino não encontrado")
    s = WorkoutSession(aluno_id=me.id, workout_id=data.workout_id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.post("/{session_id}/sets", status_code=201)
def add_sets(session_id: int, data: SetBatch, db: Session = Depends(get_db), me: User = Depends(require_aluno)):
    s = _own_session(db, me, session_id)
    if s.finished_at:
        raise HTTPException(409, "Sessão já finalizada")
    for item in data.logs:
        if not db.get(Exercise, item.exercise_id):
            raise HTTPException(404, f"Exercício {item.exercise_id} não encontrado")
        db.add(Progress(
            aluno_id=me.id, session_id=s.id, workout_id=s.workout_id, exercise_id=item.exercise_id,
            set_number=item.set_number, reps=item.reps, load_kg=item.load_kg,
        ))
    db.commit()
    return {"saved": len(data.logs)}


@router.post("/{session_id}/finish")
def finish_session(session_id: int, db: Session = Depends(get_db), me: User = Depends(require_aluno)):
    s = _own_session(db, me, session_id)
    if not s.finished_at:
        s.finished_at = now_utc()
        db.commit()
    return session_summary(db, s)


@router.get("/{session_id}/summary")
def summary(session_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    s = db.get(WorkoutSession, session_id)
    if not s:
        raise HTTPException(404, "Sessão não encontrada")
    resolve_aluno(db, me, s.aluno_id)  # aluno dono ou personal vinculado
    return session_summary(db, s)


@router.get("", response_model=list[SessionOut])
def list_sessions(aluno_id: int | None = None, limit: int = 30, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    aluno = resolve_aluno(db, me, aluno_id)
    return (db.query(WorkoutSession).filter(WorkoutSession.aluno_id == aluno.id)
            .order_by(WorkoutSession.started_at.desc()).limit(min(limit, 200)).all())
