from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def check_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres")
    if len(v.encode()) > 72:
        raise ValueError("A senha é longa demais (máximo de 72 bytes)")
    if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
        raise ValueError("A senha deve conter letras e números")
    return v


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str
    role: Literal["personal", "aluno"] = "aluno"
    goal: str | None = None
    signup_code: str | None = None  # exigido para cadastro de personal
    invite_code: str | None = None  # opcional para aluno: já solicita vínculo

    @field_validator("password")
    @classmethod
    def _pw(cls, v):
        return check_password(v)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    goal: str | None = None
    password: str | None = None

    @field_validator("password")
    @classmethod
    def _pw(cls, v):
        return check_password(v) if v else v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str
    goal: str | None = None
    personal_id: int | None = None


class MeOut(UserOut):
    invite_code: str | None = None
    personal_name: str | None = None


class LoginIn(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: MeOut


class ForgotIn(BaseModel):
    email: str


class ResetIn(BaseModel):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def _pw(cls, v):
        return check_password(v)


class LinkRequestIn(BaseModel):
    invite_code: str = Field(min_length=4, max_length=12)


class LinkRespondIn(BaseModel):
    accept: bool


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    aluno_id: int
    aluno_name: str
    aluno_email: str
    personal_id: int
    personal_name: str
    created_at: datetime
