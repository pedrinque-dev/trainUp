from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.tz import now_utc
from app.core.types import UTCDateTime
from app.database import Base
from app.models.user import User

PENDENTE, ACEITO, RECUSADO, CANCELADO = "PENDENTE", "ACEITO", "RECUSADO", "CANCELADO"


class LinkRequest(Base):
    """Solicitação de vínculo aluno -> personal (precisa de aprovação do personal)."""

    __tablename__ = "link_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    personal_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(10), default=PENDENTE)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    responded_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    aluno: Mapped[User] = relationship(foreign_keys=[aluno_id], lazy="joined")
    personal: Mapped[User] = relationship(foreign_keys=[personal_id], lazy="joined")

    @property
    def aluno_name(self) -> str:
        return self.aluno.name

    @property
    def aluno_email(self) -> str:
        return self.aluno.email

    @property
    def personal_name(self) -> str:
        return self.personal.name
