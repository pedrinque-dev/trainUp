from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tz import now_utc
from app.core.types import UTCDateTime
from app.database import Base


class Progress(Base):
    """Uma série executada: exercício, repetições e carga."""

    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    workout_id: Mapped[int | None] = mapped_column(ForeignKey("workouts.id"), nullable=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("workout_sessions.id"), nullable=True, index=True)
    set_number: Mapped[int] = mapped_column(Integer, default=1)
    reps: Mapped[int] = mapped_column(Integer)
    load_kg: Mapped[float] = mapped_column(Float)
    performed_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
