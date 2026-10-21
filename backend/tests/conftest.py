import os

os.environ.update(
    DATABASE_URL="sqlite:///./test_trainup.db", APP_ENV="test", SEED_DEMO="false",
    SECRET_KEY="test-secret-key-test-secret-key-0123456789", PERSONAL_SIGNUP_CODE="CODIGO-TESTE",
)

from datetime import datetime, timedelta, timezone  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core import ratelimit  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import ensure_base_data  # noqa: E402

API = "/api/v1"
PASSWORD = "Senha1234"


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ensure_base_data(db)
    ratelimit.reset_all()
    return TestClient(app)  # sem "with": o lifespan (migrações/seed) não roda nos testes


def login(c, email: str, password: str = PASSWORD) -> dict:
    r = c.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    return {"headers": {"Authorization": f"Bearer {data['access_token']}"}, "user": data["user"]}


def make_personal(c, email: str = "p1@test.com") -> dict:
    r = c.post(f"{API}/auth/register", json={
        "name": "Personal Teste", "email": email, "password": PASSWORD, "role": "personal", "signup_code": "CODIGO-TESTE",
    })
    assert r.status_code == 201, r.text
    return login(c, email)


def make_aluno(c, personal: dict, email: str = "a1@test.com", name: str = "Aluno Teste") -> dict:
    r = c.post(f"{API}/users", headers=personal["headers"], json={
        "name": name, "email": email, "password": PASSWORD, "goal": "ganho_massa",
    })
    assert r.status_code == 201, r.text
    return login(c, email)


def iso(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def schedule(c, personal: dict, aluno: dict, minutes: int, duration: int = 60):
    return c.post(f"{API}/schedules", headers=personal["headers"], json={
        "aluno_id": aluno["user"]["id"], "start_time": iso(minutes), "duration_min": duration,
    })
