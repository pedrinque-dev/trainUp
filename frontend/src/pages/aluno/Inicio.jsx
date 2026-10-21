import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CalendarDays, Dumbbell, KeyRound } from "lucide-react";
import { useAuth } from "../../AuthContext";
import CheckinCard from "../../components/Catraca";
import { useToast } from "../../components/Toast";
import { Badge, Card, EmptyState, ErrorState, Field, PageHeader, SkeletonList } from "../../components/ui";
import { fmtDateTime, todayISO, weekdayIndex } from "../../lib/format";
import { useFetch } from "../../lib/hooks";
import api, { errMsg, GOALS } from "../../services/api";

const LINK_STATUS = { PENDENTE: ["Aguardando aprovação", "warn"], ACEITO: ["Aceita", "ok"], RECUSADO: ["Recusada", "danger"], CANCELADO: ["Cancelada", "neutral"] };

function LinkCard({ onLinked }) {
  const toast = useToast();
  const [code, setCode] = useState("");
  const { data: reqs, reload } = useFetch(async () => (await api.get("/links/mine")).data, []);
  const pending = reqs?.some((r) => r.status === "PENDENTE");

  async function send(e) {
    e.preventDefault();
    try { await api.post("/links/request", { invite_code: code.trim().toUpperCase() }); toast("Solicitação enviada ao personal"); setCode(""); reload(true); }
    catch (err) { toast(errMsg(err), "error"); }
  }
  return (
    <Card className="space-y-4">
      <div className="flex items-center gap-3">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-soft text-brand-deeper"><KeyRound size={22} /></span>
        <div><h2>Vincule-se a um personal</h2><p className="text-sm text-muted">Informe o código de convite que seu personal passou. Ele precisa aprovar a solicitação.</p></div>
      </div>
      <form onSubmit={send} className="flex flex-wrap items-end gap-3">
        <div className="min-w-48 flex-1"><Field label="Código de convite"><input className="input uppercase tracking-widest" value={code} onChange={(e) => setCode(e.target.value)} maxLength={12} required placeholder="EX.: TRAIN123" /></Field></div>
        <button className="btn" disabled={!code.trim()}>Solicitar vínculo</button>
      </form>
      {reqs?.length > 0 && (
        <ul className="divide-y divide-line text-sm">
          {reqs.map((r) => <li key={r.id} className="flex items-center justify-between py-2"><span>Personal <b>{r.personal_name}</b></span><Badge tone={LINK_STATUS[r.status][1]}>{LINK_STATUS[r.status][0]}</Badge></li>)}
        </ul>
      )}
      {pending && <button className="btn-ghost" onClick={onLinked}>Já foi aprovado? Atualizar</button>}
    </Card>
  );
}

export default function Inicio() {
  const { user, refreshUser } = useAuth();
  const [linked, setLinked] = useState(!!user.personal_id);
  useEffect(() => { refreshUser().then((u) => setLinked(!!u.personal_id)).catch(() => {}); }, [refreshUser]);

  const { data, loading, error, reload } = useFetch(async () => {
    const [w, s] = await Promise.all([api.get(`/workouts/today?weekday=${weekdayIndex(todayISO())}`), api.get("/schedules")]);
    const now = Date.now();
    const next = s.data.find((x) => ["AGENDADO", "CHECKIN"].includes(x.status) && new Date(x.start_time).getTime() + x.duration_min * 60000 > now) || null;
    return { workouts: w.data, next };
  }, [linked]);

  return (
    <>
      <PageHeader title={`Olá, ${user.name.split(" ")[0]}`} subtitle={`Objetivo: ${GOALS[user.goal] || "não definido"}${user.personal_name ? ` · Personal: ${user.personal_name}` : ""}`} />
      {!linked && <LinkCard onLinked={() => refreshUser().then((u) => setLinked(!!u.personal_id))} />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {loading && !data && <SkeletonList rows={2} />}
      {data && linked && (
        <>
          {data.workouts.length === 0 ? (
            <EmptyState icon={Dumbbell} title="Sem treino para hoje" text="Seu personal ainda não montou uma ficha para você." />
          ) : (
            <section className="relative overflow-hidden rounded-3xl bg-ink p-6 text-white sm:p-8" aria-labelledby="hoje">
              <div className="absolute -right-10 -top-10 h-48 w-48 rounded-full bg-brand/25 blur-3xl" aria-hidden="true" />
              <p className="relative text-sm font-semibold text-white/70">Treino de hoje</p>
              <h2 id="hoje" className="relative mt-1 !text-2xl !text-white sm:!text-3xl">{data.workouts.map((w) => w.name).join(" + ")}</h2>
              <p className="relative mt-1 text-sm text-white/70">{data.workouts.reduce((n, w) => n + w.items.length, 0)} exercícios · {data.workouts.reduce((n, w) => n + w.items.reduce((m, i) => m + i.sets, 0), 0)} séries</p>
              <Link to="/aluno/treinar" className="btn-accent relative mt-5 !px-6 !py-3 !text-base">Começar treino<ArrowRight size={18} /></Link>
            </section>
          )}

          <section aria-labelledby="aula">
            <h2 id="aula" className="mb-2">Próxima aula</h2>
            {data.next ? (
              <Card className="space-y-4">
                <div className="flex items-center gap-3">
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-soft text-ink"><CalendarDays size={22} /></span>
                  <div className="flex-1"><p className="font-bold capitalize">{fmtDateTime(data.next.start_time)}</p><p className="text-sm text-muted">com {data.next.personal_name} · {data.next.duration_min} min</p></div>
                  {data.next.status === "CHECKIN" && <Badge tone="accent">Check-in feito</Badge>}
                </div>
                {data.next.status === "AGENDADO" && <div className="border-t border-line pt-4"><CheckinCard scheduleId={data.next.id} onDone={() => reload(true)} /></div>}
              </Card>
            ) : (
              <EmptyState icon={CalendarDays} title="Nenhuma aula marcada" action={<Link to="/agendamento" className="btn">Agendar aula</Link>} />
            )}
          </section>
        </>
      )}
    </>
  );
}
