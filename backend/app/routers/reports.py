import re
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_personal, resolve_aluno
from app.core.tz import now_utc, today_local
from app.database import get_db
from app.models import ReportNote, User
from app.schemas.progress import NoteIn
from app.services.report_pdf import render_report_pdf
from app.services.reports import build_report

router = APIRouter(prefix="/reports", tags=["Relatórios"])


def _period(start: date | None, end: date | None) -> tuple[date, date]:
    end = end or today_local()
    start = start or end - timedelta(days=29)
    if start > end:
        raise HTTPException(400, "A data inicial deve ser anterior à final")
    if (end - start).days > 366:
        raise HTTPException(400, "O período máximo é de 1 ano")
    return start, end


@router.get("/aluno/{aluno_id}")
def report(aluno_id: int, start: date | None = None, end: date | None = None,
           db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    aluno = resolve_aluno(db, me, aluno_id)
    s, e = _period(start, end)
    return build_report(db, aluno, s, e)


@router.get("/aluno/{aluno_id}/pdf")
def report_pdf(aluno_id: int, start: date | None = None, end: date | None = None,
               db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    aluno = resolve_aluno(db, me, aluno_id)
    s, e = _period(start, end)
    pdf = render_report_pdf(build_report(db, aluno, s, e))
    slug = re.sub(r"[^a-z0-9]+", "-", aluno.name.lower()).strip("-") or "aluno"
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="relatorio-{slug}-{s}_{e}.pdf"'},
    )


@router.put("/aluno/{aluno_id}/note")
def save_note(aluno_id: int, data: NoteIn, db: Session = Depends(get_db), me: User = Depends(require_personal)):
    aluno = resolve_aluno(db, me, aluno_id)
    note = db.query(ReportNote).filter(ReportNote.aluno_id == aluno.id).first()
    if note:
        note.text, note.personal_id, note.updated_at = data.text.strip(), me.id, now_utc()
    else:
        db.add(ReportNote(aluno_id=aluno.id, personal_id=me.id, text=data.text.strip()))
    db.commit()
    return {"saved": True}
