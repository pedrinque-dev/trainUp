import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, Check, Dumbbell, Minus, Plus, SkipForward, Timer, Trophy } from "lucide-react";
import { useToast } from "../../components/Toast";
import { Badge, Card, EmptyState, ErrorState, PageHeader, ProgressBar, SkeletonList, StatCard } from "../../components/ui";
import { num, todayISO, weekdayIndex } from "../../lib/format";
import { useFetch } from "../../lib/hooks";
import api, { errMsg } from "../../services/api";

function Stepper({ label, value, onChange, step = 1, min = 0, unit }) {
  const n = Number(value) || 0;
  const set = (v) => onChange(String(Math.max(min, Math.round(v * 100) / 100)));
  return (
    <div className="flex-1">
      <p className="mb-1 text-center text-xs font-semibold text-muted">{label}</p>
      <div className="flex items-center gap-1.5">
        <button type="button" className="btn-ghost !h-12 !w-12 !p-0" onClick={() => set(n - step)} aria-label={`Diminuir ${label}`}><Minus size={18} /></button>
        <div className="flex-1 text-center">
          <input className="w-full bg-transparent text-center text-2xl font-extrabold text-ink outline-none" inputMode="decimal" aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} />
          <span className="text-xs text-muted">{unit}</span>
        </div>
        <button type="button" className="btn-ghost !h-12 !w-12 !p-0" onClick={() => set(n + step)} aria-label={`Aumentar ${label}`}><Plus size={18} /></button>
      </div>
    </div>
  );
}

export default function Treinar() {
  const toast = useToast();
  const [stage, setStage] = useState("select"); // select | run | summary
  const [workout, setWorkout] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [idx, setIdx] = useState(0);
  const [sets, setSets] = useState({});
  const [rest, setRest] = useState({ enabled: true, seconds: 60, left: 0 });
  const [busy, setBusy] = useState(false);
  const [summary, setSummary] = useState(null);

  const { data: workouts, loading, error, reload } = useFetch(async () => (await api.get(`/workouts/today?weekday=${weekdayIndex(todayISO())}`)).data, []);

  useEffect(() => {
    if (rest.left <= 0) return undefined;
    const t = setTimeout(() => {
      setRest((r) => ({ ...r, left: r.left - 1 }));
      if (rest.left === 1) navigator.vibrate?.(200);
    }, 1000);
    return () => clearTimeout(t);
  }, [rest.left]);

  const key = (item, n) => `${item.id}-${n}`;
  const val = (item, n) => sets[key(item, n)] ?? { reps: String(item.reps), load: String(item.target_load), done: false };
  const upd = (item, n, patch) => setSets((s) => ({ ...s, [key(item, n)]: { ...val(item, n), ...patch } }));

  async function start(w) {
    setBusy(true);
    try {
      const { data } = await api.post("/sessions", { workout_id: w.id });
      setWorkout(w); setSessionId(data.id); setIdx(0); setSets({}); setStage("run");
    } catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  }

  const items = workout?.items || [];
  const item = items[idx];
  const totalSets = items.reduce((n, i) => n + i.sets, 0);
  const doneSets = items.reduce((n, i) => n + Array.from({ length: i.sets }).filter((_, k) => val(i, k).done).length, 0);
  const currentSet = item ? Array.from({ length: item.sets }).findIndex((_, k) => !val(item, k).done) : -1;

  async function complete(n) {
    const v = val(item, n);
    if (!(Number(v.reps) > 0) || Number(v.load) < 0 || v.load === "") return toast("Informe repetições e carga válidas", "error");
    setBusy(true);
    try {
      await api.post(`/sessions/${sessionId}/sets`, { logs: [{ exercise_id: item.exercise.id, workout_id: workout.id, set_number: n + 1, reps: Number(v.reps), load_kg: Number(v.load) }] });
      upd(item, n, { done: true });
      const last = doneSets + 1 === totalSets;
      if (rest.enabled && !last) setRest((r) => ({ ...r, left: r.seconds }));
    } catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  }

  async function finish() {
    if (doneSets === 0 && !window.confirm("Você não concluiu nenhuma série. Encerrar mesmo assim?")) return;
    setBusy(true);
    try {
      const { data } = await api.post(`/sessions/${sessionId}/finish`);
      setSummary(data); setRest((r) => ({ ...r, left: 0 })); setStage("summary");
    } catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  }

  if (stage === "select") {
    return (
      <>
        <PageHeader title="Treinar" subtitle="Escolha a ficha de hoje para começar." />
        {error && <ErrorState message={error} onRetry={reload} />}
        {loading && !workouts && <SkeletonList rows={2} />}
        {workouts?.length === 0 && <EmptyState icon={Dumbbell} title="Sem treino para hoje" text="Seu personal ainda não montou uma ficha para você." action={<Link to="/aluno" className="btn-ghost">Voltar ao início</Link>} />}
        <div className="grid gap-3 md:grid-cols-2">
          {workouts?.map((w) => (
            <Card key={w.id} className="flex flex-col gap-3">
              <h3>{w.name}</h3>
              <ul className="flex-1 space-y-1 text-sm text-muted">{w.items.map((i) => <li key={i.id}>{i.exercise.name} · {i.sets}x{i.reps}</li>)}</ul>
              <button className="btn-accent" onClick={() => start(w)} disabled={busy}>Iniciar este treino<ArrowRight size={16} /></button>
            </Card>
          ))}
        </div>
      </>
    );
  }

  if (stage === "summary" && summary) {
    const delta = summary.volume_delta_pct;
    return (
      <>
        <PageHeader title="Treino concluído" subtitle={summary.workout_name} />
        <section className="rounded-3xl bg-ink p-6 text-white">
          <p className="text-sm text-white/70">Volume total da sessão</p>
          <p className="text-5xl font-extrabold"><span className="text-grad">{num(summary.total_volume, 0)}</span> <span className="text-xl text-white/70">kg</span></p>
          <p className="mt-2 text-sm text-white/80">
            {delta == null ? "Primeira vez nesta ficha: ela vira sua referência." : `${delta >= 0 ? "+" : ""}${num(delta)}% em relação ao treino anterior (${num(summary.previous_volume, 0)} kg).`}
          </p>
        </section>
        <div className="grid gap-3 sm:grid-cols-3">
          <StatCard icon={Check} tone="accent" label="Séries feitas" value={summary.total_sets} />
          <StatCard icon={Timer} label="Duração" value={summary.duration_min ? `${summary.duration_min} min` : "-"} />
          <StatCard icon={Trophy} tone="accent" label="Recordes de carga" value={summary.records.length} hint={summary.records.join(", ") || undefined} />
        </div>
        <Card className="divide-y divide-line !p-0">
          {summary.exercises.map((x) => (
            <div key={x.exercise_id} className="flex items-center gap-3 px-4 py-3">
              <div className="min-w-0 flex-1"><p className="font-semibold">{x.exercise}</p><p className="text-xs text-muted">{x.sets} séries · {num(x.volume, 0)} kg de volume</p></div>
              <span className="text-sm font-semibold">{num(x.max_load)} kg</span>
              {x.record && <Badge tone="accent"><Trophy size={12} />Recorde</Badge>}
            </div>
          ))}
        </Card>
        <div className="flex gap-3"><Link to="/aluno" className="btn">Voltar ao início</Link><Link to="/aluno/evolucao" className="btn-ghost">Ver evolução</Link></div>
      </>
    );
  }

  const allDone = currentSet === -1;
  const lastItem = idx === items.length - 1;
  return (
    <div className="mx-auto max-w-xl space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm"><span className="font-semibold">{workout.name}</span><span className="text-muted">{doneSets}/{totalSets} séries</span></div>
        <ProgressBar value={doneSets} max={totalSets} />
      </div>

      {rest.left > 0 && (
        <div className="flex items-center gap-4 rounded-2xl bg-ink px-5 py-4 text-white" role="timer" aria-live="off">
          <Timer size={26} className="text-accent" aria-hidden="true" />
          <div className="flex-1"><p className="text-xs text-white/70">Descanso</p><p className="text-3xl font-extrabold tabular-nums">{String(Math.floor(rest.left / 60)).padStart(2, "0")}:{String(rest.left % 60).padStart(2, "0")}</p></div>
          <button className="btn-ghost !bg-white/10 !text-white !border-white/20" onClick={() => setRest((r) => ({ ...r, left: 0 }))}><SkipForward size={16} />Pular</button>
        </div>
      )}

      <Card className="space-y-4">
        <div>
          <p className="text-xs font-semibold text-muted">Exercício {idx + 1} de {items.length}</p>
          <h2 className="!text-2xl">{item.exercise.name}</h2>
          <p className="text-sm text-muted">Meta: {item.sets}x{item.reps} com {num(item.target_load)} kg · {item.exercise.muscle_group}</p>
          {item.exercise.description && <p className="mt-2 rounded-xl bg-paper p-3 text-sm text-ink/80">{item.exercise.description}</p>}
        </div>

        <ol className="space-y-2">
          {Array.from({ length: item.sets }, (_, n) => {
            const v = val(item, n);
            const current = n === currentSet;
            return (
              <li key={n} className={`rounded-2xl border p-3 ${current ? "border-brand bg-brand-soft/40" : v.done ? "border-accent/60 bg-accent-soft" : "border-line"}`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold">Série {n + 1}</span>
                  {v.done ? <Badge tone="ok"><Check size={12} />{v.reps} reps · {num(v.load)} kg</Badge> : !current && <span className="text-xs text-muted">Alvo: {item.reps} x {num(item.target_load)} kg</span>}
                </div>
                {current && (
                  <div className="mt-3 space-y-3">
                    <div className="flex gap-4">
                      <Stepper label="Repetições" value={v.reps} onChange={(x) => upd(item, n, { reps: x })} step={1} min={1} />
                      <Stepper label="Carga" unit="kg" value={v.load} onChange={(x) => upd(item, n, { load: x })} step={2.5} />
                    </div>
                    <button className="btn-accent w-full !py-4 !text-base" onClick={() => complete(n)} disabled={busy}><Check size={20} />Concluir série</button>
                  </div>
                )}
              </li>
            );
          })}
        </ol>

        <div className="flex items-center justify-between gap-2 border-t border-line pt-4">
          <button className="btn-ghost" onClick={() => setIdx(idx - 1)} disabled={idx === 0}><ArrowLeft size={16} />Anterior</button>
          {!lastItem ? (
            <button className={allDone ? "btn" : "btn-ghost"} onClick={() => setIdx(idx + 1)}>Próximo<ArrowRight size={16} /></button>
          ) : (
            <button className={allDone ? "btn-accent" : "btn-ghost"} onClick={finish} disabled={busy}>Finalizar treino<Check size={16} /></button>
          )}
        </div>
      </Card>

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <label className="flex items-center gap-2 font-medium">
          <input type="checkbox" className="h-5 w-5 accent-brand" checked={rest.enabled} onChange={(e) => setRest({ ...rest, enabled: e.target.checked, left: 0 })} />Timer de descanso
        </label>
        {rest.enabled && (
          <select className="input !w-auto" aria-label="Tempo de descanso" value={rest.seconds} onChange={(e) => setRest({ ...rest, seconds: Number(e.target.value) })}>
            {[30, 45, 60, 90, 120].map((s) => <option key={s} value={s}>{s}s</option>)}
          </select>
        )}
        {!lastItem && doneSets > 0 && <button className="font-semibold text-brand-deeper underline" onClick={finish}>Encerrar treino agora</button>}
      </div>
    </div>
  );
}
