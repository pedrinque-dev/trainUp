from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SetIn(BaseModel):
    exercise_id: int
    workout_id: int | None = None
    set_number: int = Field(default=1, ge=1)
    reps: int = Field(ge=1, le=200)
    load_kg: float = Field(ge=0, le=1000)


class SetBatch(BaseModel):
    logs: list[SetIn] = Field(min_length=1)


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    exercise_id: int
    workout_id: int | None
    session_id: int | None = None
    set_number: int
    reps: int
    load_kg: float
    performed_at: datetime


class SessionStartIn(BaseModel):
    workout_id: int | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    workout_id: int | None
    started_at: datetime
    finished_at: datetime | None = None


class CheckinIn(BaseModel):
    schedule_id: int
    turnstile_id: int | None = None


class SimulateIn(BaseModel):
    scenario: Literal["valida", "invalida", "sem_aula", "fora_janela", "dupla"]
    turnstile_id: int | None = None
    aluno_id: int | None = None


class TurnstileRef(BaseModel):
    turnstile_id: int | None = None


class NoteIn(BaseModel):
    text: str = Field(max_length=2000)
