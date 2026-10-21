"""Resumo de uma sessão de treino: volume, comparação com a sessão anterior e recordes."""
from sqlalchemy.orm import Session

from app.models import Exercise, Progress, Workout, WorkoutSession


def _volume(rows) -> float:
    return round(sum(r.load_kg * r.reps for r in rows), 1)


def session_summary(db: Session, s: WorkoutSession) -> dict:
    rows = db.query(Progress).filter(Progress.session_id == s.id).order_by(Progress.id).all()
    names = {e.id: e.name for e in db.query(Exercise).filter(Exercise.id.in_({r.exercise_id for r in rows}))} if rows else {}

    by_ex: dict[int, list] = {}
    for r in rows:
        by_ex.setdefault(r.exercise_id, []).append(r)

    exercises, records = [], []
    for ex_id, sets in by_ex.items():
        prev = (
            db.query(Progress.load_kg)
            .filter(Progress.aluno_id == s.aluno_id, Progress.exercise_id == ex_id, Progress.performed_at < s.started_at)
            .order_by(Progress.load_kg.desc())
            .first()
        )
        prev_max = prev[0] if prev else None
        max_load = max(r.load_kg for r in sets)
        record = prev_max is not None and max_load > prev_max
        if record:
            records.append(names[ex_id])
        exercises.append({
            "exercise_id": ex_id, "exercise": names[ex_id], "sets": len(sets),
            "volume": _volume(sets), "max_load": max_load, "previous_max": prev_max, "record": record,
        })

    total_volume = _volume(rows)
    previous_volume, delta = None, None
    q = db.query(WorkoutSession).filter(
        WorkoutSession.aluno_id == s.aluno_id, WorkoutSession.finished_at.isnot(None),
        WorkoutSession.started_at < s.started_at, WorkoutSession.id != s.id,
    )
    if s.workout_id:
        q = q.filter(WorkoutSession.workout_id == s.workout_id)
    prev_session = q.order_by(WorkoutSession.started_at.desc()).first()
    if prev_session:
        prev_rows = db.query(Progress).filter(Progress.session_id == prev_session.id).all()
        previous_volume = _volume(prev_rows)
        if previous_volume:
            delta = round((total_volume - previous_volume) / previous_volume * 100, 1)

    workout = db.get(Workout, s.workout_id) if s.workout_id else None
    duration = None
    if s.finished_at:
        duration = max(1, round((s.finished_at - s.started_at).total_seconds() / 60))
    return {
        "session_id": s.id,
        "workout_id": s.workout_id,
        "workout_name": workout.name if workout else "Treino livre",
        "started_at": s.started_at,
        "finished_at": s.finished_at,
        "duration_min": duration,
        "total_sets": len(rows),
        "total_volume": total_volume,
        "previous_volume": previous_volume,
        "volume_delta_pct": delta,
        "exercises": exercises,
        "records": records,
    }
