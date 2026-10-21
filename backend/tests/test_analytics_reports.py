from datetime import timedelta

from app.core.tz import now_utc, today_local
from app.database import SessionLocal
from app.models import Exercise, Progress, User
from app.services.analytics import stagnation, stagnation_streak
from conftest import API, make_aluno, make_personal


def test_streak_de_estagnacao():
    assert stagnation_streak([40, 40, 40, 40, 40]) == 4
    assert stagnation_streak([40, 42.5, 45]) == 0
    assert stagnation_streak([40, 45, 45, 45]) == 2
    assert stagnation_streak([]) == 0


def _history(aluno_id: int, name: str, loads: list[float]):
    with SessionLocal() as db:
        ex = Exercise(name=name, muscle_group="Teste", owner_id=None)
        db.add(ex)
        db.flush()
        for i, load in enumerate(loads):
            day = now_utc() - timedelta(days=(len(loads) - i) * 3)
            for s in range(3):
                db.add(Progress(aluno_id=aluno_id, exercise_id=ex.id, set_number=s + 1, reps=10, load_kg=load, performed_at=day))
        db.commit()


def test_alerta_de_estagnacao(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    aid = a["user"]["id"]
    _history(aid, "Exercício parado", [40, 40, 40, 40, 40])
    _history(aid, "Exercício evoluindo", [40, 42.5, 45, 47.5])
    with SessionLocal() as db:
        alerts = stagnation(db, db.get(User, aid), 3)
    assert [x["exercise"] for x in alerts] == ["Exercício parado"]
    assert alerts[0]["sessions"] == 4
    r = client.get(f"{API}/analytics/stagnation", headers=p["headers"]).json()
    assert len(r) == 1


def test_relatorio_json_e_pdf(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    aid = a["user"]["id"]
    _history(aid, "Agachamento teste", [60, 62.5, 65, 67.5])
    start, end = today_local() - timedelta(days=30), today_local()
    r = client.get(f"{API}/reports/aluno/{aid}?start={start}&end={end}", headers=p["headers"])
    assert r.status_code == 200
    data = r.json()
    ex = data["exercises"][0]
    assert ex["exercise"] == "Agachamento teste" and ex["progression_pct"] == 12.5
    assert data["attendance"]["sessoes"] == 4
    assert "12,5%" in data["summary_text"]

    note = client.put(f"{API}/reports/aluno/{aid}/note", headers=p["headers"], json={"text": "Ótimo ritmo."})
    assert note.status_code == 200
    assert client.get(f"{API}/reports/aluno/{aid}", headers=a["headers"]).json()["note"]["text"] == "Ótimo ritmo."

    pdf = client.get(f"{API}/reports/aluno/{aid}/pdf?start={start}&end={end}", headers=a["headers"])
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    assert client.put(f"{API}/reports/aluno/{aid}/note", headers=a["headers"], json={"text": "x"}).status_code == 403


def test_sessao_de_treino_resumo_com_recorde(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    ex_id = client.get(f"{API}/exercises", headers=p["headers"]).json()[0]["id"]

    def run(load):
        sid = client.post(f"{API}/sessions", headers=a["headers"], json={}).json()["id"]
        client.post(f"{API}/sessions/{sid}/sets", headers=a["headers"], json={"logs": [
            {"exercise_id": ex_id, "set_number": 1, "reps": 10, "load_kg": load},
            {"exercise_id": ex_id, "set_number": 2, "reps": 10, "load_kg": load},
        ]})
        return client.post(f"{API}/sessions/{sid}/finish", headers=a["headers"]).json()

    first, second = run(40), run(45)
    assert first["records"] == [] and first["total_volume"] == 800
    assert second["records"] and second["exercises"][0]["previous_max"] == 40
