"""Simulação de automação industrial: catraca controlada por uma máquina de estados.

Ciclo: SENSOR (leitura de credencial) -> CLP (lógica de validação) -> ATUADOR (trava/LEDs) -> SCADA (registro).
O estado fica persistido no banco (tabela turnstiles), então funciona com mais de um worker/instância
e permite várias catracas (unidades).
"""
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.tz import day_bounds_utc, fmt_local, now_utc, today_local
from app.models import AccessLog, Schedule, Turnstile, User
from app.models.schedule import AGENDADO, CHECKIN

TRAVADA, VALIDANDO, LIBERADA, AGUARDANDO, BLOQUEIO = (
    "TRAVADA", "VALIDANDO", "LIBERADA", "AGUARDANDO_PASSAGEM", "BLOQUEIO",
)

TRANSITIONS: dict[str, set[str]] = {
    TRAVADA: {VALIDANDO, BLOQUEIO},
    VALIDANDO: {LIBERADA, TRAVADA},
    LIBERADA: {AGUARDANDO},
    AGUARDANDO: {TRAVADA},
    BLOQUEIO: {TRAVADA},
}
COLORS = {TRAVADA: "VERMELHO", VALIDANDO: "AMARELO", LIBERADA: "VERDE", AGUARDANDO: "VERDE", BLOQUEIO: "VERMELHO"}


class InvalidTransition(Exception):
    pass


class TurnstileFSM:
    """Aplica transições validadas e registra o rastro (trace) de cada uma."""

    def __init__(self, t: Turnstile):
        self.t = t
        self.trace: list[dict] = []
        self._t0 = time.perf_counter()

    def go(self, new: str, why: str = "") -> None:
        if new not in TRANSITIONS[self.t.state]:
            raise InvalidTransition(f"{self.t.state} -> {new}")
        old = self.t.state
        self.t.state, self.t.state_since = new, now_utc()
        self.trace.append({"from": old, "state": new, "t_ms": int((time.perf_counter() - self._t0) * 1000), "why": why})


@dataclass
class Booking:
    """Visão unificada de um agendamento (real ou simulado)."""
    start: datetime
    duration: int
    status: str
    row: Schedule | None = None
    simulated: bool = False

    @property
    def id(self) -> int | None:
        return self.row.id if self.row else None


def get_turnstile(db: Session, turnstile_id: int | None) -> Turnstile | None:
    q = db.query(Turnstile)
    return db.get(Turnstile, turnstile_id) if turnstile_id else q.order_by(Turnstile.id).first()


def personal_of(db: Session, aluno_id: int | None) -> int | None:
    """Personal responsável pelo aluno (None se não houver)."""
    if not aluno_id:
        return None
    a = db.get(User, aluno_id)
    return a.personal_id if a else None


def refresh(db: Session, t: Turnstile) -> Turnstile:
    """Transições por tempo: religamento sem passagem e rearme após bloqueio."""
    now = now_utc()
    if t.state == AGUARDANDO and t.unlock_until and now >= t.unlock_until:
        TurnstileFSM(t).go(TRAVADA, "timeout")
        t.unlock_until = None
        db.add(AccessLog(turnstile_id=t.id, aluno_id=t.last_aluno_id, personal_id=personal_of(db, t.last_aluno_id),
                         event="TIMEOUT", reason="sem passagem: religamento automático",
                         detail=f"TIMER    tempo de passagem esgotado; trava religada ({settings.CATRACA_OPEN_SECONDS}s)"))
        db.commit()
    if t.state == BLOQUEIO and t.blocked_until and now >= t.blocked_until:
        TurnstileFSM(t).go(TRAVADA, "rearme automático")
        t.blocked_until, t.consecutive_denials = None, 0
        db.add(AccessLog(turnstile_id=t.id, event="RESET", reason="rearme automático após bloqueio",
                         detail="TIMER    período de bloqueio encerrado; catraca rearmada"))
        db.commit()
    return t


def io_map(state: str) -> list[dict]:
    """Entradas (I) e saídas (Q) como num CLP."""
    return [
        {"tag": "I0.0", "label": "Sensor de credencial (leitor)", "value": state == VALIDANDO},
        {"tag": "I0.1", "label": "Sensor de passagem (óptico)", "value": False},
        {"tag": "I0.2", "label": "Botão de rearme do supervisor", "value": False},
        {"tag": "Q0.0", "label": "Solenoide da trava", "value": state in (LIBERADA, AGUARDANDO)},
        {"tag": "Q0.1", "label": "LED verde", "value": state in (LIBERADA, AGUARDANDO)},
        {"tag": "Q0.2", "label": "LED vermelho", "value": state in (TRAVADA, BLOQUEIO)},
        {"tag": "Q0.3", "label": "LED amarelo", "value": state == VALIDANDO},
        {"tag": "Q0.4", "label": "Sirene de alarme", "value": state == BLOQUEIO},
    ]


def snapshot(t: Turnstile) -> dict:
    now = now_utc()
    until = t.unlock_until if t.state == AGUARDANDO else t.blocked_until if t.state == BLOQUEIO else None
    left = max(0, int((until - now).total_seconds())) if until else 0
    return {
        "id": t.id, "name": t.name, "location": t.location, "state": t.state, "color": COLORS[t.state],
        "seconds_left": left, "denials": t.consecutive_denials, "max_denials": settings.CATRACA_MAX_DENIALS,
        "state_since": t.state_since, "io": io_map(t.state),
    }


def _validate(cred_aluno: User | None, b: Booking | None, now: datetime) -> tuple[str | None, str | None]:
    """Lógica do CLP. Devolve (motivo_da_negativa | None, linha_de_log_da_janela)."""
    if cred_aluno is None:
        return "credencial não reconhecida", None
    if b is None:
        return "sem agendamento para este aluno", None
    window = None
    opens = b.start - timedelta(minutes=settings.CHECKIN_EARLY_MIN)
    closes = b.start + timedelta(minutes=b.duration)
    window = f"janela de acesso: {fmt_local(opens, '%d/%m %H:%M')} até {fmt_local(closes, '%d/%m %H:%M')}"
    if b.status == CHECKIN:
        return "check-in já realizado para esta aula (anti-fraude)", window
    if b.status != AGENDADO:
        return f"agendamento com status {b.status}", window
    if now < opens:
        return f"fora da janela: cedo demais (libera às {fmt_local(opens, '%H:%M')})", window
    if now > closes:
        return "fora da janela: aula já encerrada", window
    return None, window


def run_cycle(db: Session, t: Turnstile, cred_aluno: User | None, booking: Booking | None, *,
              credential_label: str, scenario: str | None = None, simulated: bool = False,
              acting_personal_id: int | None = None) -> dict:
    refresh(db, t)
    t0 = time.perf_counter()
    fsm = TurnstileFSM(t)
    lines: list[str] = []

    def step(comp: str, msg: str) -> None:
        lines.append(f"[{int((time.perf_counter() - t0) * 1000):04d}ms] {comp:<7} {msg}")

    now = now_utc()
    step("SENSOR", f"I0.0 leitura de credencial: {credential_label}")
    reason: str | None = None
    window: str | None = None

    if t.state == BLOQUEIO:
        reason = "catraca em BLOQUEIO (aguardando rearme do supervisor)"
        step("CLP", f"estado BLOQUEIO: leitura ignorada, sirene Q0.4 ligada")
    else:
        if t.state in (LIBERADA, AGUARDANDO):
            fsm.go(TRAVADA, "novo ciclo encerra a espera anterior")
            t.unlock_until = None
            step("CLP", "novo ciclo: espera de passagem anterior encerrada")
        fsm.go(VALIDANDO, "credencial lida")
        step("CLP", "TRAVADA -> VALIDANDO (LED amarelo Q0.3)")
        reason, window = _validate(cred_aluno, booking, now)
        if window:
            step("CLP", window)
        t.last_aluno_id = cred_aluno.id if cred_aluno else None

    granted = reason is None
    event = "TENTATIVA"
    if granted:
        fsm.go(LIBERADA, "agendamento válido")
        step("CLP", "agendamento válido e dentro da janela")
        step("ATUADOR", "VALIDANDO -> LIBERADA: solenoide Q0.0 energizado, LED verde Q0.1")
        fsm.go(AGUARDANDO, "aguardando passagem")
        t.unlock_until = now + timedelta(seconds=settings.CATRACA_OPEN_SECONDS)
        t.consecutive_denials = 0
        step("TIMER", f"LIBERADA -> AGUARDANDO_PASSAGEM; religamento em {settings.CATRACA_OPEN_SECONDS}s")
        if booking:
            booking.status = CHECKIN
            if booking.row is not None:
                booking.row.status, booking.row.checkin_at = CHECKIN, now
    elif t.state == VALIDANDO:
        fsm.go(TRAVADA, reason)
        t.consecutive_denials += 1
        step("CLP", f"acesso negado: {reason}")
        step("ATUADOR", f"VALIDANDO -> TRAVADA: LED vermelho Q0.2 ({t.consecutive_denials}/{settings.CATRACA_MAX_DENIALS} negativas seguidas)")
        if t.consecutive_denials >= settings.CATRACA_MAX_DENIALS:
            fsm.go(BLOQUEIO, "limite de negativas seguidas")
            t.blocked_until = now + timedelta(seconds=settings.CATRACA_BLOCK_SECONDS)
            event = "BLOQUEIO"
            step("ALARME", f"TRAVADA -> BLOQUEIO: sirene Q0.4 ligada por {settings.CATRACA_BLOCK_SECONDS}s ou até rearme")
    else:
        step("ATUADOR", "catraca mantida em BLOQUEIO")

    cycle_ms = int((time.perf_counter() - t0) * 1000)
    step("SCADA", f"evento registrado; ciclo concluído em {cycle_ms}ms")
    aluno_id = cred_aluno.id if cred_aluno else None
    db.add(AccessLog(
        turnstile_id=t.id, aluno_id=aluno_id,
        personal_id=acting_personal_id or personal_of(db, aluno_id),
        schedule_id=booking.id if booking else None, event=event, granted=granted,
        reason=reason or "ok", scenario=scenario, simulated=simulated, cycle_ms=cycle_ms,
        detail="\n".join(lines),
    ))
    db.commit()
    return {
        "granted": granted, "reason": reason, "event": event, "scenario": scenario,
        "cycle_ms": cycle_ms, "log": lines, "transitions": fsm.trace, "turnstile": snapshot(t),
    }


def confirm_passage(db: Session, t: Turnstile, personal_id: int | None = None) -> dict:
    refresh(db, t)
    if t.state != AGUARDANDO:
        raise InvalidTransition("nenhuma passagem pendente")
    fsm = TurnstileFSM(t)
    fsm.go(TRAVADA, "passagem confirmada")
    t.unlock_until = None
    db.add(AccessLog(turnstile_id=t.id, aluno_id=t.last_aluno_id,
                     personal_id=personal_id or personal_of(db, t.last_aluno_id),
                     event="PASSAGEM", reason="passagem confirmada pelo sensor I0.1",
                     detail="SENSOR   I0.1 passagem detectada\nATUADOR  AGUARDANDO_PASSAGEM -> TRAVADA: trava religada"))
    db.commit()
    return {"turnstile": snapshot(t), "transitions": fsm.trace}


def reset(db: Session, t: Turnstile, personal_id: int) -> dict:
    if t.state != BLOQUEIO:
        raise InvalidTransition("a catraca não está em BLOQUEIO")
    fsm = TurnstileFSM(t)
    fsm.go(TRAVADA, "rearme manual")
    t.blocked_until, t.consecutive_denials = None, 0
    db.add(AccessLog(turnstile_id=t.id, personal_id=personal_id, event="RESET", reason="rearme manual pelo supervisor",
                     detail="SENSOR   I0.2 botão de rearme acionado\nATUADOR  BLOQUEIO -> TRAVADA: sirene desligada"))
    db.commit()
    return {"turnstile": snapshot(t), "transitions": fsm.trace}


def simulate(db: Session, t: Turnstile, scenario: str, aluno: User, personal_id: int) -> list[dict]:
    """Cenários de teste sem depender de dados preparados."""
    now = now_utc()
    label = f"aluno#{aluno.id} ({aluno.name})"
    kw = dict(scenario=scenario, simulated=True, acting_personal_id=personal_id)
    valid = lambda: Booking(start=now, duration=60, status=AGENDADO, simulated=True)

    if scenario == "invalida":
        return [run_cycle(db, t, None, None, credential_label="CRED-0000 (desconhecida)", **kw)]
    if scenario == "sem_aula":
        return [run_cycle(db, t, aluno, None, credential_label=label, **kw)]
    if scenario == "fora_janela":
        b = Booking(start=now + timedelta(hours=3), duration=60, status=AGENDADO, simulated=True)
        return [run_cycle(db, t, aluno, b, credential_label=label, **kw)]
    b = valid()
    first = run_cycle(db, t, aluno, b, credential_label=label, **kw)
    if scenario == "valida":
        return [first]
    return [first, run_cycle(db, t, aluno, b, credential_label=label + " (2ª leitura)", **kw)]  # dupla


def stats_today(db: Session, personal_id: int, turnstile_id: int) -> dict:
    lo, hi = day_bounds_utc(today_local())
    rows = db.query(AccessLog).filter(
        AccessLog.personal_id == personal_id, AccessLog.turnstile_id == turnstile_id,
        AccessLog.event.in_(["TENTATIVA", "BLOQUEIO"]), AccessLog.created_at >= lo, AccessLog.created_at < hi,
    ).all()
    cycles = [r.cycle_ms for r in rows if r.cycle_ms is not None]
    return {
        "permitidos": sum(1 for r in rows if r.granted),
        "negados": sum(1 for r in rows if r.granted is False),
        "ciclo_medio_ms": round(sum(cycles) / len(cycles), 1) if cycles else None,
    }
