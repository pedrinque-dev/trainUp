from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_aluno, require_personal
from app.core.tz import now_utc
from app.database import get_db
from app.models import LinkRequest, User
from app.models.link import ACEITO, CANCELADO, PENDENTE, RECUSADO
from app.routers.auth import find_personal_by_code
from app.schemas.user import LinkOut, LinkRequestIn, LinkRespondIn

router = APIRouter(prefix="/links", tags=["Vínculo aluno-personal"])


@router.post("/request", response_model=LinkOut, status_code=201)
def request_link(data: LinkRequestIn, db: Session = Depends(get_db), me: User = Depends(require_aluno)):
    if me.personal_id:
        raise HTTPException(400, "Você já está vinculado a um personal")
    personal = find_personal_by_code(db, data.invite_code)
    dup = db.query(LinkRequest).filter(
        LinkRequest.aluno_id == me.id, LinkRequest.personal_id == personal.id, LinkRequest.status == PENDENTE
    ).first()
    if dup:
        raise HTTPException(400, "Você já tem uma solicitação pendente para este personal")
    req = LinkRequest(aluno_id=me.id, personal_id=personal.id)
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("/mine", response_model=list[LinkOut])
def my_requests(db: Session = Depends(get_db), me: User = Depends(require_aluno)):
    return db.query(LinkRequest).filter(LinkRequest.aluno_id == me.id).order_by(LinkRequest.id.desc()).all()


@router.get("/pending", response_model=list[LinkOut])
def pending(db: Session = Depends(get_db), me: User = Depends(require_personal)):
    return db.query(LinkRequest).filter(
        LinkRequest.personal_id == me.id, LinkRequest.status == PENDENTE
    ).order_by(LinkRequest.id).all()


@router.post("/{link_id}/respond", response_model=LinkOut)
def respond(link_id: int, data: LinkRespondIn, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    req = db.get(LinkRequest, link_id)
    if not req or req.personal_id != me.id:
        raise HTTPException(404, "Solicitação não encontrada")
    if req.status != PENDENTE:
        raise HTTPException(409, "Solicitação já respondida")
    if data.accept:
        aluno = db.get(User, req.aluno_id)
        if aluno.personal_id and aluno.personal_id != me.id:
            raise HTTPException(409, "O aluno já está vinculado a outro personal")
        aluno.personal_id = me.id
        req.status = ACEITO
        for other in db.query(LinkRequest).filter(
            LinkRequest.aluno_id == aluno.id, LinkRequest.status == PENDENTE, LinkRequest.id != req.id
        ):
            other.status = CANCELADO
    else:
        req.status = RECUSADO
    req.responded_at = now_utc()
    db.commit()
    db.refresh(req)
    return req
