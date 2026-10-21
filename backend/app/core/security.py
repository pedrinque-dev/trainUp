from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models.user import ROLE_ALUNO, ROLE_PERSONAL, User

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "role": user.role, "tv": user.token_version or 0, "exp": exp}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    err = HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou ausente")
    if not creds:
        raise err
    try:
        data = jwt.decode(creds.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user = db.get(User, int(data["sub"]))
        tv = int(data.get("tv", 0))
    except (JWTError, KeyError, ValueError, TypeError):
        raise err
    if not user or tv != (user.token_version or 0):
        raise err  # usuário removido ou token revogado (logout / troca de senha)
    return user


def require_personal(user: User = Depends(get_current_user)) -> User:
    if user.role != ROLE_PERSONAL:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas Personal Trainers")
    return user


def require_aluno(user: User = Depends(get_current_user)) -> User:
    if user.role != ROLE_ALUNO:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas alunos")
    return user


def resolve_aluno(db: Session, user: User, aluno_id: int | None = None) -> User:
    """Aluno -> ele mesmo. Personal -> um aluno que pertença a ele."""
    if user.role == ROLE_ALUNO:
        if aluno_id not in (None, user.id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado")
        return user
    if aluno_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe aluno_id")
    aluno = db.get(User, aluno_id)
    if not aluno or aluno.role != ROLE_ALUNO or aluno.personal_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aluno não encontrado")
    return aluno
