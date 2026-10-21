from conftest import API, login, make_aluno, make_personal, schedule


def test_logout_revoga_o_token(client):
    p = make_personal(client)
    assert client.get(f"{API}/auth/me", headers=p["headers"]).status_code == 200
    assert client.post(f"{API}/auth/logout", headers=p["headers"]).status_code == 204
    assert client.get(f"{API}/auth/me", headers=p["headers"]).status_code == 401
    # novo login emite token válido
    again = login(client, "p1@test.com")
    assert client.get(f"{API}/auth/me", headers=again["headers"]).status_code == 200


def test_troca_de_senha_derruba_sessoes_antigas(client, caplog):
    p = make_personal(client)
    with caplog.at_level("WARNING", logger="trainup"):
        client.post(f"{API}/auth/forgot", json={"email": "p1@test.com"})
    token = caplog.records[-1].args[1]
    r = client.post(f"{API}/auth/reset", json={"token": token, "password": "NovaSenha123"})
    assert r.status_code == 200, r.text
    assert client.get(f"{API}/auth/me", headers=p["headers"]).status_code == 401
    assert login(client, "p1@test.com", "NovaSenha123")["user"]["email"] == "p1@test.com"


def test_rate_limit_por_email_ignora_ip_forjado(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
    monkeypatch.setattr(settings, "LOGIN_MAX_ATTEMPTS_PER_EMAIL", 8)
    make_personal(client)
    codes = []
    for i in range(10):  # cada tentativa "vem" de um IP diferente
        r = client.post(f"{API}/auth/login", headers={"x-real-ip": f"10.0.0.{i}"},
                        json={"email": "p1@test.com", "password": "errada123"})
        codes.append(r.status_code)
    assert codes[:8] == [401] * 8 and codes[8:] == [429, 429]


def test_x_real_ip_ignorado_sem_proxy_confiavel(client):
    make_personal(client)
    for i in range(5):
        client.post(f"{API}/auth/login", headers={"x-real-ip": f"10.0.1.{i}"},
                    json={"email": "p1@test.com", "password": "errada123"})
    r = client.post(f"{API}/auth/login", headers={"x-real-ip": "10.0.1.99"},
                    json={"email": "p1@test.com", "password": "errada123"})
    assert r.status_code == 429  # mesmo IP real: o cabeçalho forjado não burla o limite


def test_passagem_so_pelo_aluno_liberado_ou_seu_personal(client):
    p1, p2 = make_personal(client, "p1@test.com"), make_personal(client, "p2@test.com")
    a1, a2 = make_aluno(client, p1, "a1@test.com"), make_aluno(client, p1, "a2@test.com")
    sid = schedule(client, p1, a1, 5).json()["id"]
    assert client.post(f"{API}/automacao/checkin", headers=a1["headers"], json={"schedule_id": sid}).json()["granted"]
    pas = lambda who: client.post(f"{API}/automacao/passagem", headers=who["headers"], json={})
    assert pas(a2).status_code == 403   # outro aluno
    assert pas(p2).status_code == 403   # personal de outro aluno
    assert pas(a1).status_code == 200   # quem foi liberado
    assert pas(a1).status_code == 409   # nada pendente
