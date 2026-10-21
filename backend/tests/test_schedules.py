from conftest import API, make_aluno, make_personal, schedule


def test_conflito_de_agenda(client):
    p = make_personal(client)
    a1, a2 = make_aluno(client, p, "a1@test.com"), make_aluno(client, p, "a2@test.com")
    assert schedule(client, p, a1, 120, 60).status_code == 201
    assert schedule(client, p, a2, 150, 60).status_code == 409  # sobrepõe a aula anterior
    assert schedule(client, p, a2, 240, 60).status_code == 201


def test_transicoes_de_status(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    sid = schedule(client, p, a, 120).json()["id"]
    # CHECKIN não pode ser definido manualmente
    assert client.patch(f"{API}/schedules/{sid}/status", headers=p["headers"], json={"status": "CHECKIN"}).status_code == 422
    # AGENDADO -> CONCLUIDO é inválido
    assert client.patch(f"{API}/schedules/{sid}/status", headers=p["headers"], json={"status": "CONCLUIDO"}).status_code == 409
    # aluno só cancela
    assert client.patch(f"{API}/schedules/{sid}/status", headers=a["headers"], json={"status": "CONCLUIDO"}).status_code == 403
    r = client.patch(f"{API}/schedules/{sid}/status", headers=a["headers"], json={"status": "CANCELADO"})
    assert r.status_code == 200 and r.json()["status"] == "CANCELADO"
    # cancelada não volta
    assert client.patch(f"{API}/schedules/{sid}/status", headers=p["headers"], json={"status": "CONCLUIDO"}).status_code == 409


def test_checkin_leva_a_concluido(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    sid = schedule(client, p, a, 5).json()["id"]
    assert client.post(f"{API}/automacao/checkin", headers=a["headers"], json={"schedule_id": sid}).json()["granted"]
    r = client.patch(f"{API}/schedules/{sid}/status", headers=p["headers"], json={"status": "CONCLUIDO"})
    assert r.status_code == 200 and r.json()["status"] == "CONCLUIDO"
