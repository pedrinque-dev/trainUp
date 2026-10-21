import { useEffect, useState } from "react";
import { AlertTriangle, CalendarCheck, Download, Dumbbell, Trophy } from "lucide-react";
import api, { downloadFile, errMsg } from "../services/api";
import { addDays, dayLong, fmtFull, num, todayISO } from "../lib/format";
import { useFetch } from "../lib/hooks";
import { LoadChart, VolumeChart } from "./charts";
import { useToast } from "./Toast";
import { Badge, Card, EmptyState, ErrorState, Field, SkeletonList, StatCard } from "./ui";

const PRESETS = [
  { value: "7", label: "7 dias" },
  { value: "30", label: "30 dias" },
  { value: "90", label: "3 meses" },
  { value: "custom", label: "Personalizado" },
];

/** Relatório de evolução com pré-visualização, seleção de período, download em PDF e observação do personal. */
export default function ReportView({ alunoId, canEdit = false }) {
  const toast = useToast();
  const [preset, setPreset] = useState("30");
  const [range, setRange] = useState({ start: addDays(todayISO(), -29), end: todayISO() });
  const [sel, setSel] = useState(0);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (preset !== "custom") setRange({ start: addDays(todayISO(), -(Number(preset) - 1)), end: todayISO() });
  }, [preset]);

  const { data: r, loading, error, reload } = useFetch(
    async () => (await api.get(`/reports/aluno/${alunoId}`, { params: range })).data,
    [alunoId, range.start, range.end]
  );
  useEffect(() => { setNote(r?.note?.text || ""); }, [r]);
  useEffect(() => { setSel(0); }, [alunoId, range.start, range.end]);

  async function pdf() {
    setBusy(true);
    try {
      await downloadFile(`/reports/aluno/${alunoId}/pdf?start=${range.start}&end=${range.end}`, `relatorio-trainup-${range.start}_${range.end}.pdf`);
    } catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  }
  async function saveNote() {
    try { await api.put(`/reports/aluno/${alunoId}/note`, { text: note }); toast("Observação salva"); reload(true); }
    catch (e) { toast(errMsg(e), "error"); }
  }

  const ex = r?.exercises?.[sel];
  return (
    <div className="space-y-5">
      <Card className="flex flex-wrap items-end gap-3">
        <div className="flex gap-1 rounded-xl bg-paper p-1" role="group" aria-label="Período">
          {PRESETS.map((p) => (
            <button key={p.value} onClick={() => setPreset(p.value)} aria-pressed={preset === p.value}
              className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${preset === p.value ? "bg-white text-ink shadow-sm" : "text-muted"}`}>{p.label}</button>
          ))}
        </div>
        {preset === "custom" && (
          <>
            <Field label="De"><input type="date" className="input !w-auto" value={range.start} max={range.end} onChange={(e) => setRange({ ...range, start: e.target.value })} /></Field>
            <Field label="Até"><input type="date" className="input !w-auto" value={range.end} min={range.start} max={todayISO()} onChange={(e) => setRange({ ...range, end: e.target.value })} /></Field>
          </>
        )}
        <button className="btn-accent ml-auto" onClick={pdf} disabled={busy || !r}><Download size={16} />{busy ? "Gerando..." : "Baixar PDF"}</button>
      </Card>

      {loading && !r && <SkeletonList rows={4} />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {r && (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <StatCard icon={Dumbbell} label="Sessões de treino" value={r.attendance.sessoes} hint={`${num(r.attendance.sessoes_por_semana)} por semana`} />
            <StatCard icon={CalendarCheck} tone="accent" label="Presença nas aulas" value={r.attendance.presenca_pct != null ? `${r.attendance.presenca_pct}%` : "-"}
              hint={`${r.attendance.realizadas} realizadas · ${r.attendance.canceladas} canceladas · ${r.attendance.faltas} faltas`} />
            <StatCard icon={Trophy} tone="accent" label="Recordes pessoais" value={r.records.length} hint={r.records.slice(0, 2).join(", ") || "Nenhum no período"} />
          </div>

          <Card className="border-l-4 border-l-brand">
            <p className="text-xs font-semibold text-muted">Resumo · {dayLong(r.period.start)} a {dayLong(r.period.end)}</p>
            <p className="mt-1 text-[15px] leading-relaxed">{r.summary_text}</p>
            {r.stagnant.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {r.stagnant.map((s) => <Badge key={s.exercise} tone="warn"><AlertTriangle size={12} />{s.exercise}: {s.streak} sessões sem recorde</Badge>)}
              </div>
            )}
          </Card>

          {r.exercises.length === 0 ? (
            <EmptyState icon={Dumbbell} title="Sem treinos neste período" text="Escolha outro período ou aguarde os primeiros treinos serem registrados." />
          ) : (
            <>
              <Card className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h2>Evolução de carga</h2>
                  <select className="input !w-auto" aria-label="Exercício" value={sel} onChange={(e) => setSel(Number(e.target.value))}>
                    {r.exercises.map((x, i) => <option key={x.exercise_id} value={i}>{x.exercise}</option>)}
                  </select>
                </div>
                {ex && (
                  <p className="text-sm text-muted">
                    <b className={ex.progression_pct > 0 ? "text-ok" : "text-ink"}>{ex.progression_pct > 0 ? "+" : ""}{num(ex.progression_pct)}%</b>{" "}
                    entre a primeira e a última sessão ({num(ex.first_load)} → {num(ex.last_load)} kg).
                  </p>
                )}
                {ex && <LoadChart points={ex.points} />}
              </Card>

              <Card className="space-y-3">
                <h2>Volume semanal</h2>
                <VolumeChart data={r.weekly_volume} />
              </Card>

              <Card className="overflow-hidden !p-0">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[640px] text-left text-sm">
                    <thead className="bg-paper text-xs text-muted">
                      <tr>{["Exercício", "Sessões", "Inicial", "Final", "Máx.", "Progressão", "Volume", ""].map((h) => <th key={h} className="px-4 py-3 font-semibold">{h}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                      {r.exercises.map((x) => (
                        <tr key={x.exercise_id}>
                          <td className="px-4 py-3 font-semibold">{x.exercise}</td>
                          <td className="px-4 py-3">{x.sessions}</td>
                          <td className="px-4 py-3">{num(x.first_load)} kg</td>
                          <td className="px-4 py-3">{num(x.last_load)} kg</td>
                          <td className="px-4 py-3">{num(x.max_load)} kg</td>
                          <td className={`px-4 py-3 font-semibold ${x.progression_pct > 0 ? "text-ok" : "text-muted"}`}>{x.progression_pct > 0 ? "+" : ""}{num(x.progression_pct)}%</td>
                          <td className="px-4 py-3">{num(x.total_volume, 0)} kg</td>
                          <td className="px-4 py-3">{x.record ? <Badge tone="accent"><Trophy size={12} />Recorde</Badge> : x.stagnant ? <Badge tone="warn">Estagnado</Badge> : null}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </>
          )}

          <Card className="space-y-3">
            <h2>Observações do personal</h2>
            {canEdit ? (
              <>
                <textarea className="input min-h-28" value={note} onChange={(e) => setNote(e.target.value)} maxLength={2000}
                  placeholder="Recomendações, ajustes de ficha, pontos de atenção... (entra no PDF)" aria-label="Observações do personal" />
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted">{r.note ? `Atualizado em ${fmtFull(r.note.updated_at)}` : "Ainda sem observação"}</span>
                  <button className="btn" onClick={saveNote}>Salvar observação</button>
                </div>
              </>
            ) : (
              <p className="whitespace-pre-line text-sm text-ink/85">{r.note?.text || "Seu personal ainda não deixou observações."}</p>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
