from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.tz import now_utc
from app.core.types import UTCDateTime
from app.database import Base
from app.models.user import User


class Turnstile(Base):
    """Catraca virtual. O estado fica no banco (máquina de estados persistida)."""

    __tablename__ = "turnstiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    location: Mapped[str] = mapped_column(String(120), default="")
    state: Mapped[str] = mapped_column(String(24), default="TRAVADA")
    state_since: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    unlock_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    blocked_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    consecutive_denials: Mapped[int] = mapped_column(Integer, default=0)
    last_aluno_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AccessLog(Base):
    """Histórico de eventos da catraca (tentativas, passagens, timeouts, bloqueios)."""

    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    turnstile_id: Mapped[int | None] = mapped_column(ForeignKey("turnstiles.id"), nullable=True, index=True)
    aluno_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    personal_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    schedule_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event: Mapped[str] = mapped_column(String(20), default="TENTATIVA")  # TENTATIVA|PASSAGEM|TIMEOUT|BLOQUEIO|RESET
    granted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reason: Mapped[str] = mapped_column(String(200), default="")
    scenario: Mapped[str | None] = mapped_column(String(20), nullable=True)
    simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    cycle_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc, index=True)

    aluno: Mapped[User | None] = relationship(foreign_keys=[aluno_id], lazy="joined")

    @property
    def aluno_name(self) -> str | None:
        return self.aluno.name if self.aluno else None
