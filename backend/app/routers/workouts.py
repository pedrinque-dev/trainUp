from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_personal, resolve_aluno
from app.database import get_db
from app.models import Exercise, User, Workout, WorkoutItem
from app.models.user import ROLE_PERSONAL
from app.schemas.workout import ExerciseIn, ExerciseOut, WorkoutIn, WorkoutItemIn, WorkoutOut

router = APIRouter(tags=["Treinos"])


# ---------- Exercícios (catálogo base + biblioteca do personal) ----------
def _owner_scope(user: User) -> int | None:
    return user.id if user.role == ROLE_PERSONAL else user.personal_id


def _visible(db: Session, user: User):
    owner = _owner_scope(user)
    cond = Exercise.owner_id.is_(None) if owner is None else or_(Exercise.owner_id.is_(None), Exercise.owner_id == owner)
    return db.query(Exercise).filter(cond)


@router.get("/exercises", response_model=list[ExerciseOut])
def list_exercises(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    return _visible(db, me).order_by(Exercise.muscle_group, Exercise.name).all()


@router.post("/exercises", response_model=ExerciseOut, status_code=201)
def create_exercise(data: ExerciseIn, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    if any(e.name.lower() == data.name.strip().lower() for e in _visible(db, me).all()):
        raise HTTPException(400, "Já existe um exercício com esse nome na sua biblioteca")
    ex = Exercise(**data.model_dump(), owner_id=me.id)
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex


def _own_exercise(db: Session, me: User, ex_id: int) -> Exercise:
    ex = db.get(Exercise, ex_id)
    if not ex:
        raise HTTPException(404, "Exercício não encontrado")
    if ex.owner_id is None:
        raise HTTPException(403, "O catálogo base é somente leitura")
    if ex.owner_id != me.id:
        raise HTTPException(404, "Exercício não encontrado")
    return ex


@router.put("/exercises/{ex_id}", response_model=ExerciseOut)
def update_exercise(ex_id: int, data: ExerciseIn, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    ex = _own_exercise(db, me, ex_id)
    for k, v in data.model_dump().items():
        setattr(ex, k, v)
    db.commit()
    db.refresh(ex)
    return ex


@router.delete("/exercises/{ex_id}", status_code=204)
def delete_exercise(ex_id: int, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    ex = _own_exercise(db, me, ex_id)
    try:
        db.delete(ex)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Exercício em uso por fichas ou históricos")


# ---------- Fichas de treino ----------
def _items(db: Session, me: User, items: list[WorkoutItemIn]) -> list[WorkoutItem]:
    ids = {e.id for e in _visible(db, me).all()}
    for i in items:
        if i.exercise_id not in ids:
            raise HTTPException(404, f"Exercício {i.exercise_id} não encontrado na sua biblioteca")
    return [WorkoutItem(**i.model_dump()) for i in items]


def _get_workout(db: Session, user: User, workout_id: int) -> Workout:
    w = db.get(Workout, workout_id)
    if not w or user.id not in (w.personal_id, w.aluno_id):
        raise HTTPException(404, "Treino não encontrado")
    return w


@router.post("/workouts", response_model=WorkoutOut, status_code=201)
def create_workout(data: WorkoutIn, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    aluno = resolve_aluno(db, me, data.aluno_id)
    w = Workout(name=data.name, personal_id=me.id, aluno_id=aluno.id, weekday=data.weekday,
                items=_items(db, me, data.items))
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


@router.get("/workouts", response_model=list[WorkoutOut])
def list_workouts(aluno_id: int | None = None, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    q = db.query(Workout)
    if me.role == ROLE_PERSONAL:
        q = q.filter(Workout.personal_id == me.id)
        if aluno_id:
            q = q.filter(Workout.aluno_id == aluno_id)
    else:
        q = q.filter(Workout.aluno_id == me.id)
    return q.order_by(Workout.id.desc()).all()


@router.get("/workouts/today", response_model=list[WorkoutOut])
def workouts_today(weekday: int | None = None, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    """Treino do dia (weekday 0=segunda). Ficha sem dia definido vale para qualquer dia."""
    wd = weekday if weekday is not None else datetime.now(timezone.utc).weekday()
    ws = db.query(Workout).filter(Workout.aluno_id == me.id).order_by(Workout.id).all()
    return [w for w in ws if w.weekday == wd] or [w for w in ws if w.weekday is None]


@router.get("/workouts/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    return _get_workout(db, me, workout_id)


@router.put("/workouts/{workout_id}", response_model=WorkoutOut)
def update_workout(workout_id: int, data: WorkoutIn, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    w = _get_workout(db, me, workout_id)
    if w.personal_id != me.id:
        raise HTTPException(404, "Treino não encontrado")
    w.name, w.weekday = data.name, data.weekday
    w.items.clear()
    w.items.extend(_items(db, me, data.items))
    db.commit()
    db.refresh(w)
    return w


@router.delete("/workouts/{workout_id}", status_code=204)
def delete_workout(workout_id: int, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    w = _get_workout(db, me, workout_id)
    if w.personal_id != me.id:
        raise HTTPException(404, "Treino não encontrado")
    db.delete(w)
    db.commit()
