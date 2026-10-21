from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tz import now_utc
from app.core.types import UTCDateTime
from app.database import Base


class ReportNote(Base):
    """Observação/recomendação do personal que entra no relatório do aluno."""

    __tablename__ = "report_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    personal_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
