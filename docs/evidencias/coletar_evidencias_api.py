"""Coleta as evidências de RNF03 (tempo de resposta) e RNF08 (ciclo da catraca) contra a API em execução.

Uso (com a API no ar e SEED_DEMO=true):
    python docs/evidencias/coletar_evidencias_api.py [http://localhost:8000]
"""
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api/v1"
c = httpx.Client(timeout=30)


def login(email, pwd="trainup123"):
    r = c.post(f"{BASE}/auth/login", json={"email": email, "password": pwd})
    r.raise_for_status()
    d = r.json()
    return {"Authorization": f"Bearer {d['access_token']}"}, d["user"]


print(f"Coleta em {datetime.now().strftime('%d/%m/%Y %H:%M')} contra {BASE}\n")
ph, _ = login("personal@trainup.com")
ah, ana = login("aluno@trainup.com")

print("== RNF03 — tempo de resposta de GET /analytics/evolution (limite: 3 s) ==")
tempos = []
for i in range(1, 6):
    t0 = time.perf_counter()
    r = c.get(f"{BASE}/analytics/evolution", params={"aluno_id": ana["id"]}, headers=ph)
    ms = (time.perf_counter() - t0) * 1000
    tempos.append(ms)
    pontos = sum(len(e["points"]) for e in r.json())
    print(f"  chamada {i}: HTTP {r.status_code}, {len(r.json())} exercícios, {pontos} pontos, {ms:.1f} ms")
print(f"  média {statistics.mean(tempos):.1f} ms | máximo {max(tempos):.1f} ms | resultado: {'APROVADO' if max(tempos) < 3000 else 'REPROVADO'}\n")

print("== RNF08 — ciclo da catraca (limite: 1 s por ciclo) ==")
ciclos = []
for cen in ["valida", "invalida", "sem_aula", "fora_janela", "dupla"]:
    c.post(f"{BASE}/automacao/reset", headers=ph, json={})
    r = c.post(f"{BASE}/automacao/simulate", headers=ph, json={"scenario": cen})
    for cy in r.json()["cycles"]:
        ciclos.append(cy["cycle_ms"])
        print(f"  cenário {cen:<12} granted={str(cy['granted']):<5} motivo={str(cy['reason']):<32} cycle_ms={cy['cycle_ms']}")
c.post(f"{BASE}/automacao/reset", headers=ph, json={})
for minutos in (5, 2, 8, 11, 14, 1):  # dentro da janela de check-in (15 min antes do início); evita choque com a agenda do seed
    inicio = (datetime.now(timezone.utc) + timedelta(minutes=minutos)).isoformat()
    s = c.post(f"{BASE}/schedules", headers=ph, json={"aluno_id": ana["id"], "duration_min": 15, "start_time": inicio})
    if s.status_code == 201:
        break
sid = s.json()["id"]
t0 = time.perf_counter()
r = c.post(f"{BASE}/automacao/checkin", headers=ah, json={"schedule_id": sid}).json()
total = (time.perf_counter() - t0) * 1000
ciclos.append(r["cycle_ms"])
print(f"  check-in real      granted={r['granted']} transições={[t['state'] for t in r['transitions']]}")
print(f"                     cycle_ms={r['cycle_ms']} | tempo total da requisição {total:.1f} ms")
print(f"  ciclos medidos: {len(ciclos)} | máximo {max(ciclos)} ms | resultado: {'APROVADO' if max(ciclos) < 1000 else 'REPROVADO'}")
