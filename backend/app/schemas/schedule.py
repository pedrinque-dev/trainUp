from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ScheduleIn(BaseModel):
    start_time: datetime
    duration_min: int = Field(default=60, ge=15, le=240)
    aluno_id: int | None = None  # obrigatório apenas quando o personal agenda


class ScheduleStatusIn(BaseModel):
    # CHECKIN não é aceito aqui: só a catraca (check-in) leva a esse status.
    status: Literal["CANCELADO", "CONCLUIDO"]


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    personal_id: int
    aluno_id: int
    aluno_name: str
    personal_name: str
    start_time: datetime
    duration_min: int
    status: str
    checkin_at: datetime | None = None
