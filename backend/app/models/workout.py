from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Exercise(Base):
    """owner_id nulo = catálogo base do sistema (somente leitura)."""

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    muscle_group: Mapped[str] = mapped_column(String(60), default="Geral")
    description: Mapped[str] = mapped_column(String(500), default="")
    video_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    @property
    def is_base(self) -> bool:
        return self.owner_id is None


class Workout(Base):
    """Ficha de treino de um aluno, criada por um personal."""

    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    personal_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    aluno_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    weekday: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0=segunda ... 6=domingo

    items: Mapped[list["WorkoutItem"]] = relationship(
        back_populates="workout", cascade="all, delete-orphan", lazy="selectin",
        order_by="WorkoutItem.id",
    )


class WorkoutItem(Base):
    __tablename__ = "workout_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    sets: Mapped[int] = mapped_column(Integer, default=3)
    reps: Mapped[int] = mapped_column(Integer, default=10)
    target_load: Mapped[float] = mapped_column(Float, default=0)

    workout: Mapped[Workout] = relationship(back_populates="items")
    exercise: Mapped[Exercise] = relationship(lazy="joined")
