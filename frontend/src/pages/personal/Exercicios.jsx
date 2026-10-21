import { useState } from "react";
import { BookOpen, ExternalLink, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useToast } from "../../components/Toast";
import { Badge, Card, EmptyState, ErrorState, Field, Modal, PageHeader, SkeletonList, Tabs } from "../../components/ui";
import { useFetch } from "../../lib/hooks";
import api, { errMsg, MUSCLE_GROUPS } from "../../services/api";

const blank = { id: null, name: "", muscle_group: "Peito", description: "", video_url: "" };

export default function Exercicios() {
  const toast = useToast();
  const [tab, setTab] = useState("base");
  const [q, setQ] = useState("");
  const [group, setGroup] = useState("");
  const [form, setForm] = useState(null);
  const { data, loading, error, reload } = useFetch(async () => (await api.get("/exercises")).data, []);

  async function save(e) {
    e.preventDefault();
    const body = { name: form.name, muscle_group: form.muscle_group, description: form.description, video_url: form.video_url || null };
    try {
      if (form.id) await api.put(`/exercises/${form.id}`, body); else await api.post("/exercises", body);
      toast(form.id ? "Exercício atualizado" : "Exercício criado");
      setForm(null);
      setTab("meus");
      reload(true);
    } catch (err) { toast(errMsg(err), "error"); }
  }
  async function remove(x) {
    if (!window.confirm(`Excluir "${x.name}"?`)) return;
    try { await api.delete(`/exercises/${x.id}`); toast("Exercício excluído"); reload(true); } catch (e) { toast(errMsg(e), "error"); }
  }

  const base = (data || []).filter((x) => x.is_base);
  const mine = (data || []).filter((x) => !x.is_base);
  const list = (tab === "base" ? base : mine).filter((x) => (!group || x.muscle_group === group) && x.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <>
      <PageHeader title="Exercícios" subtitle="Catálogo base do sistema e a sua biblioteca."
        actions={<button className="btn" onClick={() => setForm(blank)}><Plus size={16} />Novo exercício</button>} />
      {error && <ErrorState message={error} onRetry={reload} />}
      {loading && !data && <SkeletonList rows={5} />}
      {data && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <Tabs value={tab} onChange={setTab} tabs={[{ value: "base", label: `Catálogo base (${base.length})` }, { value: "meus", label: `Meus exercícios (${mine.length})` }]} />
            <div className="relative min-w-48 flex-1">
              <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
              <input className="input !pl-10" placeholder="Buscar exercício" aria-label="Buscar exercício" value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
            <select className="input !w-auto" aria-label="Grupo muscular" value={group} onChange={(e) => setGroup(e.target.value)}>
              <option value="">Todos os grupos</option>{MUSCLE_GROUPS.map((g) => <option key={g}>{g}</option>)}
            </select>
          </div>
          {list.length === 0 ? (
            <EmptyState icon={BookOpen} title={tab === "meus" && !mine.length ? "Sua biblioteca está vazia" : "Nada encontrado"}
              text={tab === "meus" && !mine.length ? "Crie exercícios próprios; os do catálogo base já podem ser usados nas fichas." : "Ajuste a busca ou o grupo muscular."}
              action={tab === "meus" && !mine.length && <button className="btn" onClick={() => setForm(blank)}>Criar exercício</button>} />
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {list.map((x) => (
                <Card key={x.id} className="flex flex-col gap-2">
                  <div className="flex items-start justify-between gap-3"><h3 className="text-base">{x.name}</h3><Badge tone={x.is_base ? "neutral" : "brand"}>{x.muscle_group}</Badge></div>
                  <p className="flex-1 text-sm text-muted">{x.description || "Sem descrição."}</p>
                  <div className="flex flex-wrap items-center gap-2">
                    {x.video_url && <a href={x.video_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm font-semibold text-brand-deeper"><ExternalLink size={14} />Ver vídeo</a>}
                    {!x.is_base && (
                      <span className="ml-auto flex gap-2">
                        <button className="btn-ghost" onClick={() => setForm({ ...x, video_url: x.video_url || "" })}><Pencil size={14} />Editar</button>
                        <button className="btn-danger" onClick={() => remove(x)} aria-label={`Excluir ${x.name}`}><Trash2 size={14} /></button>
                      </span>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      <Modal open={!!form} onClose={() => setForm(null)} title={form?.id ? "Editar exercício" : "Novo exercício"}>
        {form && (
          <form onSubmit={save} className="space-y-4">
            <Field label="Nome"><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required minLength={2} /></Field>
            <Field label="Grupo muscular"><select className="input" value={form.muscle_group} onChange={(e) => setForm({ ...form, muscle_group: e.target.value })}>{MUSCLE_GROUPS.map((g) => <option key={g}>{g}</option>)}</select></Field>
            <Field label="Como executar"><textarea className="input min-h-24" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} maxLength={500} /></Field>
            <Field label="Link de vídeo (opcional)"><input type="url" className="input" value={form.video_url} onChange={(e) => setForm({ ...form, video_url: e.target.value })} placeholder="https://" /></Field>
            <button className="btn w-full">Salvar exercício</button>
          </form>
        )}
      </Modal>
    </>
  );
}
