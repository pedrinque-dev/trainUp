from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_aluno, resolve_aluno
from app.database import get_db
from app.models import Exercise, Progress, User
from app.schemas.progress import ProgressOut, SetBatch

router = APIRouter(prefix="/progress", tags=["Execução de treino"])


@router.post("", status_code=201)
def register_sets(data: SetBatch, db: Session = Depends(get_db), me: User = Depends(require_aluno)):
    """Registro avulso (em lote) de séries. O fluxo guiado usa /sessions."""
    for s in data.logs:
        if not db.get(Exercise, s.exercise_id):
            raise HTTPException(404, f"Exercício {s.exercise_id} não encontrado")
        db.add(Progress(aluno_id=me.id, **s.model_dump()))
    db.commit()
    return {"saved": len(data.logs)}


@router.get("", response_model=list[ProgressOut])
def list_progress(aluno_id: int | None = None, exercise_id: int | None = None, limit: int = 200,
                  db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    aluno = resolve_aluno(db, me, aluno_id)
    q = db.query(Progress).filter(Progress.aluno_id == aluno.id)
    if exercise_id:
        q = q.filter(Progress.exercise_id == exercise_id)
    return q.order_by(Progress.performed_at.desc()).limit(min(limit, 1000)).all()
