import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, Dumbbell, Plus, Trash2 } from "lucide-react";
import { LoadChart } from "../../components/charts";
import ReportView from "../../components/ReportView";
import { useToast } from "../../components/Toast";
import { Badge, Card, EmptyState, ErrorState, PageHeader, SkeletonList, Tabs } from "../../components/ui";
import { initials, num } from "../../lib/format";
import { useFetch } from "../../lib/hooks";
import api, { errMsg, GOALS, WEEK } from "../../services/api";

export default function AlunoPerfil() {
  const { id } = useParams();
  const nav = useNavigate();
  const toast = useToast();
  const [tab, setTab] = useState("fichas");
  const [sel, setSel] = useState(0);

  const { data, loading, error, reload } = useFetch(async () => {
    const [u, w, e, s] = await Promise.all([
      api.get(`/users/${id}`), api.get("/workouts", { params: { aluno_id: id } }),
      api.get("/analytics/evolution", { params: { aluno_id: id } }), api.get("/analytics/stagnation", { params: { aluno_id: id } }),
    ]);
    return { aluno: u.data, workouts: w.data, evo: e.data, alerts: s.data };
  }, [id]);

  async function remove() {
    if (!window.confirm(`Remover ${data.aluno.name}? Treinos, histórico e aulas serão apagados.`)) return;
    try { await api.delete(`/users/${id}`); toast("Aluno removido"); nav("/personal/alunos"); } catch (e) { toast(errMsg(e), "error"); }
  }

  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (loading && !data) return <SkeletonList rows={4} />;
  const { aluno, workouts, evo, alerts } = data;
  const ex = evo[sel];

  return (
    <>
      <Link to="/personal/alunos" className="inline-flex items-center gap-1 text-sm font-semibold text-brand-deeper"><ArrowLeft size={16} />Alunos</Link>
      <PageHeader
        title={<span className="flex items-center gap-3"><span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-soft text-base font-bold text-brand-deeper">{initials(aluno.name)}</span>{aluno.name}</span>}
        subtitle={`${GOALS[aluno.goal] || "Sem objetivo definido"} · ${aluno.email}`}
        actions={<button className="btn-danger" onClick={remove}><Trash2 size={15} />Remover</button>} />

      {alerts.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {alerts.map((a) => <Badge key={a.exercise} tone="warn"><AlertTriangle size={12} />{a.exercise}: {a.sessions} sessões sem recorde</Badge>)}
        </div>
      )}

      <Tabs value={tab} onChange={setTab} tabs={[{ value: "fichas", label: "Fichas" }, { value: "evolucao", label: "Evolução" }, { value: "relatorio", label: "Relatório" }]} />

      {tab === "fichas" && (
        <section className="space-y-3">
          <div className="flex justify-end"><Link to={`/personal/treinos?aluno=${id}&novo=1`} className="btn"><Plus size={16} />Nova ficha</Link></div>
          {workouts.length === 0 ? (
            <EmptyState icon={Dumbbell} title="Nenhuma ficha ainda" text="Crie a primeira ficha de treino deste aluno." />
          ) : workouts.map((w) => (
            <Card key={w.id}>
              <div className="flex items-center justify-between gap-3"><h3>{w.name}</h3><Badge>{w.weekday == null ? "Qualquer dia" : WEEK[w.weekday]}</Badge></div>
              <ul className="mt-3 grid gap-x-6 gap-y-1.5 text-sm sm:grid-cols-2">
                {w.items.map((i) => <li key={i.id} className="flex justify-between gap-3 border-b border-line/60 py-1"><span>{i.exercise.name}</span><span className="text-muted">{i.sets}x{i.reps} · {num(i.target_load)} kg</span></li>)}
              </ul>
            </Card>
          ))}
        </section>
      )}

      {tab === "evolucao" && (
        evo.length === 0 ? <EmptyState icon={Dumbbell} title="Sem histórico" text="O gráfico aparece depois dos primeiros treinos registrados." /> : (
          <Card className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2>Carga por sessão</h2>
              <select className="input !w-auto" aria-label="Exercício" value={sel} onChange={(e) => setSel(Number(e.target.value))}>{evo.map((x, i) => <option key={x.exercise_id} value={i}>{x.exercise}</option>)}</select>
            </div>
            <p className="text-sm text-muted"><b className={ex.progression_pct > 0 ? "text-ok" : "text-ink"}>{ex.progression_pct > 0 ? "+" : ""}{num(ex.progression_pct)}%</b> desde a primeira sessão.</p>
            <LoadChart points={ex.points} />
          </Card>
        )
      )}

      {tab === "relatorio" && <ReportView alunoId={Number(id)} canEdit />}
    </>
  );
}
