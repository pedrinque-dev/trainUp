from conftest import API, PASSWORD, login, make_personal


def test_fluxo_de_vinculo_com_aprovacao(client):
    p = make_personal(client)
    code = p["user"]["invite_code"]
    assert code

    r = client.post(f"{API}/auth/register", json={"name": "Aluna Nova", "email": "n@test.com", "password": PASSWORD})
    assert r.status_code == 201
    a = login(client, "n@test.com")
    assert a["user"]["personal_id"] is None

    # sem vínculo ativo, não agenda
    r = client.post(f"{API}/schedules", headers=a["headers"], json={"start_time": "2099-01-01T10:00:00+00:00"})
    assert r.status_code == 400

    assert client.post(f"{API}/links/request", headers=a["headers"], json={"invite_code": "ZZZZZZZZ"}).status_code == 404
    assert client.post(f"{API}/links/request", headers=a["headers"], json={"invite_code": code}).status_code == 201
    assert client.post(f"{API}/links/request", headers=a["headers"], json={"invite_code": code}).status_code == 400

    pending = client.get(f"{API}/links/pending", headers=p["headers"]).json()
    assert len(pending) == 1
    r = client.post(f"{API}/links/{pending[0]['id']}/respond", headers=p["headers"], json={"accept": True})
    assert r.status_code == 200 and r.json()["status"] == "ACEITO"

    me = client.get(f"{API}/auth/me", headers=a["headers"]).json()
    assert me["personal_id"] == p["user"]["id"]
    assert client.get(f"{API}/users", headers=p["headers"]).json()[0]["email"] == "n@test.com"


def test_recusar_nao_vincula(client):
    p = make_personal(client)
    client.post(f"{API}/auth/register", json={
        "name": "Aluno", "email": "r@test.com", "password": PASSWORD, "invite_code": p["user"]["invite_code"],
    })
    req = client.get(f"{API}/links/pending", headers=p["headers"]).json()[0]
    client.post(f"{API}/links/{req['id']}/respond", headers=p["headers"], json={"accept": False})
    a = login(client, "r@test.com")
    assert client.get(f"{API}/auth/me", headers=a["headers"]).json()["personal_id"] is None
