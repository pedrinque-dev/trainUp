from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tz import now_utc
from app.core.types import UTCDateTime
from app.database import Base

ROLE_PERSONAL = "personal"
ROLE_ALUNO = "aluno"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(10))  # personal | aluno
    goal: Mapped[str | None] = mapped_column(String(30), nullable=True)
    personal_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)  # vínculo ATIVO
    invite_code: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    reset_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    reset_expires: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    # incrementado no logout / troca de senha: invalida todos os JWT emitidos antes
    token_version: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
