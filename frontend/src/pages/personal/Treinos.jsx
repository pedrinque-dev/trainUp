import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Dumbbell, Pencil, Plus, Trash2 } from "lucide-react";
import { useToast } from "../../components/Toast";
import { Badge, Card, EmptyState, ErrorState, Field, Modal, PageHeader, SkeletonList } from "../../components/ui";
import { num } from "../../lib/format";
import { useFetch } from "../../lib/hooks";
import api, { errMsg, WEEK } from "../../services/api";

const blankItem = () => ({ exercise_id: "", sets: 3, reps: 10, target_load: 0 });
const blank = (aluno_id = "") => ({ id: null, aluno_id, name: "", weekday: "", items: [blankItem()] });

export default function Treinos() {
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const [filter, setFilter] = useState(params.get("aluno") || "");
  const [form, setForm] = useState(null);

  const { data, loading, error, reload } = useFetch(async () => {
    const [a, e, w] = await Promise.all([api.get("/users"), api.get("/exercises"), api.get("/workouts")]);
    return { alunos: a.data, exercises: e.data, workouts: w.data };
  }, []);

  useEffect(() => {
    if (params.get("novo") && data) { setForm(blank(params.get("aluno") || "")); setParams({}, { replace: true }); }
  }, [params, data, setParams]);

  const aluno = (id) => data.alunos.find((a) => a.id === id)?.name ?? `#${id}`;
  const setItem = (i, k, v) => setForm((f) => ({ ...f, items: f.items.map((it, n) => (n === i ? { ...it, [k]: v } : it)) }));
  const edit = (w) => setForm({ id: w.id, aluno_id: w.aluno_id, name: w.name, weekday: w.weekday ?? "", items: w.items.map((i) => ({ exercise_id: i.exercise.id, sets: i.sets, reps: i.reps, target_load: i.target_load })) });

  async function save(e) {
    e.preventDefault();
    const body = {
      name: form.name, aluno_id: Number(form.aluno_id), weekday: form.weekday === "" ? null : Number(form.weekday),
      items: form.items.map((i) => ({ exercise_id: Number(i.exercise_id), sets: Number(i.sets), reps: Number(i.reps), target_load: Number(i.target_load) })),
    };
    try {
      if (form.id) await api.put(`/workouts/${form.id}`, body); else await api.post("/workouts", body);
      toast(form.id ? "Ficha atualizada" : "Ficha criada");
      setForm(null);
      reload(true);
    } catch (err) { toast(errMsg(err), "error"); }
  }
  async function remove(w) {
    if (!window.confirm(`Excluir "${w.name}"?`)) return;
    try { await api.delete(`/workouts/${w.id}`); toast("Ficha excluída"); reload(true); } catch (e) { toast(errMsg(e), "error"); }
  }

  const list = (data?.workouts || []).filter((w) => !filter || String(w.aluno_id) === filter);
  return (
    <>
      <PageHeader title="Treinos" subtitle="Fichas de treino por aluno."
        actions={<button className="btn" onClick={() => setForm(blank(filter))} disabled={!data?.alunos.length}><Plus size={16} />Nova ficha</button>} />
      {error && <ErrorState message={error} onRetry={reload} />}
      {loading && !data && <SkeletonList rows={3} />}
      {data && (
        <>
          <select className="input !w-auto" aria-label="Filtrar por aluno" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="">Todos os alunos</option>
            {data.alunos.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
          {list.length === 0 ? (
            <EmptyState icon={Dumbbell} title="Nenhuma ficha encontrada" text={data.alunos.length ? "Crie uma ficha para começar." : "Cadastre ou aceite um aluno antes de criar fichas."} />
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {list.map((w) => (
                <Card key={w.id} className="flex flex-col gap-3">
                  <div className="flex items-start justify-between gap-3">
                    <div><h3>{w.name}</h3><p className="text-sm text-muted">{aluno(w.aluno_id)}</p></div>
                    <Badge>{w.weekday == null ? "Qualquer dia" : WEEK[w.weekday]}</Badge>
                  </div>
                  <ul className="flex-1 space-y-1 text-sm">
                    {w.items.map((i) => <li key={i.id} className="flex justify-between gap-3"><span>{i.exercise.name}</span><span className="text-muted">{i.sets}x{i.reps} · {num(i.target_load)} kg</span></li>)}
                  </ul>
                  <div className="flex gap-2">
                    <button className="btn-ghost" onClick={() => edit(w)}><Pencil size={15} />Editar</button>
                    <button className="btn-danger" onClick={() => remove(w)}><Trash2 size={15} />Excluir</button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      <Modal open={!!form} onClose={() => setForm(null)} title={form?.id ? "Editar ficha" : "Nova ficha"} wide>
        {form && (
          <form onSubmit={save} className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="Aluno">
                <select className="input" value={form.aluno_id} onChange={(e) => setForm({ ...form, aluno_id: e.target.value })} required disabled={!!form.id}>
                  <option value="">Escolha...</option>{data.alunos.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </Field>
              <Field label="Nome da ficha"><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required minLength={2} placeholder="Treino A · Superiores" /></Field>
              <Field label="Dia da semana">
                <select className="input" value={form.weekday} onChange={(e) => setForm({ ...form, weekday: e.target.value })}>
                  <option value="">Qualquer dia</option>{WEEK.map((d, i) => <option key={d} value={i}>{d}</option>)}
                </select>
              </Field>
            </div>
            <div className="space-y-3">
              {form.items.map((it, i) => (
                <div key={i} className="rounded-xl border border-line p-3">
                  <div className="grid grid-cols-3 gap-2 sm:grid-cols-[1fr_5rem_5rem_6rem_auto] sm:items-end">
                    <div className="col-span-3 sm:col-span-1"><Field label="Exercício">
                      <select className="input" value={it.exercise_id} onChange={(e) => setItem(i, "exercise_id", e.target.value)} required>
                        <option value="">Escolha...</option>{data.exercises.map((x) => <option key={x.id} value={x.id}>{x.name} ({x.muscle_group})</option>)}
                      </select></Field></div>
                    <Field label="Séries"><input className="input" type="number" min="1" max="20" value={it.sets} onChange={(e) => setItem(i, "sets", e.target.value)} /></Field>
                    <Field label="Reps"><input className="input" type="number" min="1" max="100" value={it.reps} onChange={(e) => setItem(i, "reps", e.target.value)} /></Field>
                    <Field label="Carga (kg)"><input className="input" type="number" min="0" step="0.5" value={it.target_load} onChange={(e) => setItem(i, "target_load", e.target.value)} /></Field>
                    <button type="button" className="btn-ghost col-span-3 sm:col-span-1" disabled={form.items.length === 1} onClick={() => setForm({ ...form, items: form.items.filter((_, n) => n !== i) })}>Remover</button>
                  </div>
                </div>
              ))}
              <button type="button" className="btn-ghost" onClick={() => setForm({ ...form, items: [...form.items, blankItem()] })}><Plus size={15} />Adicionar exercício</button>
            </div>
            <div className="flex justify-end gap-2 border-t border-line pt-4">
              <button type="button" className="btn-ghost" onClick={() => setForm(null)}>Cancelar</button>
              <button className="btn-accent">Salvar ficha</button>
            </div>
          </form>
        )}
      </Modal>
    </>
  );
}
