from datetime import datetime

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tz import now_utc
from app.core.types import UTCDateTime
from app.database import Base


class WorkoutSession(Base):
    """Uma sessão de treino executada pelo aluno (agrupa as séries de `progress`)."""

    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    workout_id: Mapped[int | None] = mapped_column(ForeignKey("workouts.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
