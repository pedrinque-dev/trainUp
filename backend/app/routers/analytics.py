from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user, resolve_aluno
from app.database import get_db
from app.models import User
from app.models.user import ROLE_PERSONAL
from app.services import analytics

router = APIRouter(prefix="/analytics", tags=["Ciência de dados"])


@router.get("/evolution")
def evolution(aluno_id: int | None = None, exercise_id: int | None = None,
              db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    """Média e progressão de carga por exercício ao longo do tempo."""
    aluno = resolve_aluno(db, me, aluno_id)
    return analytics.evolution(db, aluno.id, exercise_id)


@router.get("/stagnation")
def stagnation(aluno_id: int | None = None, n: int = settings.STAGNATION_N,
               db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    """Alertas de estagnação. Personal sem aluno_id recebe os alertas de todos os seus alunos."""
    if me.role == ROLE_PERSONAL and aluno_id is None:
        alunos = db.query(User).filter(User.personal_id == me.id).all()
    else:
        alunos = [resolve_aluno(db, me, aluno_id)]
    return [a for aluno in alunos for a in analytics.stagnation(db, aluno, max(2, n))]


@router.get("/tips")
def tips(aluno_id: int | None = None, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    """Dicas educativas gerais de nutrição e recuperação (não é prescrição)."""
    aluno = resolve_aluno(db, me, aluno_id)
    return analytics.tips(aluno.goal)
