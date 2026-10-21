import { Link } from "react-router-dom";
import { AlertTriangle, CalendarDays, ChevronRight, UserPlus, Users } from "lucide-react";
import { useAuth } from "../../AuthContext";
import { Badge, Card, EmptyState, ErrorState, PageHeader, SkeletonList, StatCard } from "../../components/ui";
import { fmtDateTime, fmtTime } from "../../lib/format";
import { useFetch } from "../../lib/hooks";
import api, { STATUS } from "../../services/api";

export default function Overview() {
  const { user } = useAuth();
  const { data: d, loading, error, reload } = useFetch(async () => (await api.get("/dashboard/personal")).data, []);
  const today = new Date().toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo", weekday: "long", day: "numeric", month: "long" });

  return (
    <>
      <PageHeader title={`Olá, ${user.name.split(" ")[0]}`} subtitle={today} />
      {error && <ErrorState message={error} onRetry={reload} />}
      {loading && !d && <SkeletonList rows={3} />}
      {d && (
        <>
          {d.pendentes > 0 && (
            <Link to="/personal/alunos" className="flex items-center gap-3 rounded-2xl bg-ink px-5 py-4 text-white">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10"><UserPlus size={20} /></span>
              <div className="flex-1"><p className="font-bold">{d.pendentes} solicitação(ões) de vínculo</p><p className="text-sm text-white/70">Aceite ou recuse para liberar o acesso dos alunos.</p></div>
              <ChevronRight size={20} />
            </Link>
          )}

          <div className="grid gap-3 sm:grid-cols-3">
            <StatCard icon={Users} label="Alunos ativos" value={d.alunos_ativos} />
            <StatCard icon={CalendarDays} tone="accent" label="Aulas hoje" value={d.aulas_hoje} />
            <StatCard icon={AlertTriangle} tone={d.alertas ? "warn" : "neutral"} label="Alertas de estagnação" value={d.alertas} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section aria-labelledby="prox">
              <div className="mb-2 flex items-center justify-between"><h2 id="prox">Próximas aulas</h2><Link to="/agendamento" className="text-sm font-semibold text-brand-deeper">Ver agenda</Link></div>
              {d.proximas.length === 0 ? (
                <EmptyState icon={CalendarDays} title="Nenhuma aula marcada" text="Marque aulas na agenda para ver os próximos horários aqui." action={<Link to="/agendamento" className="btn">Abrir agenda</Link>} />
              ) : (
                <Card className="divide-y divide-line !p-0">
                  {d.proximas.map((s) => (
                    <div key={s.id} className="flex items-center gap-3 px-4 py-3">
                      <span className="w-14 text-sm font-bold text-brand-deeper">{fmtTime(s.start_time)}</span>
                      <div className="min-w-0 flex-1"><p className="truncate font-semibold">{s.aluno_name}</p><p className="text-xs text-muted">{fmtDateTime(s.start_time)}</p></div>
                      <Badge tone={STATUS[s.status].tone}>{STATUS[s.status].label}</Badge>
                    </div>
                  ))}
                </Card>
              )}
            </section>

            <section aria-labelledby="alert">
              <div className="mb-2 flex items-center justify-between"><h2 id="alert">Atenção</h2><Link to="/personal/relatorios" className="text-sm font-semibold text-brand-deeper">Relatórios</Link></div>
              {d.alertas_lista.length === 0 ? (
                <EmptyState icon={AlertTriangle} title="Tudo em ordem" text="Nenhum aluno com cargas paradas no momento." />
              ) : (
                <Card className="divide-y divide-line !p-0">
                  {d.alertas_lista.map((a, i) => (
                    <Link key={i} to={`/personal/alunos/${a.aluno_id}`} className="flex items-start gap-3 px-4 py-3 hover:bg-paper">
                      <AlertTriangle size={18} className="mt-0.5 shrink-0 text-warn" />
                      <p className="text-sm"><b>{a.aluno_name}</b> · {a.exercise}<br /><span className="text-muted">{a.sessions} sessões sem recorde (parado em {a.current_load} kg)</span></p>
                    </Link>
                  ))}
                </Card>
              )}
            </section>
          </div>
        </>
      )}
    </>
  );
}
