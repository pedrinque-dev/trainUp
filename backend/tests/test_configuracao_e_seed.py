"""RNF05 (configuração segura para nuvem) e seed de demonstração, automatizados.
Antes eram evidências manuais (CT046); agora rodam no CI."""
import os
import subprocess
import sys
from pathlib import Path

from app.database import SessionLocal
from app.models import Exercise, Progress, Schedule, User
from app.seed import DEMO_PASSWORD, ensure_base_data, seed

BACKEND = Path(__file__).resolve().parent.parent


def _importar_config(**env):
    base = {k: v for k, v in os.environ.items() if k not in ("SECRET_KEY", "APP_ENV")}
    base.update(env, DATABASE_URL="sqlite:///./test_trainup.db")
    return subprocess.run([sys.executable, "-c", "import app.core.config"], cwd=BACKEND, env=base,
                          capture_output=True, text=True)


def test_producao_exige_secret_key():
    r = _importar_config(APP_ENV="production")
    assert r.returncode != 0 and "SECRET_KEY é obrigatória em produção" in r.stderr


def test_producao_recusa_secret_key_curta():
    r = _importar_config(APP_ENV="production", SECRET_KEY="curta")
    assert r.returncode != 0 and "muito curta" in r.stderr


def test_producao_aceita_secret_key_forte():
    assert _importar_config(APP_ENV="production", SECRET_KEY="x" * 64).returncode == 0


def test_desenvolvimento_gera_chave_temporaria():
    assert _importar_config(APP_ENV="development").returncode == 0


def test_seed_cria_dados_de_demonstracao_e_e_idempotente(client):
    with SessionLocal() as db:
        seed(db)
        usuarios = db.query(User).count()
        assert usuarios >= 7 and db.query(Progress).count() > 0 and db.query(Schedule).count() > 0
        seed(db)                                   # segunda execução não duplica
        ensure_base_data(db)
        assert db.query(User).count() == usuarios
        assert db.query(Exercise).filter(Exercise.owner_id.is_(None)).count() > 0
    r = client.post("/api/v1/auth/login", json={"email": "personal@trainup.com", "password": DEMO_PASSWORD})
    assert r.status_code == 200


def test_senhas_do_seed_estao_em_bcrypt(client):
    with SessionLocal() as db:
        seed(db)
        hashes = [u.hashed_password for u in db.query(User).all()]
    assert hashes and all(h.startswith("$2b$") and DEMO_PASSWORD not in h for h in hashes)
