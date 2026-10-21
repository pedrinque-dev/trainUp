"""Dados base (catálogo, catracas) e de demonstração (personal, alunos, históricos de 8 a 12 semanas)."""
import random
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.tz import local_to_utc, now_utc, today_local
from app.models import (AccessLog, Exercise, LinkRequest, Progress, ReportNote, Schedule, Turnstile, User,
                        Workout, WorkoutItem, WorkoutSession)

DEMO_PASSWORD = "trainup123"

CATALOG = [
    ("Supino reto", "Peito", "Deitado no banco, desça a barra até o peito e empurre sem tirar os glúteos do banco."),
    ("Supino inclinado com halteres", "Peito", "Banco inclinado a 30°; suba os halteres em arco, controlando a descida."),
    ("Crucifixo com halteres", "Peito", "Braços levemente flexionados; abra em arco até sentir o alongamento do peitoral."),
    ("Flexão de braço", "Peito", "Corpo alinhado, mãos na largura dos ombros; desça até o peito quase tocar o chão."),
    ("Crossover na polia", "Peito", "Puxe os cabos à frente do corpo em arco, contraindo o peitoral no final."),
    ("Remada curvada", "Costas", "Tronco inclinado e coluna neutra; puxe a barra em direção ao abdômen."),
    ("Puxada frontal", "Costas", "Puxe a barra até a altura do queixo, levando os cotovelos para baixo e para trás."),
    ("Remada baixa no cabo", "Costas", "Sentado, puxe o cabo até o abdômen mantendo o tronco estável."),
    ("Barra fixa", "Costas", "Pegada na largura dos ombros; suba até o queixo passar da barra, sem balançar."),
    ("Levantamento terra", "Costas", "Barra rente às pernas, coluna neutra; estenda quadris e joelhos juntos."),
    ("Agachamento livre", "Pernas", "Pés na largura dos ombros; desça com o tronco firme até a coxa ficar paralela ao chão."),
    ("Leg press 45°", "Pernas", "Pés na plataforma na largura dos ombros; desça controlando sem descolar o quadril."),
    ("Cadeira extensora", "Pernas", "Estenda os joelhos sem travar no topo; desça devagar."),
    ("Mesa flexora", "Pernas", "Deitado, flexione os joelhos levando o calcanhar em direção ao glúteo."),
    ("Afundo (passada)", "Pernas", "Dê um passo à frente e desça até o joelho de trás quase tocar o chão."),
    ("Stiff", "Pernas", "Joelhos levemente flexionados; leve o quadril para trás descendo a barra rente às pernas."),
    ("Elevação pélvica", "Pernas", "Costas apoiadas no banco; suba o quadril contraindo os glúteos no topo."),
    ("Panturrilha em pé", "Pernas", "Suba na ponta dos pés o máximo possível e desça alongando a panturrilha."),
    ("Desenvolvimento com halteres", "Ombros", "Sentado, empurre os halteres acima da cabeça sem arquear a lombar."),
    ("Elevação lateral", "Ombros", "Eleve os halteres até a altura dos ombros com cotovelos levemente flexionados."),
    ("Elevação frontal", "Ombros", "Eleve o haltere à frente até a altura dos ombros, sem balançar o tronco."),
    ("Remada alta", "Ombros", "Puxe a barra rente ao corpo até o peito, cotovelos acima das mãos."),
    ("Face pull", "Ombros", "Puxe a corda em direção ao rosto, abrindo os cotovelos e contraindo as escápulas."),
    ("Rosca direta", "Bíceps", "Cotovelos junto ao corpo; flexione sem balançar o tronco."),
    ("Rosca alternada", "Bíceps", "Alterne os braços girando o punho (supinação) durante a subida."),
    ("Rosca martelo", "Bíceps", "Pegada neutra (palmas para dentro); flexione sem mover os cotovelos."),
    ("Tríceps pulley", "Tríceps", "Cotovelos fixos ao lado do corpo; estenda os braços para baixo."),
    ("Tríceps testa", "Tríceps", "Deitado, flexione apenas os cotovelos levando a barra em direção à testa."),
    ("Mergulho no banco", "Tríceps", "Mãos no banco atrás do corpo; desça flexionando os cotovelos e suba."),
    ("Prancha abdominal", "Core", "Apoie antebraços e pontas dos pés; mantenha o corpo alinhado e o abdômen contraído."),
    ("Abdominal crunch", "Core", "Eleve ombros e escápulas do chão contraindo o abdômen, sem puxar o pescoço."),
    ("Esteira (caminhada inclinada)", "Cardio", "Caminhada com inclinação moderada em ritmo constante, postura ereta."),
]


def ensure_base_data(db: Session) -> None:
    if not db.query(Exercise).filter(Exercise.owner_id.is_(None)).count():
        db.add_all(Exercise(name=n, muscle_group=g, description=d) for n, g, d in CATALOG)
    if not db.query(Turnstile).count():
        db.add_all([
            Turnstile(name="Catraca 01", location="Unidade Centro · Entrada principal"),
            Turnstile(name="Catraca 02", location="Unidade Zona Sul · Entrada principal"),
        ])
    db.commit()


# nome, email, objetivo, perfil, semanas, prob. de faltar, passo semanal de carga
ALUNOS = [
    ("Ana Souza", "aluno@trainup.com", "ganho_massa", "evolui", 12, 0.05, 0.025),
    ("Bruno Lima", "bruno@trainup.com", "ganho_massa", "estagnado", 12, 0.10, 0.03),
    ("Carla Mendes", "carla@trainup.com", "emagrecimento", "irregular", 10, 0.55, 0.012),
    ("Diego Ramos", "diego@trainup.com", "saude", "moderado", 12, 0.15, 0.02),
    ("Elisa Prado", "elisa@trainup.com", "resistencia", "evolui", 8, 0.05, 0.035),
]
BASE_LOADS = {
    "Supino reto": 40, "Remada curvada": 35, "Desenvolvimento com halteres": 14, "Rosca direta": 15,
    "Agachamento livre": 60, "Leg press 45°": 140, "Stiff": 40, "Elevação pélvica": 60,
}
WORKOUTS = {
    "Treino A · Superiores": ["Supino reto", "Remada curvada", "Desenvolvimento com halteres", "Rosca direta"],
    "Treino B · Inferiores": ["Agachamento livre", "Leg press 45°", "Stiff", "Elevação pélvica"],
}


def _load(base: float, week: int, profile: str, step: float, factor: float) -> float:
    w = min(week, 5) if profile == "estagnado" else week
    return round(base * factor * (1 + step * w) * 4) / 4


def seed(db: Session) -> None:
    ensure_base_data(db)
    if db.query(User).count():
        return
    rng = random.Random(42)
    ex = {e.name: e for e in db.query(Exercise).filter(Exercise.owner_id.is_(None))}

    personal = User(name="Carlos Personal", email="personal@trainup.com", role="personal",
                    hashed_password=hash_password(DEMO_PASSWORD), invite_code="TRAIN123")
    db.add(personal)
    db.flush()

    today = today_local()
    monday = today - timedelta(days=today.weekday())
    now = now_utc()
    turnstile = db.query(Turnstile).order_by(Turnstile.id).first()
    alunos: list[User] = []

    for idx, (name, email, goal, profile, weeks, skip, step) in enumerate(ALUNOS):
        a = User(name=name, email=email, role="aluno", goal=goal, personal_id=personal.id,
                 hashed_password=hash_password(DEMO_PASSWORD))
        db.add(a)
        db.flush()
        alunos.append(a)
        factor = 0.85 + 0.1 * idx
        ws: list[Workout] = []
        for wname, names in WORKOUTS.items():
            w = Workout(name=wname, personal_id=personal.id, aluno_id=a.id, weekday=None, items=[
                WorkoutItem(exercise_id=ex[n].id, sets=3, reps=10 if "Superiores" in wname else 12,
                            target_load=_load(BASE_LOADS[n], weeks - 1, profile, step, factor)) for n in names])
            db.add(w)
            ws.append(w)
        db.flush()

        # histórico de treinos (sessões + séries)
        k = 0
        for week in range(weeks - 1, -1, -1):
            wk_idx = weeks - 1 - week
            for off in (0, 2, 4):
                d = monday - timedelta(weeks=week) + timedelta(days=off)
                if d > today or rng.random() < skip:
                    continue
                w = ws[k % 2]
                k += 1
                start = local_to_utc(d, 18, 5 * idx)
                s = WorkoutSession(aluno_id=a.id, workout_id=w.id, started_at=start, finished_at=start + timedelta(minutes=55))
                db.add(s)
                db.flush()
                t = 0
                for item in w.items:
                    base = BASE_LOADS[item.exercise.name]
                    load = _load(base, wk_idx, profile, step, factor)
                    for sn in range(1, item.sets + 1):
                        db.add(Progress(aluno_id=a.id, exercise_id=item.exercise_id, workout_id=w.id, session_id=s.id,
                                        set_number=sn, reps=item.reps - (1 if sn == item.sets else 0), load_kg=load,
                                        performed_at=start + timedelta(minutes=t)))
                        t += 3

        # aulas com o personal: passadas, hoje e futuras
        slot_day, slot_hour = idx % 5, 7 + idx * 2
        for week in range(weeks, 0, -1):
            d = monday - timedelta(weeks=week) + timedelta(days=slot_day)
            r = rng.random()
            if profile == "irregular":
                status = "CONCLUIDO" if r < 0.4 else "CANCELADO" if r < 0.7 else "AGENDADO"
            else:
                status = "CANCELADO" if r < 0.08 else "CONCLUIDO"
            st = local_to_utc(d, slot_hour)
            db.add(Schedule(personal_id=personal.id, aluno_id=a.id, start_time=st, duration_min=60, status=status,
                            checkin_at=st - timedelta(minutes=5) if status == "CONCLUIDO" else None))
        for week in (1, 2):
            d = monday + timedelta(weeks=week, days=slot_day)
            db.add(Schedule(personal_id=personal.id, aluno_id=a.id, start_time=local_to_utc(d, slot_hour), duration_min=60))

    # aulas de hoje (para a demonstração do check-in)
    for a, mins in ((alunos[0], 20), (alunos[1], 100)):
        st = (now + timedelta(minutes=mins)).replace(second=0, microsecond=0)
        db.add(Schedule(personal_id=personal.id, aluno_id=a.id, start_time=st, duration_min=60))

    # solicitação de vínculo pendente (demonstra o fluxo de aprovação)
    fabio = User(name="Fábio Torres", email="fabio@trainup.com", role="aluno", goal="ganho_massa",
                 hashed_password=hash_password(DEMO_PASSWORD))
    db.add(fabio)
    db.flush()
    db.add(LinkRequest(aluno_id=fabio.id, personal_id=personal.id))

    db.add(ReportNote(
        aluno_id=alunos[1].id, personal_id=personal.id,
        text="Bruno estabilizou as cargas há várias semanas. Sugiro uma semana de deload (70% das cargas) "
             "e depois trocar a ordem dos exercícios e variar o intervalo de repetições.",
    ))

    # histórico da catraca (para os contadores do painel SCADA)
    reasons = [(True, "ok", "valida"), (True, "ok", "valida"), (False, "fora da janela: cedo demais", "fora_janela"),
               (False, "credencial não reconhecida", "invalida"), (False, "sem agendamento para este aluno", "sem_aula")]
    for i in range(18):
        granted, reason, scen = reasons[i % len(reasons)]
        a = alunos[i % len(alunos)]
        when = now - timedelta(hours=i * 3 + 1)
        db.add(AccessLog(turnstile_id=turnstile.id, aluno_id=None if scen == "invalida" else a.id,
                         personal_id=personal.id, event="TENTATIVA", granted=granted, reason=reason,
                         scenario=scen, simulated=True, cycle_ms=rng.randint(2, 14), created_at=when,
                         detail="SENSOR   I0.0 leitura de credencial\nCLP      validação concluída\nSCADA    evento registrado"))
    db.commit()
