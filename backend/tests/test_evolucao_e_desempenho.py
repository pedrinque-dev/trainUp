"""RF13 (evolução de carga), RNF03 (tempo de resposta) e RNF08 (ciclo da catraca em até 1 s)."""
import time
from datetime import timedelta

from app.core.tz import now_utc
from app.database import SessionLocal
from app.models import Exercise, Progress
from conftest import API, make_aluno, make_personal, schedule


def _history(aluno_id: int, name: str, loads: list[float], sets: int = 3) -> int:
    with SessionLocal() as db:
        ex = Exercise(name=name, muscle_group="Teste", owner_id=None)
        db.add(ex)
        db.flush()
        for i, load in enumerate(loads):
            day = now_utc() - timedelta(days=(len(loads) - i) * 3)
            for s in range(sets):
                db.add(Progress(aluno_id=aluno_id, exercise_id=ex.id, set_number=s + 1, reps=10, load_kg=load, performed_at=day))
        db.commit()
        return ex.id


def test_evolucao_calcula_media_e_progressao(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    aid = a["user"]["id"]
    ex_id = _history(aid, "Agachamento evolução", [60, 62.5, 65, 67.5])
    _history(aid, "Supino evolução", [40, 40, 42.5])

    r = client.get(f"{API}/analytics/evolution?aluno_id={aid}", headers=p["headers"])
    assert r.status_code == 200
    data = {e["exercise"]: e for e in r.json()}
    ag = data["Agachamento evolução"]
    assert [pt["avg_load"] for pt in ag["points"]] == [60, 62.5, 65, 67.5]
    assert [pt["date"] for pt in ag["points"]] == sorted(pt["date"] for pt in ag["points"])
    assert ag["progression_pct"] == 12.5
    assert data["Supino evolução"]["progression_pct"] == 6.2

    só_um = client.get(f"{API}/analytics/evolution?aluno_id={aid}&exercise_id={ex_id}", headers=p["headers"]).json()
    assert [e["exercise"] for e in só_um] == ["Agachamento evolução"]

    # o próprio aluno consulta sem informar aluno_id
    assert len(client.get(f"{API}/analytics/evolution", headers=a["headers"]).json()) == 2


def test_evolucao_sem_dados_e_sem_aluno_id(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    assert client.get(f"{API}/analytics/evolution?aluno_id={a['user']['id']}", headers=p["headers"]).json() == []
    r = client.get(f"{API}/analytics/evolution", headers=p["headers"])
    assert r.status_code == 400  # o Personal precisa informar o aluno


def test_rnf03_evolucao_responde_em_ate_3_segundos(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    aid = a["user"]["id"]
    for i in range(5):  # 5 exercícios x 24 dias x 3 séries (cerca de 12 semanas de treino)
        _history(aid, f"Exercício carga {i}", [40 + k * 1.25 for k in range(24)])
    tempos = []
    for _ in range(5):
        t0 = time.perf_counter()
        r = client.get(f"{API}/analytics/evolution?aluno_id={aid}", headers=p["headers"])
        tempos.append(time.perf_counter() - t0)
        assert r.status_code == 200 and len(r.json()) == 5
    assert max(tempos) < 3.0, tempos


def test_rnf08_ciclo_da_catraca_dentro_de_1_segundo(client):
    p = make_personal(client)
    a = make_aluno(client, p)
    sid = schedule(client, p, a, 5).json()["id"]
    t0 = time.perf_counter()
    r = client.post(f"{API}/automacao/checkin", headers=a["headers"], json={"schedule_id": sid})
    total = time.perf_counter() - t0
    assert r.status_code == 200 and r.json()["granted"] is True
    assert r.json()["cycle_ms"] < 1000 and total < 1.0

    for cenario in ["valida", "invalida", "sem_aula", "fora_janela", "dupla"]:
        client.post(f"{API}/automacao/reset", headers=p["headers"], json={})
        ciclos = client.post(f"{API}/automacao/simulate", headers=p["headers"], json={"scenario": cenario}).json()["cycles"]
        assert ciclos and all(c["cycle_ms"] < 1000 for c in ciclos), cenario

    logs = client.get(f"{API}/automacao/logs?limit=200", headers=p["headers"]).json()
    assert any(l["cycle_ms"] is not None for l in logs)
