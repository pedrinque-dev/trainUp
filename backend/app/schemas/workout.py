from pydantic import BaseModel, ConfigDict, Field


class ExerciseIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    muscle_group: str = Field(default="Geral", max_length=60)
    description: str = Field(default="", max_length=500)
    video_url: str | None = Field(default=None, max_length=300)


class ExerciseOut(ExerciseIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int | None = None
    is_base: bool = False


class WorkoutItemIn(BaseModel):
    exercise_id: int
    sets: int = Field(default=3, ge=1, le=20)
    reps: int = Field(default=10, ge=1, le=100)
    target_load: float = Field(default=0, ge=0)


class WorkoutItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sets: int
    reps: int
    target_load: float
    exercise: ExerciseOut


class WorkoutIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    aluno_id: int
    weekday: int | None = Field(default=None, ge=0, le=6)
    items: list[WorkoutItemIn] = Field(min_length=1)


class WorkoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    aluno_id: int
    personal_id: int
    weekday: int | None
    items: list[WorkoutItemOut]
