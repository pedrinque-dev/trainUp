import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check, ChevronRight, Copy, Search, UserPlus, Users, X } from "lucide-react";
import { useAuth } from "../../AuthContext";
import { useToast } from "../../components/Toast";
import { Badge, Card, EmptyState, ErrorState, Field, Modal, PageHeader, SkeletonList } from "../../components/ui";
import { initials } from "../../lib/format";
import { useFetch } from "../../lib/hooks";
import api, { errMsg, GOALS } from "../../services/api";

export default function Alunos() {
  const { user } = useAuth();
  const toast = useToast();
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const [invite, setInvite] = useState(false);
  const [manual, setManual] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", goal: "ganho_massa" });

  const { data, loading, error, reload } = useFetch(async () => {
    const [a, p, s] = await Promise.all([api.get("/users"), api.get("/links/pending"), api.get("/analytics/stagnation")]);
    return { alunos: a.data, pending: p.data, alerts: s.data };
  }, []);

  const link = `${window.location.origin}/login?convite=${user.invite_code}`;
  const copy = async (text) => { try { await navigator.clipboard.writeText(text); toast("Copiado!"); } catch { toast("Não foi possível copiar", "error"); } };
  const respond = async (id, accept) => {
    try { await api.post(`/links/${id}/respond`, { accept }); toast(accept ? "Aluno vinculado" : "Solicitação recusada"); reload(true); }
    catch (e) { toast(errMsg(e), "error"); }
  };
  async function create(e) {
    e.preventDefault();
    try {
      await api.post("/users", form);
      toast("Aluno cadastrado");
      setManual(false);
      setForm({ name: "", email: "", password: "", goal: "ganho_massa" });
      reload(true);
    } catch (err) { toast(errMsg(err), "error"); }
  }

  const alunos = (data?.alunos || []).filter((a) => `${a.name} ${a.email}`.toLowerCase().includes(q.toLowerCase()));
  const alertCount = (id) => data?.alerts.filter((a) => a.aluno_id === id).length || 0;

  return (
    <>
      <PageHeader title="Alunos" subtitle="Gerencie vínculos, fichas e evolução."
        actions={<><button className="btn-ghost" onClick={() => setManual(true)}>Cadastrar manualmente</button><button className="btn" onClick={() => setInvite(true)}><UserPlus size={16} />Convidar aluno</button></>} />
      {error && <ErrorState message={error} onRetry={reload} />}
      {loading && !data && <SkeletonList rows={4} />}

      {data?.pending.length > 0 && (
        <section aria-labelledby="pend" className="space-y-2">
          <h2 id="pend">Solicitações de vínculo <Badge tone="accent">{data.pending.length}</Badge></h2>
          <Card className="divide-y divide-line !p-0">
            {data.pending.map((p) => (
              <div key={p.id} className="flex flex-wrap items-center gap-3 px-4 py-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-soft text-sm font-bold text-brand-deeper">{initials(p.aluno_name)}</span>
                <div className="min-w-0 flex-1"><p className="font-semibold">{p.aluno_name}</p><p className="truncate text-xs text-muted">{p.aluno_email}</p></div>
                <button className="btn-ghost" onClick={() => respond(p.id, false)}><X size={15} />Recusar</button>
                <button className="btn" onClick={() => respond(p.id, true)}><Check size={15} />Aceitar</button>
              </div>
            ))}
          </Card>
        </section>
      )}

      {data && (data.alunos.length === 0 ? (
        <EmptyState icon={Users} title="Você ainda não tem alunos"
          text={`Compartilhe seu código de convite ${user.invite_code} para o aluno solicitar o vínculo, ou cadastre-o manualmente.`}
          action={<button className="btn" onClick={() => setInvite(true)}>Ver código de convite</button>} />
      ) : (
        <>
          <div className="relative">
            <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
            <input className="input !pl-10" placeholder="Buscar aluno por nome ou e-mail" aria-label="Buscar aluno" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <Card className="divide-y divide-line !p-0">
            {alunos.map((a) => (
              <button key={a.id} onClick={() => nav(`/personal/alunos/${a.id}`)} className="flex w-full items-center gap-3 px-4 py-3.5 text-left hover:bg-paper">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-soft text-sm font-bold text-brand-deeper">{initials(a.name)}</span>
                <div className="min-w-0 flex-1"><p className="font-semibold">{a.name}</p><p className="truncate text-xs text-muted">{GOALS[a.goal] || "Sem objetivo"} · {a.email}</p></div>
                {alertCount(a.id) > 0 && <Badge tone="warn">{alertCount(a.id)} alerta(s)</Badge>}
                <ChevronRight size={18} className="text-muted" aria-hidden="true" />
              </button>
            ))}
            {alunos.length === 0 && <p className="px-4 py-6 text-center text-sm text-muted">Nenhum aluno encontrado para "{q}".</p>}
          </Card>
        </>
      ))}

      <Modal open={invite} onClose={() => setInvite(false)} title="Convidar aluno">
        <div className="space-y-4">
          <p className="text-sm text-muted">O aluno informa este código ao se cadastrar (ou depois, na tela inicial). Você aprova cada solicitação antes de o vínculo ficar ativo.</p>
          <div className="flex items-center justify-between rounded-2xl bg-paper px-5 py-4">
            <span className="text-3xl font-extrabold tracking-widest text-ink">{user.invite_code}</span>
            <button className="btn-ghost" onClick={() => copy(user.invite_code)}><Copy size={15} />Copiar</button>
          </div>
          <Field label="Link de cadastro com o código preenchido">
            <div className="flex gap-2"><input className="input" readOnly value={link} onFocus={(e) => e.target.select()} /><button className="btn-ghost shrink-0" type="button" onClick={() => copy(link)} aria-label="Copiar link"><Copy size={15} /></button></div>
          </Field>
        </div>
      </Modal>

      <Modal open={manual} onClose={() => setManual(false)} title="Cadastrar aluno">
        <form onSubmit={create} className="space-y-4">
          <Field label="Nome"><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required minLength={2} /></Field>
          <Field label="E-mail"><input type="email" className="input" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></Field>
          <Field label="Senha inicial" hint="Mínimo de 8 caracteres, com letras e números. Informe ao aluno por fora."><input type="password" className="input" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} autoComplete="new-password" /></Field>
          <Field label="Objetivo">
            <select className="input" value={form.goal} onChange={(e) => setForm({ ...form, goal: e.target.value })}>{Object.entries(GOALS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
          </Field>
          <button className="btn w-full">Cadastrar aluno</button>
        </form>
      </Modal>
    </>
  );
}
