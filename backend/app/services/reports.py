"""Relatório consolidado de evolução do aluno em um período (datas no fuso de São Paulo)."""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.tz import day_bounds_utc, local_date, now_utc
from app.models import Progress, ReportNote, Schedule, User
from app.models.schedule import AGENDADO, CANCELADO, CHECKIN, CONCLUIDO
from app.services.analytics import exercise_series, stagnation_streak

STAGNANT_MIN_STREAK = 2


def _pt(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def build_report(db: Session, aluno: User, start: date, end: date) -> dict:
    personal = db.get(User, aluno.personal_id) if aluno.personal_id else None
    lo, hi = day_bounds_utc(start)[0], day_bounds_utc(end)[1]
    now = now_utc()

    # --- frequência (aulas) ---
    scheds = db.query(Schedule).filter(
        Schedule.aluno_id == aluno.id, Schedule.start_time >= lo, Schedule.start_time < hi
    ).all()
    realizadas = sum(1 for s in scheds if s.status in (CHECKIN, CONCLUIDO))
    canceladas = sum(1 for s in scheds if s.status == CANCELADO)
    faltas = sum(
        1 for s in scheds
        if s.status == AGENDADO and s.start_time + timedelta(minutes=s.duration_min) < now
    )
    pendentes = sum(
        1 for s in scheds
        if s.status == AGENDADO and s.start_time + timedelta(minutes=s.duration_min) >= now
    )
    base = realizadas + faltas
    presenca = round(realizadas / base * 100) if base else None

    # --- sessões de treino no período ---
    rows = db.query(Progress).filter(
        Progress.aluno_id == aluno.id, Progress.performed_at >= lo, Progress.performed_at < hi
    ).all()
    session_keys = {r.session_id or local_date(r.performed_at) for r in rows}
    sessions = len(session_keys)
    weeks = max(1.0, ((end - start).days + 1) / 7)

    # --- por exercício ---
    exercises, records, stagnant = [], [], []
    for ex_id, ex in exercise_series(db, aluno.id).items():
        pts_all = [p for p in ex["points"] if p["date"] <= end]
        pts = [p for p in pts_all if p["date"] >= start]
        if not pts:
            continue
        before = [p for p in pts_all if p["date"] < start]
        first, last = pts[0]["max_load"], pts[-1]["max_load"]
        max_load = max(p["max_load"] for p in pts)
        record = bool(before) and max_load > max(p["max_load"] for p in before)
        streak = stagnation_streak([p["max_load"] for p in pts_all])
        is_stagnant = len(pts_all) >= 3 and streak >= STAGNANT_MIN_STREAK
        item = {
            "exercise_id": ex_id,
            "exercise": ex["name"],
            "sessions": len(pts),
            "first_load": first,
            "last_load": last,
            "max_load": max_load,
            "avg_load": round(sum(p["avg_load"] for p in pts) / len(pts), 1),
            "progression_pct": round((last - first) / first * 100, 1) if first else 0.0,
            "total_volume": round(sum(p["volume"] for p in pts), 1),
            "record": record,
            "stagnant": is_stagnant,
            "streak": streak,
            "points": [{"date": p["date"].isoformat(), "max_load": p["max_load"], "avg_load": p["avg_load"]} for p in pts],
        }
        exercises.append(item)
        if record:
            records.append(ex["name"])
        if is_stagnant:
            stagnant.append({"exercise": ex["name"], "streak": streak, "load": last})
    exercises.sort(key=lambda e: -e["total_volume"])

    # --- volume semanal ---
    vol: dict[date, float] = {}
    w = _monday(start)
    while w <= end:
        vol[w] = 0.0
        w += timedelta(days=7)
    for r in rows:
        k = _monday(local_date(r.performed_at))
        vol[k] = vol.get(k, 0.0) + r.load_kg * r.reps
    weekly_volume = [{"week": k.isoformat(), "volume": round(v, 1)} for k, v in sorted(vol.items())]

    # --- resumo em texto (regras) ---
    first_name = aluno.name.split()[0]
    parts = []
    if sessions:
        parts.append(
            f"No período, {first_name} fez {sessions} sess{'ão' if sessions == 1 else 'ões'} de treino"
            + (f" e compareceu a {realizadas} de {base} aulas ({presenca}% de presença)." if base else ".")
        )
    else:
        parts.append(f"{first_name} não registrou treinos no período.")
    progressing = [e for e in exercises if e["progression_pct"] > 0 and e["sessions"] >= 2]
    if progressing:
        best = max(progressing, key=lambda e: e["progression_pct"])
        parts.append(f"{first_name} evoluiu {_pt(best['progression_pct'])}% de carga em {best['exercise']}.")
    if stagnant:
        top = max(stagnant, key=lambda s: s["streak"])
        parts.append(f"Sem recorde de carga em {top['exercise']} há {top['streak']} sessões; vale revisar a ficha.")
    if records:
        parts.append("Recordes pessoais em: " + ", ".join(records) + ".")
    if faltas:
        parts.append(f"{faltas} aula(s) agendada(s) sem comparecimento.")

    note = db.query(ReportNote).filter(ReportNote.aluno_id == aluno.id).first()
    return {
        "aluno": {"id": aluno.id, "name": aluno.name, "goal": aluno.goal},
        "personal": personal.name if personal else None,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "attendance": {
            "agendadas": len(scheds), "realizadas": realizadas, "canceladas": canceladas,
            "faltas": faltas, "pendentes": pendentes, "presenca_pct": presenca,
            "sessoes": sessions, "sessoes_por_semana": round(sessions / weeks, 1),
        },
        "exercises": exercises,
        "records": records,
        "stagnant": stagnant,
        "weekly_volume": weekly_volume,
        "summary_text": " ".join(parts),
        "note": {"text": note.text, "updated_at": note.updated_at} if note and note.text else None,
    }
