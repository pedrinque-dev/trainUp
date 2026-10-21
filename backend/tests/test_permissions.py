from conftest import API, make_aluno, make_personal


def test_personal_nao_acessa_aluno_de_outro(client):
    p1, p2 = make_personal(client, "p1@test.com"), make_personal(client, "p2@test.com")
    a1 = make_aluno(client, p1, "a1@test.com")
    aid = a1["user"]["id"]
    assert client.get(f"{API}/reports/aluno/{aid}", headers=p2["headers"]).status_code == 404
    assert client.get(f"{API}/analytics/evolution?aluno_id={aid}", headers=p2["headers"]).status_code == 404
    r = client.post(f"{API}/workouts", headers=p2["headers"], json={
        "name": "Treino", "aluno_id": aid, "items": [{"exercise_id": 1, "sets": 3, "reps": 10, "target_load": 10}],
    })
    assert r.status_code == 404
    assert client.get(f"{API}/users/{aid}", headers=p2["headers"]).status_code == 404


def test_aluno_so_ve_o_proprio_relatorio(client):
    p1 = make_personal(client)
    a1, a2 = make_aluno(client, p1, "a1@test.com"), make_aluno(client, p1, "a2@test.com")
    assert client.get(f"{API}/reports/aluno/{a1['user']['id']}", headers=a1["headers"]).status_code == 200
    assert client.get(f"{API}/reports/aluno/{a2['user']['id']}", headers=a1["headers"]).status_code == 403


def test_aluno_nao_cria_exercicio_nem_edita_catalogo_base(client):
    p1 = make_personal(client)
    a1 = make_aluno(client, p1)
    assert client.post(f"{API}/exercises", headers=a1["headers"], json={"name": "Meu exercício"}).status_code == 403
    base_id = client.get(f"{API}/exercises", headers=p1["headers"]).json()[0]["id"]
    assert client.put(f"{API}/exercises/{base_id}", headers=p1["headers"], json={"name": "Alterado"}).status_code == 403
    assert client.delete(f"{API}/exercises/{base_id}", headers=p1["headers"]).status_code == 403


def test_cadastro_de_personal_exige_codigo(client):
    body = {"name": "Falso Personal", "email": "x@test.com", "password": "Senha1234", "role": "personal"}
    assert client.post(f"{API}/auth/register", json=body).status_code == 403
    assert client.post(f"{API}/auth/register", json={**body, "signup_code": "errado"}).status_code == 403


def test_rate_limit_do_login(client):
    make_personal(client)
    for _ in range(5):
        assert client.post(f"{API}/auth/login", json={"email": "p1@test.com", "password": "errada123"}).status_code == 401
    assert client.post(f"{API}/auth/login", json={"email": "p1@test.com", "password": "errada123"}).status_code == 429


def test_senha_fraca_e_rejeitada(client):
    r = client.post(f"{API}/auth/register", json={"name": "Aluno", "email": "z@test.com", "password": "12345678"})
    assert r.status_code == 422
