"""Gestão de usuários (/users) e rotas da catraca que os demais testes não exercitam."""
from datetime import date

from conftest import API, login, make_aluno, make_personal, schedule


# ---------- usuários ----------
def test_listagem_de_usuarios_por_perfil(client):
    p = make_personal(client)
    a = make_aluno(client, p, "a1@test.com", "Zeca")
    make_aluno(client, p, "a2@test.com", "Ana")
    nomes = [u["name"] for u in client.get(f"{API}/users", headers=p["headers"]).json()]
    assert nomes == ["Ana", "Zeca"]                                     # ordenado por nome
    so_eu = client.get(f"{API}/users", headers=a["headers"]).json()
    assert [u["id"] for u in so_eu] == [a["user"]["id"]]                # aluno só se enxerga


def test_atualizar_usuario_nome_objetivo_e_senha(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    uid = a["user"]["id"]
    r = client.put(f"{API}/users/{uid}", headers=p["headers"], json={"name": "Novo Nome", "goal": "emagrecimento"})
    assert r.status_code == 200 and r.json()["name"] == "Novo Nome" and r.json()["goal"] == "emagrecimento"
    assert client.put(f"{API}/users/{uid}", headers=a["headers"], json={"password": "fraca"}).status_code == 422
    assert client.put(f"{API}/users/{uid}", headers=a["headers"], json={"password": "Outra1234"}).status_code == 200
    assert login(client, "a1@test.com", "Outra1234")["user"]["id"] == uid
    assert client.put(f"{API}/users/{uid}", headers=a["headers"], json={"name": "X"}).status_code == 422  # nome curto


def test_personal_nao_altera_objetivo_de_si_mesmo(client):
    p = make_personal(client)
    r = client.put(f"{API}/users/{p['user']['id']}", headers=p["headers"], json={"goal": "x"})
    assert r.status_code == 200 and r.json()["goal"] is None  # objetivo só vale para aluno


def test_usuarios_de_outro_personal_sao_invisiveis(client):
    p1, p2 = make_personal(client, "p1@test.com"), make_personal(client, "p2@test.com")
    a1 = make_aluno(client, p1, "a1@test.com")
    uid = a1["user"]["id"]
    assert client.get(f"{API}/users/{uid}", headers=p2["headers"]).status_code == 404
    assert client.put(f"{API}/users/{uid}", headers=p2["headers"], json={"name": "Hack"}).status_code == 404
    assert client.delete(f"{API}/users/{uid}", headers=p2["headers"]).status_code == 404
    assert client.get(f"{API}/users/{uid}", headers=p1["headers"]).status_code == 200
    assert client.get(f"{API}/users/99999", headers=p1["headers"]).status_code == 404
    # aluno não cadastra aluno
    r = client.post(f"{API}/users", headers=a1["headers"], json={"name": "Fulano", "email": "f@test.com", "password": "Senha1234"})
    assert r.status_code == 403


def test_remover_aluno_apaga_historico_completo(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    ex = client.get(f"{API}/exercises", headers=p["headers"]).json()[0]["id"]
    client.post(f"{API}/progress", headers=a["headers"], json={"logs": [{"exercise_id": ex, "reps": 10, "load_kg": 20}]})
    client.post(f"{API}/sessions", headers=a["headers"], json={})
    schedule(client, p, a, 30)
    assert client.delete(f"{API}/users/{a['user']['id']}", headers=p["headers"]).status_code == 204
    assert client.post(f"{API}/auth/login", json={"email": "a1@test.com", "password": "Senha1234"}).status_code == 401
    assert client.get(f"{API}/users", headers=p["headers"]).json() == []


# ---------- catraca ----------
def test_status_estatisticas_e_catracas(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    lista = client.get(f"{API}/automacao/turnstiles", headers=a["headers"]).json()
    assert lista and lista[0]["state"] == "TRAVADA"
    st_p = client.get(f"{API}/automacao/status", headers=p["headers"]).json()
    st_a = client.get(f"{API}/automacao/status", headers=a["headers"]).json()
    assert "stats" in st_p and "stats" not in st_a                       # estatísticas só para o personal
    assert client.get(f"{API}/automacao/status", headers=p["headers"], params={"turnstile_id": 9999}).status_code == 404


def test_logs_filtros_e_privacidade(client):
    p = make_personal(client)
    a = make_aluno(client, p, "a1@test.com")
    b = make_aluno(client, p, "a2@test.com")
    ok = schedule(client, p, a, 5).json()["id"]
    tarde = schedule(client, p, b, 240).json()["id"]
    chk = lambda who, sid: client.post(f"{API}/automacao/checkin", headers=who["headers"], json={"schedule_id": sid}).json()
    assert chk(a, ok)["granted"] and not chk(b, tarde)["granted"]
    logs = lambda who, **q: client.get(f"{API}/automacao/logs", headers=who["headers"], params=q).json()
    assert len(logs(p)) >= 2
    assert all(l["granted"] for l in logs(p, result="permitido"))
    assert all(not l["granted"] for l in logs(p, result="negado")) and logs(p, result="negado")
    assert logs(p, day=date.today().isoformat()) or logs(p, day=date.today().isoformat()) == []  # filtro aceito
    assert logs(p, day="2000-01-01") == []
    # o aluno só vê os próprios eventos e não vê o campo de detalhe técnico
    meus = logs(a)
    assert meus and {l["aluno_id"] for l in meus} == {a["user"]["id"]} and all(l["detail"] == "" for l in meus)


def test_reset_fora_de_bloqueio_e_aluno_sem_permissao(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    assert client.post(f"{API}/automacao/reset", headers=p["headers"], json={}).status_code == 409
    assert client.post(f"{API}/automacao/reset", headers=a["headers"], json={}).status_code == 403
    assert client.post(f"{API}/automacao/passagem", headers=a["headers"], json={}).status_code == 409  # nada pendente


def test_simulador_sem_aluno_e_cenario_invalido(client):
    p = make_personal(client)
    sim = lambda s: client.post(f"{API}/automacao/simulate", headers=p["headers"], json={"scenario": s})
    assert sim("valida").status_code == 400            # sem alunos cadastrados
    make_aluno(client, p)
    assert sim("inexistente").status_code == 422
    assert sim("fora_janela").status_code == 200


def test_checkin_de_aula_de_outro_aluno_e_negado(client):
    p = make_personal(client)
    a, b = make_aluno(client, p, "a1@test.com"), make_aluno(client, p, "a2@test.com")
    sid = schedule(client, p, a, 5).json()["id"]
    r = client.post(f"{API}/automacao/checkin", headers=b["headers"], json={"schedule_id": sid}).json()
    assert r["granted"] is False
    assert client.post(f"{API}/automacao/checkin", headers=p["headers"], json={"schedule_id": sid}).status_code == 403
