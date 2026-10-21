import { useCallback, useEffect, useRef, useState } from "react";
import { Activity, CheckCircle2, Gauge, Play, RotateCcw, ShieldAlert, XCircle } from "lucide-react";
import { useToast } from "../components/Toast";
import { Badge, Card, ErrorState, PageHeader, Tabs } from "../components/ui";
import { fmtTimeSec, num } from "../lib/format";
import { useInterval } from "../lib/hooks";
import api, { errMsg } from "../services/api";

const STATE_LOOK = {
  TRAVADA: { lamp: "red", label: "TRAVADA", text: "Trava energizada: acesso bloqueado" },
  VALIDANDO: { lamp: "yellow", label: "VALIDANDO", text: "CLP validando a credencial" },
  LIBERADA: { lamp: "green", label: "LIBERADA", text: "Solenoide acionado" },
  AGUARDANDO_PASSAGEM: { lamp: "green", label: "AGUARDANDO PASSAGEM", text: "Trava livre; aguardando o sensor de passagem" },
  BLOQUEIO: { lamp: "red", label: "BLOQUEIO", text: "Alarme: negativas seguidas" },
};
const ioFor = (s) => ({
  "I0.0": s === "VALIDANDO", "I0.1": false, "I0.2": false,
  "Q0.0": s === "LIBERADA" || s === "AGUARDANDO_PASSAGEM", "Q0.1": s === "LIBERADA" || s === "AGUARDANDO_PASSAGEM",
  "Q0.2": s === "TRAVADA" || s === "BLOQUEIO", "Q0.3": s === "VALIDANDO", "Q0.4": s === "BLOQUEIO",
});
const IO_LABELS = [
  ["I0.0", "Sensor de credencial (leitor)"], ["I0.1", "Sensor de passagem (óptico)"], ["I0.2", "Botão de rearme do supervisor"],
  ["Q0.0", "Solenoide da trava"], ["Q0.1", "LED verde"], ["Q0.2", "LED vermelho"], ["Q0.3", "LED amarelo"], ["Q0.4", "Sirene de alarme"],
];
const SCENARIOS = [
  { id: "valida", label: "Credencial válida", desc: "Aluno com aula agora" },
  { id: "invalida", label: "Credencial inválida", desc: "Cartão desconhecido" },
  { id: "sem_aula", label: "Aluno sem aula", desc: "Credencial ok, sem agendamento" },
  { id: "fora_janela", label: "Fora da janela", desc: "Aula daqui a 3 horas" },
  { id: "dupla", label: "Tentativa dupla", desc: "Mesma aula lida duas vezes" },
];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function Lamp({ color, size = "h-9 w-9" }) {
  const on = { red: "bg-red-500 shadow-[0_0_22px_6px_rgba(239,68,68,.55)]", yellow: "bg-amber-400 shadow-[0_0_22px_6px_rgba(251,191,36,.55)]", green: "bg-accent shadow-[0_0_22px_6px_rgba(155,214,74,.6)]" };
  return (
    <div className="flex flex-col gap-2 rounded-2xl bg-black/30 p-3" role="img" aria-label={`Sinaleiro ${color}`}>
      {["red", "yellow", "green"].map((c) => <span key={c} className={`${size} rounded-full transition ${color === c ? on[c] : "bg-white/10"}`} />)}
    </div>
  );
}

function Led({ on, tone = "green" }) {
  const c = on ? (tone === "red" ? "bg-red-500" : tone === "yellow" ? "bg-amber-400" : "bg-accent") : "bg-line";
  return <span className={`inline-block h-3 w-3 rounded-full ${c}`} aria-hidden="true" />;
}

/* ---------- Supervisório ---------- */
function Supervisorio({ turnstiles, tid, setTid }) {
  const toast = useToast();
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [view, setView] = useState(null);
  const [cycles, setCycles] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const playing = useRef(false);

  const refresh = useCallback(async () => {
    if (!tid) return;
    try {
      const [s, l] = await Promise.all([api.get("/automacao/status", { params: { turnstile_id: tid } }), api.get("/automacao/logs", { params: { turnstile_id: tid, limit: 40 } })]);
      setStatus(s.data); setLogs(l.data); setErr(null);
    } catch (e) { setErr(errMsg(e)); }
  }, [tid]);
  useEffect(() => { setStatus(null); refresh(); }, [refresh]);
  useInterval(refresh, 2000);

  async function play(cs) {
    playing.current = true;
    for (const c of cs) for (const tr of c.transitions) { setView(tr.state); await sleep(550); }
    setView(null); playing.current = false; refresh();
  }
  async function simulate(scenario) {
    setBusy(true);
    try { const { data } = await api.post("/automacao/simulate", { scenario, turnstile_id: tid }); setCycles(data.cycles); await play(data.cycles); }
    catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  }
  async function act(path, ok) {
    try { const { data } = await api.post(path, { turnstile_id: tid }); await play(data.transitions || []); toast(ok); }
    catch (e) { toast(errMsg(e), "error"); }
  }

  const t = status?.turnstile;
  const state = view || t?.state || "TRAVADA";
  const look = STATE_LOOK[state];
  const io = view || !t ? ioFor(state) : Object.fromEntries(t.io.map((x) => [x.tag, x.value]));
  const stats = status?.stats;

  return (
    <div className="space-y-5">
      {err && <ErrorState message={err} onRetry={refresh} />}
      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-5">
          <section className="rounded-3xl bg-ink p-5 text-white sm:p-6" aria-label="Estado da catraca">
            <div className="flex flex-wrap items-center gap-2">
              {turnstiles.map((x) => (
                <button key={x.id} onClick={() => setTid(x.id)} aria-pressed={tid === x.id}
                  className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${tid === x.id ? "bg-white text-ink" : "bg-white/10 text-white/80 hover:bg-white/15"}`}>{x.name}</button>
              ))}
              <span className="ml-auto text-xs text-white/60">{t?.location}</span>
            </div>
            <div className="mt-5 flex items-center gap-6">
              <Lamp color={look.lamp} />
              <div className="min-w-0">
                <p className="text-xs font-semibold text-white/60">Estado</p>
                <p className="text-3xl font-extrabold leading-tight sm:text-4xl" aria-live="polite">{look.label}</p>
                <p className="mt-1 text-sm text-white/70">{look.text}</p>
                {t?.seconds_left > 0 && !view && <p className="mt-2 text-sm font-semibold text-accent">{state === "BLOQUEIO" ? "Rearme automático" : "Religa"} em {t.seconds_left}s</p>}
                {t && <p className="mt-1 text-xs text-white/50">Negativas seguidas: {t.denials}/{t.max_denials}</p>}
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              <button className="btn-ghost !border-white/20 !bg-white/10 !text-white hover:!bg-white/20" disabled={state !== "AGUARDANDO_PASSAGEM"} onClick={() => act("/automacao/passagem", "Passagem registrada")}>Registrar passagem (I0.1)</button>
              <button className="btn-ghost !border-white/20 !bg-white/10 !text-white hover:!bg-white/20" disabled={state !== "BLOQUEIO"} onClick={() => act("/automacao/reset", "Catraca rearmada")}><RotateCcw size={15} />Rearmar (I0.2)</button>
            </div>
          </section>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="card flex items-center gap-3"><CheckCircle2 className="text-ok" /><div><p className="text-2xl font-extrabold">{stats?.permitidos ?? "-"}</p><p className="text-xs text-muted">Acessos permitidos hoje</p></div></div>
            <div className="card flex items-center gap-3"><XCircle className="text-danger" /><div><p className="text-2xl font-extrabold">{stats?.negados ?? "-"}</p><p className="text-xs text-muted">Acessos negados hoje</p></div></div>
            <div className="card flex items-center gap-3"><Gauge className="text-brand-deeper" /><div><p className="text-2xl font-extrabold">{stats?.ciclo_medio_ms != null ? `${num(stats.ciclo_medio_ms)} ms` : "-"}</p><p className="text-xs text-muted">Tempo médio de ciclo</p></div></div>
          </div>

          <Card className="space-y-3">
            <h2>Entradas e saídas (E/S do CLP)</h2>
            <div className="grid gap-x-8 gap-y-2 sm:grid-cols-2">
              {IO_LABELS.map(([tag, label]) => (
                <div key={tag} className="flex items-center gap-3 text-sm">
                  <Led on={io[tag]} tone={tag === "Q0.2" || tag === "Q0.4" ? "red" : tag === "Q0.3" ? "yellow" : "green"} />
                  <code className="w-10 font-bold text-brand-deeper">{tag}</code><span className="text-muted">{label}</span>
                  <span className="ml-auto text-xs font-semibold">{io[tag] ? "1" : "0"}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-5">
          <Card className="space-y-3">
            <div><h2>Simulador de sensores</h2><p className="text-sm text-muted">Dispara cada cenário sem depender de dados preparados.</p></div>
            <div className="space-y-2">
              {SCENARIOS.map((s) => (
                <button key={s.id} className="flex w-full items-center gap-3 rounded-xl border border-line px-3.5 py-2.5 text-left hover:bg-paper disabled:opacity-50" disabled={busy} onClick={() => simulate(s.id)}>
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-soft text-brand-deeper"><Play size={15} /></span>
                  <span><span className="block text-sm font-bold">{s.label}</span><span className="block text-xs text-muted">{s.desc}</span></span>
                </button>
              ))}
            </div>
            {cycles && (
              <div className="space-y-2 border-t border-line pt-3">
                {cycles.map((c, i) => (
                  <div key={i}>
                    <Badge tone={c.granted ? "ok" : "danger"}>{c.granted ? "Permitido" : `Negado: ${c.reason}`}</Badge>
                    <pre className="mt-2 max-h-48 overflow-auto rounded-xl bg-ink p-3 text-[11px] leading-relaxed text-white/90">{c.log.join("\n")}</pre>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      <Card className="space-y-3">
        <div className="flex items-center justify-between"><h2>Log de eventos ao vivo</h2><span className="flex items-center gap-1.5 text-xs text-muted"><span className="h-2 w-2 animate-pulse rounded-full bg-accent" />atualiza a cada 2 s</span></div>
        <LogTable logs={logs} />
      </Card>
    </div>
  );
}

function LogTable({ logs }) {
  if (!logs.length) return <p className="rounded-xl bg-paper px-4 py-6 text-center text-sm text-muted">Nenhum evento registrado.</p>;
  return (
    <div className="overflow-hidden rounded-xl border border-line">
      <ul className="divide-y divide-line bg-ink font-mono text-xs text-white/90">
        {logs.map((l) => (
          <li key={l.id}>
            <details className="group">
              <summary className="flex cursor-pointer flex-wrap items-center gap-x-3 gap-y-1 px-3 py-2 hover:bg-white/5">
                <span className="text-white/50">{fmtTimeSec(l.created_at)}</span>
                <span className={`font-bold ${l.granted === true ? "text-accent" : l.granted === false ? "text-red-300" : "text-amber-300"}`}>{l.granted === true ? "PERMITIDO" : l.granted === false ? "NEGADO" : l.event}</span>
                <span>{l.aluno_name || "—"}</span>
                <span className="text-white/60">{l.reason}</span>
                {l.simulated && <span className="rounded bg-white/10 px-1.5 text-[10px]">simulado</span>}
                {l.cycle_ms != null && <span className="ml-auto text-white/50">{l.cycle_ms} ms</span>}
              </summary>
              {l.detail && <pre className="overflow-x-auto bg-black/30 px-4 py-2 text-[11px] leading-relaxed text-white/80">{l.detail}</pre>}
            </details>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ---------- Histórico ---------- */
function Historico({ tid }) {
  const [f, setF] = useState({ result: "", event: "", day: "" });
  const [logs, setLogs] = useState([]);
  const [err, setErr] = useState(null);
  useEffect(() => {
    const params = { turnstile_id: tid, limit: 100 };
    if (f.result) params.result = f.result;
    if (f.event) params.event = f.event;
    if (f.day) params.day = f.day;
    api.get("/automacao/logs", { params }).then((r) => { setLogs(r.data); setErr(null); }).catch((e) => setErr(errMsg(e)));
  }, [tid, f]);
  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <select className="input !w-auto" aria-label="Resultado" value={f.result} onChange={(e) => setF({ ...f, result: e.target.value })}>
          <option value="">Todos os resultados</option><option value="permitido">Permitidos</option><option value="negado">Negados</option>
        </select>
        <select className="input !w-auto" aria-label="Tipo de evento" value={f.event} onChange={(e) => setF({ ...f, event: e.target.value })}>
          <option value="">Todos os eventos</option>{["TENTATIVA", "PASSAGEM", "TIMEOUT", "BLOQUEIO", "RESET"].map((x) => <option key={x}>{x}</option>)}
        </select>
        <input type="date" className="input !w-auto" aria-label="Data" value={f.day} onChange={(e) => setF({ ...f, day: e.target.value })} />
        {(f.result || f.event || f.day) && <button className="btn-ghost" onClick={() => setF({ result: "", event: "", day: "" })}>Limpar filtros</button>}
      </div>
      {err && <ErrorState message={err} />}
      <LogTable logs={logs} />
    </Card>
  );
}

/* ---------- Lógica de controle ---------- */
function Contact({ tag, label, nc = false, on }) {
  const lit = on === undefined ? false : nc ? !on : on;
  return (
    <div className="flex shrink-0 flex-col items-center text-center">
      <span className="text-[10px] font-bold text-brand-deeper">{tag}</span>
      <span className={`flex h-9 w-14 items-center justify-center rounded-md border-2 font-mono text-base font-bold transition ${lit ? "border-ok bg-accent-soft text-ok" : "border-ink/40 bg-white text-ink/60"}`}>{nc ? "|/|" : "| |"}</span>
      <span className="mt-0.5 max-w-20 text-[10px] leading-tight text-muted">{label}</span>
    </div>
  );
}
function Coil({ tag, label, on, kind = "" }) {
  return (
    <div className="flex shrink-0 flex-col items-center text-center">
      <span className="text-[10px] font-bold text-brand-deeper">{tag}</span>
      <span className={`flex h-9 w-14 items-center justify-center rounded-full border-2 font-mono text-sm font-bold transition ${on ? "border-ok bg-accent text-ink" : "border-ink/40 bg-white text-ink/60"}`}>{kind ? `(${kind})` : "( )"}</span>
      <span className="mt-0.5 max-w-24 text-[10px] leading-tight text-muted">{label}</span>
    </div>
  );
}
const Wire = () => <span className="mt-3 h-0.5 min-w-3 flex-1 self-start bg-ink/40" aria-hidden="true" />;
function Rung({ n, title, children }) {
  return (
    <div>
      <p className="mb-1 text-xs font-bold text-muted">Degrau {n} · {title}</p>
      <div className="overflow-x-auto"><div className="flex min-w-[560px] items-start rounded-lg bg-paper px-2 py-3"><span className="mr-1 h-14 w-1 shrink-0 rounded bg-ink" /><Wire />{children}<Wire /><span className="ml-1 h-14 w-1 shrink-0 rounded bg-ink" /></div></div>
    </div>
  );
}

function Logica({ tid }) {
  const [state, setState] = useState("TRAVADA");
  useEffect(() => { api.get("/automacao/status", { params: { turnstile_id: tid } }).then((r) => setState(r.data.turnstile.state)).catch(() => {}); }, [tid]);
  const io = ioFor(state);
  const bloqueio = state === "BLOQUEIO";
  const flow = ["TRAVADA", "VALIDANDO", "LIBERADA", "AGUARDANDO_PASSAGEM"];
  return (
    <div className="space-y-5">
      <Card className="space-y-3">
        <h2>Máquina de estados</h2>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {flow.map((s, i) => (
            <span key={s} className="flex items-center gap-2">
              <span className={`rounded-lg px-3 py-1.5 font-bold ${state === s ? "bg-ink text-white" : "bg-paper text-ink"}`}>{s}</span>
              <span className="text-muted">{i < flow.length - 1 ? "→" : "→ TRAVADA"}</span>
            </span>
          ))}
        </div>
        <p className={`rounded-lg px-3 py-2 text-sm ${bloqueio ? "bg-red-50 text-danger" : "bg-paper text-muted"}`}>
          Ramo de falha: após <b>3 negativas seguidas</b>, a catraca vai para <b>BLOQUEIO</b> (sirene) até o rearme manual (I0.2) ou 60 s. Em VALIDANDO, uma negativa volta para TRAVADA.
        </p>
        <p className="text-xs text-muted">Estado atual destacado: <b>{state}</b>. Transições inválidas são rejeitadas pelo serviço (ex.: TRAVADA → LIBERADA).</p>
      </Card>

      <Card className="space-y-4">
        <div><h2>Diagrama ladder (simplificado)</h2><p className="text-sm text-muted">Contatos e bobinas acendem conforme o estado atual da catraca.</p></div>
        <Rung n={1} title="Liberação da trava">
          <Contact tag="I0.0" label="Credencial lida" on={io["I0.0"] || io["Q0.0"]} /><Wire />
          <Contact tag="M0.1" label="Agendamento válido" on={io["Q0.0"]} /><Wire />
          <Contact tag="M0.2" label="Dentro da janela" on={io["Q0.0"]} /><Wire />
          <Contact tag="M0.4" label="Já usado" nc on={false} /><Wire />
          <Contact tag="M0.3" label="Bloqueio" nc on={bloqueio} /><Wire />
          <Coil tag="Q0.0" label="Solenoide da trava" on={io["Q0.0"]} />
        </Rung>
        <Rung n={2} title="Sinalização"><Contact tag="Q0.0" label="Trava livre" on={io["Q0.0"]} /><Wire /><Coil tag="Q0.1" label="LED verde" on={io["Q0.1"]} /></Rung>
        <Rung n={3} title="Sinalização"><Contact tag="Q0.0" label="Trava livre" nc on={io["Q0.0"]} /><Wire /><Coil tag="Q0.2" label="LED vermelho" on={io["Q0.2"]} /></Rung>
        <Rung n={4} title="Religamento (passagem ou tempo)">
          <Contact tag="Q0.0" label="Trava livre" on={io["Q0.0"]} /><Wire />
          <div className="flex shrink-0 flex-col items-center text-center"><span className="text-[10px] font-bold text-brand-deeper">T1</span><span className="flex h-9 items-center rounded-md border-2 border-ink/40 bg-white px-2 font-mono text-xs font-bold">TON PT=10s</span><span className="mt-0.5 text-[10px] text-muted">Tempo de passagem</span></div><Wire />
          <Coil tag="Q0.0" label="Desliga solenoide" on={false} kind="R" />
        </Rung>
        <Rung n={5} title="Bloqueio e alarme">
          <Contact tag="C1" label="Negativas ≥ 3" on={bloqueio} /><Wire />
          <Coil tag="M0.3" label="Bloqueio" on={bloqueio} kind="S" /><Wire />
          <Coil tag="Q0.4" label="Sirene" on={io["Q0.4"]} />
        </Rung>
        <Rung n={6} title="Rearme do supervisor"><Contact tag="I0.2" label="Botão de rearme" on={false} /><Wire /><Coil tag="M0.3" label="Bloqueio" on={false} kind="R" /></Rung>
      </Card>

      <Card className="space-y-3">
        <h2>Regra de liberação</h2>
        <ol className="list-decimal space-y-1.5 pl-5 text-sm text-ink/85">
          <li>O leitor (I0.0) lê a credencial do aluno; credencial desconhecida é negada.</li>
          <li>O CLP procura o agendamento; sem agendamento, nega.</li>
          <li>O agendamento precisa estar com status AGENDADO: um segundo uso da mesma aula é negado (anti-fraude).</li>
          <li>O horário precisa estar na janela: de 15 min antes do início até o fim da aula (horário de Brasília).</li>
          <li>Válido: solenoide Q0.0 e LED verde Q0.1; a aula passa para CHECKIN e o sistema aguarda a passagem por 10 s.</li>
          <li>Negado: LED vermelho Q0.2, motivo registrado no log e contador de negativas incrementado.</li>
        </ol>
      </Card>
    </div>
  );
}

export default function Automacao() {
  const [tab, setTab] = useState("super");
  const [turnstiles, setTurnstiles] = useState([]);
  const [tid, setTid] = useState(null);
  useEffect(() => { api.get("/automacao/turnstiles").then((r) => { setTurnstiles(r.data); setTid(r.data[0]?.id ?? null); }); }, []);

  return (
    <>
      <PageHeader title="Catraca" subtitle="Supervisório da catraca virtual: simulação de um processo industrial (sensor → CLP → atuador → SCADA)."
        actions={<Badge tone="brand"><Activity size={12} />Simulação</Badge>} />
      <Tabs value={tab} onChange={setTab} tabs={[{ value: "super", label: "Supervisório" }, { value: "hist", label: "Histórico" }, { value: "logica", label: "Lógica de controle" }]} />
      {tid && tab === "super" && <Supervisorio turnstiles={turnstiles} tid={tid} setTid={setTid} />}
      {tid && tab === "hist" && <Historico tid={tid} />}
      {tid && tab === "logica" && <Logica tid={tid} />}
      {!tid && <div className="flex items-center gap-2 text-sm text-muted"><ShieldAlert size={16} />Carregando catracas...</div>}
    </>
  );
}
