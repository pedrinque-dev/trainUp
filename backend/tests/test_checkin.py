from conftest import API, make_aluno, make_personal, schedule


def checkin(c, aluno, sid):
    return c.post(f"{API}/automacao/checkin", headers=aluno["headers"], json={"schedule_id": sid}).json()


def test_checkin_dentro_da_janela_libera_a_catraca(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    sid = schedule(client, p, a, 5).json()["id"]
    r = checkin(client, a, sid)
    assert r["granted"] is True
    assert r["turnstile"]["state"] == "AGUARDANDO_PASSAGEM" and r["turnstile"]["color"] == "VERDE"
    assert [t["state"] for t in r["transitions"]] == ["VALIDANDO", "LIBERADA", "AGUARDANDO_PASSAGEM"]
    s = client.get(f"{API}/schedules", headers=a["headers"]).json()[0]
    assert s["status"] == "CHECKIN" and s["checkin_at"]


def test_segundo_checkin_da_mesma_aula_e_negado(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    sid = schedule(client, p, a, 5).json()["id"]
    assert checkin(client, a, sid)["granted"]
    second = checkin(client, a, sid)
    assert second["granted"] is False and "já realizado" in second["reason"]


def test_fora_da_janela_e_negado(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    sid = schedule(client, p, a, 180).json()["id"]
    r = checkin(client, a, sid)
    assert r["granted"] is False and "cedo demais" in r["reason"]
    assert r["turnstile"]["state"] == "TRAVADA"


def test_bloqueio_apos_negativas_seguidas_e_rearme(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    sid = schedule(client, p, a, 180).json()["id"]
    last = None
    for _ in range(3):
        last = checkin(client, a, sid)
    assert last["turnstile"]["state"] == "BLOQUEIO"
    assert "BLOQUEIO" in checkin(client, a, sid)["reason"]
    assert client.post(f"{API}/automacao/reset", headers=p["headers"], json={}).json()["turnstile"]["state"] == "TRAVADA"


def test_simulador_cenarios(client):
    p = make_personal(client)
    make_aluno(client, p)
    sim = lambda s: client.post(f"{API}/automacao/simulate", headers=p["headers"], json={"scenario": s}).json()["cycles"]
    assert sim("valida")[0]["granted"] is True
    client.post(f"{API}/automacao/passagem", headers=p["headers"], json={})
    assert sim("invalida")[0]["reason"] == "credencial não reconhecida"
    assert "sem agendamento" in sim("sem_aula")[0]["reason"]
    dupla = sim("dupla")
    assert [c["granted"] for c in dupla] == [True, False]
    status = client.get(f"{API}/automacao/status", headers=p["headers"]).json()
    assert status["stats"]["permitidos"] >= 2 and status["stats"]["negados"] >= 2


def test_aluno_nao_usa_simulador(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    assert client.post(f"{API}/automacao/simulate", headers=a["headers"], json={"scenario": "valida"}).status_code == 403
