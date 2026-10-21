import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core import ratelimit
from app.core.config import settings
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.core.tz import now_utc
from app.database import get_db
from app.models import LinkRequest, User
from app.models.link import PENDENTE
from app.models.user import ROLE_ALUNO, ROLE_PERSONAL
from app.schemas.user import ForgotIn, LoginIn, MeOut, ResetIn, Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["Autenticação"])
log = logging.getLogger("trainup")
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_invite_code(db: Session) -> str:
    while True:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
        if not db.query(User).filter(User.invite_code == code).first():
            return code


def find_personal_by_code(db: Session, code: str) -> User:
    p = db.query(User).filter(User.invite_code == code.strip().upper(), User.role == ROLE_PERSONAL).first()
    if not p:
        raise HTTPException(404, "Código de convite inválido")
    return p


def create_user(db: Session, data: UserCreate, role: str, personal_id: int | None = None) -> User:
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(400, "E-mail já cadastrado")
    user = User(
        name=data.name, email=data.email.lower(), hashed_password=hash_password(data.password), role=role,
        goal=data.goal if role == ROLE_ALUNO else None,
        personal_id=personal_id if role == ROLE_ALUNO else None,
        invite_code=new_invite_code(db) if role == ROLE_PERSONAL else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def me_out(db: Session, user: User) -> MeOut:
    out = MeOut.model_validate(user)
    if user.role == ROLE_PERSONAL:
        out.invite_code = user.invite_code
    elif user.personal_id:
        p = db.get(User, user.personal_id)
        out.personal_name = p.name if p else None
    return out


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    personal = None
    if data.role == ROLE_PERSONAL:
        if not settings.PERSONAL_SIGNUP_CODE:
            raise HTTPException(403, "O cadastro de personal está desabilitado. Peça o código de cadastro ao administrador.")
        if not hmac.compare_digest(data.signup_code or "", settings.PERSONAL_SIGNUP_CODE):
            raise HTTPException(403, "Código de cadastro de personal inválido")
    elif data.invite_code:
        personal = find_personal_by_code(db, data.invite_code)
    user = create_user(db, data, data.role)
    if personal:
        db.add(LinkRequest(aluno_id=user.id, personal_id=personal.id, status=PENDENTE))
        db.commit()
    return user


def client_ip(request: Request) -> str:
    """IP do cliente. X-Real-IP só é confiável atrás do nginx (TRUST_PROXY_HEADERS)."""
    if settings.TRUST_PROXY_HEADERS and request.headers.get("x-real-ip"):
        return request.headers["x-real-ip"]
    return request.client.host if request.client else "?"


@router.post("/login", response_model=Token)
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request)
    ratelimit.check(ip, data.email)
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        ratelimit.register_failure(ip, data.email)
        raise HTTPException(401, "E-mail ou senha incorretos")
    ratelimit.clear(ip, data.email)
    return Token(access_token=create_access_token(user), user=me_out(db, user))


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return me_out(db, user)


@router.post("/logout", status_code=204)
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoga todos os tokens do usuário (incrementa token_version)."""
    user.token_version = (user.token_version or 0) + 1
    db.commit()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/forgot")
def forgot(data: ForgotIn, db: Session = Depends(get_db)):
    """MVP: o token de recuperação é impresso no log do backend (não há envio de e-mail)."""
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user:
        token = secrets.token_urlsafe(12)
        user.reset_token_hash = _hash(token)
        user.reset_expires = now_utc() + timedelta(minutes=settings.RESET_TOKEN_MINUTES)
        db.commit()
        log.warning("RECUPERAÇÃO DE SENHA | %s | token: %s | válido por %s min",
                    user.email, token, settings.RESET_TOKEN_MINUTES)
    return {"detail": "Se o e-mail existir, um token de recuperação foi gerado. No MVP, ele aparece no log do backend."}


@router.post("/reset")
def reset(data: ResetIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token_hash == _hash(data.token.strip())).first()
    if not user or not user.reset_expires or user.reset_expires < now_utc():
        raise HTTPException(400, "Token inválido ou expirado")
    user.hashed_password = hash_password(data.password)
    user.reset_token_hash = user.reset_expires = None
    user.token_version = (user.token_version or 0) + 1  # derruba sessões antigas
    db.commit()
    return {"detail": "Senha atualizada. Faça login."}
