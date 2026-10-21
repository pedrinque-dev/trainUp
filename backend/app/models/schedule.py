from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import UTCDateTime
from app.database import Base
from app.models.user import User

AGENDADO, CHECKIN, CANCELADO, CONCLUIDO = "AGENDADO", "CHECKIN", "CANCELADO", "CONCLUIDO"


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    personal_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    start_time: Mapped[datetime] = mapped_column(UTCDateTime())
    duration_min: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[str] = mapped_column(String(12), default=AGENDADO)
    checkin_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    aluno: Mapped[User] = relationship(foreign_keys=[aluno_id], lazy="joined")
    personal: Mapped[User] = relationship(foreign_keys=[personal_id], lazy="joined")

    @property
    def aluno_name(self) -> str:
        return self.aluno.name

    @property
    def personal_name(self) -> str:
        return self.personal.name
