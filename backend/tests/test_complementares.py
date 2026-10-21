"""Testes complementares (Sprint 2 - v2.2): cobrem os requisitos que na v2.1 eram verificados só manualmente.
Copiar para backend/tests/ e executar: python -m pytest tests/test_complementares.py -v
RF03, RF07, RF08, RF09, RF10, RF15, RF17, RF27 e RNF06 (série em sessão finalizada)."""
from conftest import API, make_aluno, make_personal, schedule


def _exercise(c, who):
    return c.get(f"{API}/exercises", headers=who["headers"]).json()[0]["id"]


def _ficha(c, p, a, ex, weekday=None):
    r = c.post(f"{API}/workouts", headers=p["headers"], json={
        "name": "Treino A", "aluno_id": a["user"]["id"], "weekday": weekday,
        "items": [{"exercise_id": ex, "sets": 3, "reps": 10, "target_load": 20}]})
    assert r.status_code == 201, r.text
    return r.json()


def test_recuperar_senha_token_invalido_e_senha_fraca(client, caplog):  # RF03 (A1, A2)
    make_personal(client)
    with caplog.at_level("WARNING", logger="trainup"):
        r = client.post(f"{API}/auth/forgot", json={"email": "naoexiste@test.com"})
    assert r.status_code == 200  # mensagem genérica, não revela se o e-mail existe
    assert client.post(f"{API}/auth/reset", json={"token": "tokeninvalido", "password": "NovaSenha123"}).status_code == 400
    with caplog.at_level("WARNING", logger="trainup"):
        client.post(f"{API}/auth/forgot", json={"email": "p1@test.com"})
    token = caplog.records[-1].args[1]
    assert client.post(f"{API}/auth/reset", json={"token": token, "password": "123"}).status_code == 422


def test_ficha_de_treino_crud_e_ficha_do_dia(client):  # RF09, RF10
    p = make_personal(client)
    a = make_aluno(client, p)
    ex = _exercise(client, p)
    dia = _ficha(client, p, a, ex, weekday=2)
    livre = _ficha(client, p, a, ex, weekday=None)
    hoje = lambda wd: [w["id"] for w in client.get(f"{API}/workouts/today", headers=a["headers"], params={"weekday": wd}).json()]
    assert hoje(2) == [dia["id"]]          # ficha do dia da semana
    assert hoje(4) == [livre["id"]]        # sem ficha no dia: cai nas fichas sem dia
    r = client.put(f"{API}/workouts/{dia['id']}", headers=p["headers"], json={
        "name": "Treino A2", "aluno_id": a["user"]["id"], "weekday": 2,
        "items": [{"exercise_id": ex, "sets": 4, "reps": 8, "target_load": 25}]})
    assert r.status_code == 200 and r.json()["name"] == "Treino A2"
    assert client.delete(f"{API}/workouts/{dia['id']}", headers=p["headers"]).status_code == 204
    assert client.get(f"{API}/workouts/{dia['id']}", headers=p["headers"]).status_code == 404
    assert client.post(f"{API}/workouts", headers=a["headers"], json={  # aluno não cria ficha
        "name": "X", "aluno_id": a["user"]["id"], "items": [{"exercise_id": ex}]}).status_code == 403


def test_ficha_so_para_aluno_vinculado(client):  # RF09 (A1), RN02
    p1, p2 = make_personal(client, "p1@test.com"), make_personal(client, "p2@test.com")
    a2 = make_aluno(client, p2, "a2@test.com")
    r = client.post(f"{API}/workouts", headers=p1["headers"], json={
        "name": "Treino", "aluno_id": a2["user"]["id"], "items": [{"exercise_id": _exercise(client, p1)}]})
    assert r.status_code == 404


def test_biblioteca_propria_de_exercicios(client):  # RF08 (A1, A4)
    p = make_personal(client)
    a = make_aluno(client, p)
    body = {"name": "Remada Curvada Especial", "muscle_group": "Costas", "description": "teste"}
    ex = client.post(f"{API}/exercises", headers=p["headers"], json=body)
    assert ex.status_code == 201 and ex.json()["is_base"] is False
    assert client.post(f"{API}/exercises", headers=p["headers"], json=body).status_code == 400  # nome duplicado
    _ficha(client, p, a, ex.json()["id"])
    assert client.delete(f"{API}/exercises/{ex.json()['id']}", headers=p["headers"]).status_code == 409  # em uso


def test_dicas_por_objetivo_com_aviso(client):  # RF15, RN14
    p = make_personal(client)
    a = make_aluno(client, p)
    r = client.get(f"{API}/analytics/tips", headers=a["headers"])
    assert r.status_code == 200
    d = r.json()
    assert d["goal"] == "ganho_massa" and len(d["dicas"]) == 3 and d["aviso"]


def test_observacao_do_personal_no_relatorio(client):  # RF17
    p = make_personal(client)
    a = make_aluno(client, p)
    aid = a["user"]["id"]
    assert client.put(f"{API}/reports/aluno/{aid}/note", headers=p["headers"], json={"text": "Aumentar a carga."}).status_code == 200
    assert "Aumentar a carga." in client.get(f"{API}/reports/aluno/{aid}", headers=a["headers"]).text
    assert client.put(f"{API}/reports/aluno/{aid}/note", headers=p["headers"], json={"text": "x" * 2001}).status_code == 422
    assert client.put(f"{API}/reports/aluno/{aid}/note", headers=a["headers"], json={"text": "oi"}).status_code == 403


def test_painel_do_personal(client):  # RF27
    p = make_personal(client)
    a = make_aluno(client, p)
    schedule(client, p, a, 30)
    d = client.get(f"{API}/dashboard/personal", headers=p["headers"])
    assert d.status_code == 200
    j = d.json()
    assert j["alunos_ativos"] == 1 and j["pendentes"] == 0 and len(j["proximas"]) == 1
    assert client.get(f"{API}/dashboard/personal", headers=a["headers"]).status_code == 403


def test_remover_aluno_apaga_dados_e_nao_remove_personal(client):  # RF07 (A2)
    p = make_personal(client)
    a = make_aluno(client, p)
    schedule(client, p, a, 30)
    assert client.delete(f"{API}/users/{a['user']['id']}", headers=p["headers"]).status_code == 204
    assert client.get(f"{API}/users/{a['user']['id']}", headers=p["headers"]).status_code == 404
    assert client.delete(f"{API}/users/{p['user']['id']}", headers=p["headers"]).status_code == 400


def test_serie_em_sessao_finalizada_e_rejeitada(client):  # RNF06, RN12
    p = make_personal(client)
    a = make_aluno(client, p)
    ex = _exercise(client, p)
    sid = client.post(f"{API}/sessions", headers=a["headers"], json={}).json()["id"]
    serie = lambda n, reps=10: client.post(f"{API}/sessions/{sid}/sets", headers=a["headers"], json={
        "logs": [{"exercise_id": ex, "set_number": n, "reps": reps, "load_kg": 20}]})
    assert serie(1).status_code == 201
    assert serie(2, reps=500).status_code == 422          # limite de repetições (RN12)
    assert client.post(f"{API}/sessions/{sid}/finish", headers=a["headers"]).status_code == 200
    assert serie(2).status_code == 409                    # sessão finalizada
    assert client.post(f"{API}/sessions/{sid}/finish", headers=a["headers"]).status_code == 200  # idempotente
