"""Rate limit de tentativas de login (em memória; suficiente para 1 worker no MVP).

Dois limites: por (IP + e-mail) e um teto por e-mail, para que forjar o IP não permita
tentativas ilimitadas contra a mesma conta.
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException

from app.core.config import settings

_fails: dict[str, deque] = defaultdict(deque)


def _keys(ip: str, email: str) -> tuple[str, str]:
    return f"{ip}|{email.lower()}", f"email|{email.lower()}"


def _prune(key: str) -> deque:
    q = _fails[key]
    now = time.monotonic()
    while q and now - q[0] > settings.LOGIN_WINDOW_SECONDS:
        q.popleft()
    if not q:
        _fails.pop(key, None)  # não deixa o dicionário crescer indefinidamente
    return q


def check(ip: str, email: str) -> None:
    by_ip, by_email = _keys(ip, email)
    if len(_prune(by_ip)) >= settings.LOGIN_MAX_ATTEMPTS or len(_prune(by_email)) >= settings.LOGIN_MAX_ATTEMPTS_PER_EMAIL:
        raise HTTPException(429, "Muitas tentativas de login. Aguarde alguns minutos e tente de novo.")


def register_failure(ip: str, email: str) -> None:
    now = time.monotonic()
    for k in _keys(ip, email):
        _fails[k].append(now)


def clear(ip: str, email: str) -> None:
    _fails.pop(_keys(ip, email)[0], None)


def reset_all() -> None:
    _fails.clear()
