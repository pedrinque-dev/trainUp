"""Registro avulso de séries (/progress) e sessões de treino (/sessions): fluxo, isolamento e validação."""
from conftest import API, make_aluno, make_personal


def _ex(c, who):
    return c.get(f"{API}/exercises", headers=who["headers"]).json()[0]["id"]


def _serie(ex, reps=10, load=20, n=1):
    return {"exercise_id": ex, "set_number": n, "reps": reps, "load_kg": load}


def test_registro_avulso_de_series_e_listagem_com_filtro(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    exs = [e["id"] for e in client.get(f"{API}/exercises", headers=p["headers"]).json()[:2]]
    r = client.post(f"{API}/progress", headers=a["headers"],
                    json={"logs": [_serie(exs[0]), _serie(exs[0], 8, 25, 2), _serie(exs[1], 12, 15)]})
    assert r.status_code == 201 and r.json() == {"saved": 3}
    todas = client.get(f"{API}/progress", headers=a["headers"]).json()
    assert len(todas) == 3
    so_um = client.get(f"{API}/progress", headers=a["headers"], params={"exercise_id": exs[0]}).json()
    assert len(so_um) == 2 and {x["exercise_id"] for x in so_um} == {exs[0]}
    assert len(client.get(f"{API}/progress", headers=a["headers"], params={"limit": 1}).json()) == 1


def test_registro_avulso_valida_entrada_e_perfil(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    ex = _ex(client, p)
    post = lambda who, body: client.post(f"{API}/progress", headers=who["headers"], json=body).status_code
    assert post(a, {"logs": [_serie(99999)]}) == 404            # exercício inexistente
    assert post(a, {"logs": []}) == 422                         # lote vazio
    assert post(a, {"logs": [_serie(ex, reps=0)]}) == 422       # reps mínimo
    assert post(a, {"logs": [_serie(ex, reps=201)]}) == 422     # reps máximo
    assert post(a, {"logs": [_serie(ex, load=-1)]}) == 422      # carga negativa
    assert post(a, {"logs": [_serie(ex, load=1001)]}) == 422    # carga acima do limite
    assert post(p, {"logs": [_serie(ex)]}) == 403               # personal não executa treino
    assert client.get(f"{API}/progress").status_code == 401     # sem token


def test_personal_lista_progresso_so_de_aluno_proprio(client):
    p1, p2 = make_personal(client, "p1@test.com"), make_personal(client, "p2@test.com")
    a1, a2 = make_aluno(client, p1, "a1@test.com"), make_aluno(client, p2, "a2@test.com")
    ex = _ex(client, p1)
    client.post(f"{API}/progress", headers=a1["headers"], json={"logs": [_serie(ex)]})
    ver = lambda who, aid: client.get(f"{API}/progress", headers=who["headers"], params={"aluno_id": aid})
    assert len(ver(p1, a1["user"]["id"]).json()) == 1
    assert ver(p2, a1["user"]["id"]).status_code == 404       # personal de outro aluno
    assert ver(a2, a1["user"]["id"]).status_code == 403       # aluno de outro aluno
    assert client.get(f"{API}/progress", headers=p1["headers"]).status_code == 400  # personal sem aluno_id


def test_sessao_fluxo_completo_listagem_e_resumo(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    ex = _ex(client, p)
    sid = client.post(f"{API}/sessions", headers=a["headers"], json={}).json()["id"]
    assert client.post(f"{API}/sessions/{sid}/sets", headers=a["headers"],
                       json={"logs": [_serie(ex, 10, 40)]}).json() == {"saved": 1}
    fim = client.post(f"{API}/sessions/{sid}/finish", headers=a["headers"])
    assert fim.status_code == 200
    assert client.post(f"{API}/sessions/{sid}/finish", headers=a["headers"]).status_code == 200  # idempotente
    lista = client.get(f"{API}/sessions", headers=a["headers"]).json()
    assert [s["id"] for s in lista] == [sid] and lista[0]["finished_at"]
    # o personal vinculado enxerga o resumo e a lista do aluno
    assert client.get(f"{API}/sessions/{sid}/summary", headers=p["headers"]).status_code == 200
    por_personal = client.get(f"{API}/sessions", headers=p["headers"], params={"aluno_id": a["user"]["id"]})
    assert por_personal.status_code == 200 and len(por_personal.json()) == 1


def test_sessao_isolamento_e_erros(client):
    p1, p2 = make_personal(client, "p1@test.com"), make_personal(client, "p2@test.com")
    a1, a2 = make_aluno(client, p1, "a1@test.com"), make_aluno(client, p1, "a2@test.com")
    ex = _ex(client, p1)
    sid = client.post(f"{API}/sessions", headers=a1["headers"], json={}).json()["id"]
    sets = lambda who, s=sid: client.post(f"{API}/sessions/{s}/sets", headers=who["headers"], json={"logs": [_serie(ex)]})
    assert sets(a2).status_code == 404                                   # sessão de outro aluno
    assert client.post(f"{API}/sessions/{sid}/finish", headers=a2["headers"]).status_code == 404
    assert client.get(f"{API}/sessions/{sid}/summary", headers=a2["headers"]).status_code == 403
    assert client.get(f"{API}/sessions/{sid}/summary", headers=p2["headers"]).status_code == 404
    assert client.get(f"{API}/sessions/99999/summary", headers=p1["headers"]).status_code == 404
    assert client.post(f"{API}/sessions", headers=p1["headers"], json={}).status_code == 403  # personal não treina
    assert client.post(f"{API}/sessions", headers=a1["headers"], json={"workout_id": 99999}).status_code == 404
    assert client.post(f"{API}/sessions/{sid}/sets", headers=a1["headers"],
                       json={"logs": [_serie(99999)]}).status_code == 404  # exercício inexistente


def test_sessao_nao_aceita_ficha_de_outro_aluno(client):
    p = make_personal(client)
    a1, a2 = make_aluno(client, p, "a1@test.com"), make_aluno(client, p, "a2@test.com")
    ex = _ex(client, p)
    ficha = client.post(f"{API}/workouts", headers=p["headers"], json={
        "name": "Treino A", "aluno_id": a1["user"]["id"], "items": [{"exercise_id": ex, "sets": 3, "reps": 10, "target_load": 20}]}).json()
    r = client.post(f"{API}/sessions", headers=a2["headers"], json={"workout_id": ficha["id"]})
    assert r.status_code == 404
    assert client.post(f"{API}/sessions", headers=a1["headers"], json={"workout_id": ficha["id"]}).status_code == 201
