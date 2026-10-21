"""Ciência de dados: evolução de carga, estagnação e dicas educativas."""
from statistics import mean

from sqlalchemy.orm import Session

from app.core.tz import local_date
from app.models import Exercise, Progress, User


def exercise_series(db: Session, aluno_id: int, exercise_id: int | None = None) -> dict[int, dict]:
    """Histórico completo: por exercício, uma lista de sessões (dia local) com carga média/máxima e volume."""
    q = (
        db.query(Progress, Exercise.name)
        .join(Exercise, Exercise.id == Progress.exercise_id)
        .filter(Progress.aluno_id == aluno_id)
        .order_by(Progress.performed_at)
    )
    if exercise_id:
        q = q.filter(Progress.exercise_id == exercise_id)

    grouped: dict[int, dict] = {}
    for p, name in q.all():
        ex = grouped.setdefault(p.exercise_id, {"name": name, "days": {}})
        ex["days"].setdefault(local_date(p.performed_at), []).append(p)

    out: dict[int, dict] = {}
    for ex_id, ex in grouped.items():
        points = []
        for day in sorted(ex["days"]):
            sets = ex["days"][day]
            loads = [s.load_kg for s in sets]
            points.append({
                "date": day,
                "avg_load": round(mean(loads), 1),
                "max_load": max(loads),
                "volume": round(sum(s.load_kg * s.reps for s in sets), 1),
                "sets": len(sets),
            })
        out[ex_id] = {"name": ex["name"], "points": points}
    return out


def evolution(db: Session, aluno_id: int, exercise_id: int | None = None) -> list[dict]:
    result = []
    for ex_id, ex in exercise_series(db, aluno_id, exercise_id).items():
        pts = [{**p, "date": p["date"].isoformat()} for p in ex["points"]]
        first, last = pts[0]["avg_load"], pts[-1]["avg_load"]
        result.append({
            "exercise_id": ex_id,
            "exercise": ex["name"],
            "points": pts,
            "progression_pct": round((last - first) / first * 100, 1) if first else 0.0,
        })
    return result


def stagnation_streak(max_loads: list[float]) -> int:
    """Quantas sessões se passaram desde o último recorde de carga (0 = bateu recorde agora)."""
    best, last_pr = float("-inf"), -1
    for i, m in enumerate(max_loads):
        if m > best:
            best, last_pr = m, i
    return len(max_loads) - 1 - last_pr if max_loads else 0


def stagnation(db: Session, aluno: User, n: int) -> list[dict]:
    """Alerta quando a carga máxima não sobe há pelo menos N-1 sessões do exercício."""
    alerts = []
    for ex in exercise_series(db, aluno.id).values():
        maxes = [p["max_load"] for p in ex["points"]]
        if len(maxes) < n:
            continue
        streak = stagnation_streak(maxes)
        if streak >= n - 1:
            alerts.append({
                "aluno_id": aluno.id,
                "aluno_name": aluno.name,
                "exercise": ex["name"],
                "sessions": streak,
                "current_load": maxes[-1],
                "message": (
                    f"{aluno.name} está sem recorde de carga em {ex['name']} há {streak} sessões "
                    f"(parado em {maxes[-1]:g} kg). Considere ajustar a ficha."
                ),
            })
    return sorted(alerts, key=lambda a: -a["sessions"])


TIPS = {
    "ganho_massa": [
        ("Proteína em todas as refeições", "Distribua fontes como ovos, carnes, laticínios e leguminosas ao longo do dia."),
        ("Sono de qualidade", "A maior parte da recuperação muscular acontece dormindo: mire em 7 a 9 horas."),
        ("Progrida com consistência", "Pequenos aumentos de carga e boa técnica rendem mais que treinos esporádicos."),
    ],
    "emagrecimento": [
        ("Prato equilibrado", "Priorize vegetais, proteínas e alimentos pouco processados; evite cortes extremos."),
        ("Hidratação", "Beber água ao longo do dia ajuda no desempenho e na saciedade."),
        ("Movimento diário", "Caminhadas leves nos dias sem treino somam bastante ao longo da semana."),
    ],
    "resistencia": [
        ("Carboidratos antes de treinos longos", "Uma refeição leve 2 a 3 horas antes ajuda a sustentar o esforço."),
        ("Reposição de líquidos", "Em treinos longos ou no calor, leve água e reponha ao longo da sessão."),
        ("Descanso ativo", "Alongamento leve e caminhada ajudam a recuperar entre sessões intensas."),
    ],
    "saude": [
        ("Rotina possível", "Treinar 3 vezes por semana de forma regular vale mais que treinos intensos e raros."),
        ("Alimentação variada", "Frutas, verduras e grãos integrais fazem parte de uma rotina sustentável."),
        ("Pausas e sono", "Dormir bem e administrar o estresse melhoram o resultado dos treinos."),
    ],
}
AVISO = (
    "Conteúdo educativo geral. Para um plano alimentar ou qualquer suplementação, "
    "procure um nutricionista ou médico."
)


def tips(goal: str | None) -> dict:
    key = goal if goal in TIPS else "saude"
    return {
        "goal": key,
        "dicas": [{"titulo": t, "texto": x} for t, x in TIPS[key]],
        "aviso": AVISO,
    }
