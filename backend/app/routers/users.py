from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user, hash_password, require_personal
from app.database import get_db
from app.models import AccessLog, LinkRequest, Progress, ReportNote, Schedule, User, Workout, WorkoutSession
from app.models.user import ROLE_ALUNO, ROLE_PERSONAL
from app.routers.auth import create_user
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["Usuários"])


def _get_allowed(db: Session, me: User, user_id: int) -> User:
    target = db.get(User, user_id)
    allowed = target and (target.id == me.id or (me.role == ROLE_PERSONAL and target.personal_id == me.id))
    if not allowed:
        raise HTTPException(404, "Usuário não encontrado")
    return target


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    if me.role == ROLE_PERSONAL:
        return db.query(User).filter(User.personal_id == me.id).order_by(User.name).all()
    return [me]


@router.post("", response_model=UserOut, status_code=201)
def create_aluno(data: UserCreate, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    """O personal cadastra um aluno já vinculado (o aluno recebe a senha inicial por fora)."""
    return create_user(db, data, ROLE_ALUNO, personal_id=me.id)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    return _get_allowed(db, me, user_id)


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    target = _get_allowed(db, me, user_id)
    if data.name:
        target.name = data.name
    if data.goal is not None and target.role == ROLE_ALUNO:
        target.goal = data.goal
    if data.password:
        target.hashed_password = hash_password(data.password)
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    target = _get_allowed(db, me, user_id)
    if target.role != ROLE_ALUNO:
        raise HTTPException(400, "No MVP apenas contas de aluno podem ser removidas")
    for w in db.query(Workout).filter(Workout.aluno_id == target.id).all():
        db.delete(w)
    db.flush()
    db.query(Progress).filter(Progress.aluno_id == target.id).delete()
    db.query(WorkoutSession).filter(WorkoutSession.aluno_id == target.id).delete()
    db.query(AccessLog).filter(AccessLog.aluno_id == target.id).delete()
    db.query(Schedule).filter(Schedule.aluno_id == target.id).delete()
    db.query(ReportNote).filter(ReportNote.aluno_id == target.id).delete()
    db.query(LinkRequest).filter(LinkRequest.aluno_id == target.id).delete()
    db.delete(target)
    db.commit()
