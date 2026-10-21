import { useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { useAuth } from "../AuthContext";
import CheckinCard from "../components/Catraca";
import { useToast } from "../components/Toast";
import { Badge, EmptyState, ErrorState, Field, Modal, PageHeader, SkeletonList } from "../components/ui";
import { addDays, dayOf, dayShort, fmtFull, fmtTime, inputValue, mondayOf, todayISO, weekdayShort, zonedToUtc } from "../lib/format";
import { useFetch } from "../lib/hooks";
import api, { errMsg, STATUS } from "../services/api";

const BORDER = { AGENDADO: "border-l-brand", CHECKIN: "border-l-accent", CONCLUIDO: "border-l-ok", CANCELADO: "border-l-line opacity-60" };

export default function Agendamento() {
  const { user } = useAuth();
  const toast = useToast();
  const isPersonal = user.role === "personal";
  const [anchor, setAnchor] = useState(todayISO());
  const [form, setForm] = useState(null);
  const [detailId, setDetailId] = useState(null);

  const { data, loading, error, reload } = useFetch(async () => {
    const [s, a] = await Promise.all([api.get("/schedules"), isPersonal ? api.get("/users") : Promise.resolve({ data: [] })]);
    return { list: s.data, alunos: a.data };
  }, []);

  const monday = mondayOf(anchor);
  const days = Array.from({ length: 7 }, (_, i) => addDays(monday, i));
  const today = todayISO();
  const byDay = {};
  (data?.list || []).forEach((s) => { (byDay[dayOf(s.start_time)] ||= []).push(s); });
  const detail = data?.list.find((s) => s.id === detailId);

  function openNew(day) {
    const base = day && day !== today ? `${day}T09:00` : inputValue(new Date(Date.now() + 3600e3)).slice(0, 14) + "00";
    setForm({ aluno_id: "", when: base, duration_min: 60 });
  }
  async function create(e) {
    e.preventDefault();
    try {
      await api.post("/schedules", { start_time: zonedToUtc(form.when), duration_min: Number(form.duration_min), aluno_id: isPersonal ? Number(form.aluno_id) : null });
      toast("Aula agendada (horário de Brasília)");
      setForm(null);
      reload(true);
    } catch (err) { toast(errMsg(err), "error"); }
  }
  async function setStatus(id, status) {
    try { await api.patch(`/schedules/${id}/status`, { status }); toast(status === "CANCELADO" ? "Aula cancelada" : "Aula concluída"); reload(true); }
    catch (e) { toast(errMsg(e), "error"); }
  }

  const range = `${dayShort(days[0])} a ${dayShort(days[6])}`;
  return (
    <>
      <PageHeader title="Agenda" subtitle="Horários no fuso de Brasília."
        actions={<button className="btn" onClick={() => openNew()} disabled={isPersonal && !data?.alunos.length}><Plus size={16} />Nova aula</button>} />
      {error && <ErrorState message={error} onRetry={reload} />}
      {loading && !data && <SkeletonList rows={4} />}

      {data && (
        <>
          <div className="flex items-center gap-2">
            <button className="btn-ghost !px-2.5" onClick={() => setAnchor(addDays(monday, -7))} aria-label="Semana anterior"><ChevronLeft size={18} /></button>
            <button className="btn-ghost !px-2.5" onClick={() => setAnchor(addDays(monday, 7))} aria-label="Próxima semana"><ChevronRight size={18} /></button>
            <button className="btn-ghost" onClick={() => setAnchor(today)}>Hoje</button>
            <p className="ml-2 font-bold">Semana de {range}</p>
          </div>

          {data.list.length === 0 && (
            <EmptyState icon={CalendarDays} title="Nenhuma aula agendada" text={isPersonal ? "Marque a primeira aula com um aluno." : "Marque uma aula com seu personal."} action={<button className="btn" onClick={() => openNew()}>Agendar aula</button>} />
          )}

          <div className="grid gap-3 lg:grid-cols-7">
            {days.map((d) => (
              <section key={d} aria-label={`${weekdayShort(d)} ${dayShort(d)}`} className={`rounded-2xl border p-3 ${d === today ? "border-brand bg-brand-soft/40" : "border-line bg-white"}`}>
                <div className="mb-2 flex items-baseline justify-between lg:block">
                  <p className="text-xs font-semibold text-muted">{weekdayShort(d)}</p>
                  <p className={`text-lg font-extrabold ${d === today ? "text-brand-deeper" : ""}`}>{dayShort(d)}</p>
                </div>
                <div className="space-y-2">
                  {(byDay[d] || []).map((s) => (
                    <button key={s.id} onClick={() => setDetailId(s.id)} className={`w-full rounded-xl border border-line border-l-4 bg-white px-2.5 py-2 text-left text-sm shadow-sm hover:bg-paper ${BORDER[s.status]}`}>
                      <span className="block font-bold">{fmtTime(s.start_time)}</span>
                      <span className="block truncate text-xs text-muted">{isPersonal ? s.aluno_name : s.personal_name}</span>
                    </button>
                  ))}
                  {!(byDay[d] || []).length && <button onClick={() => openNew(d)} className="w-full rounded-xl border border-dashed border-line py-2 text-xs text-muted hover:bg-paper">+ marcar</button>}
                </div>
              </section>
            ))}
          </div>
        </>
      )}

      <Modal open={!!form} onClose={() => setForm(null)} title="Nova aula">
        {form && (
          <form onSubmit={create} className="space-y-4">
            {isPersonal && (
              <Field label="Aluno">
                <select className="input" value={form.aluno_id} onChange={(e) => setForm({ ...form, aluno_id: e.target.value })} required>
                  <option value="">Escolha...</option>{data.alunos.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </Field>
            )}
            <Field label="Data e hora (Brasília)"><input type="datetime-local" className="input" value={form.when} onChange={(e) => setForm({ ...form, when: e.target.value })} required step={900} /></Field>
            <Field label="Duração">
              <select className="input" value={form.duration_min} onChange={(e) => setForm({ ...form, duration_min: e.target.value })}>{[30, 45, 60, 90].map((m) => <option key={m} value={m}>{m} min</option>)}</select>
            </Field>
            <button className="btn-accent w-full">Agendar aula</button>
          </form>
        )}
      </Modal>

      <Modal open={!!detail} onClose={() => setDetailId(null)} title="Detalhes da aula">
        {detail && (
          <div className="space-y-4">
            <div>
              <p className="text-lg font-bold capitalize">{fmtFull(detail.start_time)}</p>
              <p className="text-sm text-muted">{isPersonal ? `Aluno: ${detail.aluno_name}` : `Personal: ${detail.personal_name}`} · {detail.duration_min} min</p>
              <div className="mt-2"><Badge tone={STATUS[detail.status].tone}>{STATUS[detail.status].label}</Badge></div>
              {detail.checkin_at && <p className="mt-2 text-xs text-muted">Check-in às {fmtTime(detail.checkin_at)}</p>}
            </div>
            {!isPersonal && detail.status === "AGENDADO" && <div className="border-t border-line pt-4"><CheckinCard scheduleId={detail.id} onDone={() => reload(true)} /></div>}
            <div className="flex flex-wrap gap-2 border-t border-line pt-4">
              {isPersonal && detail.status === "CHECKIN" && <button className="btn" onClick={() => setStatus(detail.id, "CONCLUIDO")}>Concluir aula</button>}
              {detail.status === "AGENDADO" && <button className="btn-danger" onClick={() => window.confirm("Cancelar esta aula?") && setStatus(detail.id, "CANCELADO")}>Cancelar aula</button>}
              <button className="btn-ghost ml-auto" onClick={() => setDetailId(null)}>Fechar</button>
            </div>
          </div>
        )}
      </Modal>
    </>
  );
}
