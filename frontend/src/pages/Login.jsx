import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Dumbbell, LineChart, ShieldCheck } from "lucide-react";
import { useAuth } from "../AuthContext";
import { LogoFull } from "../components/Logo";
import { Field } from "../components/ui";
import api, { errMsg, GOALS } from "../services/api";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [mode, setMode] = useState("login"); // login | register | forgot | reset
  const [form, setForm] = useState({
    name: "", email: "", password: "", role: "aluno", goal: "ganho_massa", invite_code: params.get("convite") || "",
    signup_code: "", token: "",
  });
  const [msg, setMsg] = useState({ type: "", text: "" });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const go = (m) => { setMode(m); setMsg({ type: "", text: "" }); };

  async function submit(e) {
    e.preventDefault();
    setMsg({ type: "", text: "" });
    setBusy(true);
    try {
      if (mode === "forgot") {
        const { data } = await api.post("/auth/forgot", { email: form.email });
        setMsg({ type: "ok", text: data.detail });
        setMode("reset");
        return;
      }
      if (mode === "reset") {
        const { data } = await api.post("/auth/reset", { token: form.token, password: form.password });
        setMsg({ type: "ok", text: data.detail });
        setMode("login");
        return;
      }
      if (mode === "register") {
        const isAluno = form.role === "aluno";
        await api.post("/auth/register", {
          name: form.name, email: form.email, password: form.password, role: form.role,
          goal: isAluno ? form.goal : null,
          invite_code: isAluno && form.invite_code ? form.invite_code.trim().toUpperCase() : null,
          signup_code: !isAluno ? form.signup_code : null,
        });
      }
      const { data } = await api.post("/auth/login", { email: form.email, password: form.password });
      login(data);
      nav(data.user.role === "personal" ? "/personal" : "/aluno");
    } catch (err) {
      setMsg({ type: "error", text: errMsg(err) });
    } finally {
      setBusy(false);
    }
  }

  const titles = { login: "Entrar", register: "Criar conta", forgot: "Recuperar senha", reset: "Definir nova senha" };
  const cta = { login: "Entrar", register: "Criar conta e entrar", forgot: "Gerar token", reset: "Salvar nova senha" };

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-ink p-12 text-white lg:flex">
        <div className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-brand/20 blur-3xl" aria-hidden="true" />
        <div className="absolute -bottom-32 -left-16 h-96 w-96 rounded-full bg-accent/15 blur-3xl" aria-hidden="true" />
        <div className="relative rounded-2xl bg-white p-4 shadow-lg w-fit"><LogoFull className="h-12" /></div>
        <div className="relative max-w-md space-y-8">
          <h2 className="!text-4xl !leading-tight !text-white">Treinar com método é <span className="text-grad">evoluir</span> com prova.</h2>
          <ul className="space-y-4 text-white/85">
            {[[Dumbbell, "Fichas e execução guiadas, série a série."], [LineChart, "Relatórios de evolução em PDF para cada aluno."], [ShieldCheck, "Controle de acesso com catraca virtual."]].map(([Icon, t]) => (
              <li key={t} className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/10"><Icon size={18} /></span>{t}</li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-white/50">TrainUp · Projeto integrador</p>
      </aside>

      <main className="flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm space-y-6">
          <div className="lg:hidden"><LogoFull className="h-14" /></div>
          <div>
            {(mode === "forgot" || mode === "reset") && (
              <button onClick={() => go("login")} className="mb-3 inline-flex items-center gap-1 text-sm font-semibold text-brand-deeper"><ArrowLeft size={16} />Voltar</button>
            )}
            <h1>{titles[mode]}</h1>
            {mode === "login" && <p className="mt-1 text-sm text-muted">Acesse sua conta para continuar.</p>}
          </div>

          <form onSubmit={submit} className="space-y-4" noValidate={false}>
            {mode === "register" && (
              <>
                <Field label="Nome completo"><input className="input" value={form.name} onChange={set("name")} required minLength={2} autoComplete="name" /></Field>
                <Field label="Perfil">
                  <select className="input" value={form.role} onChange={set("role")}>
                    <option value="aluno">Sou aluno</option>
                    <option value="personal">Sou Personal Trainer</option>
                  </select>
                </Field>
                {form.role === "aluno" ? (
                  <>
                    <Field label="Objetivo">
                      <select className="input" value={form.goal} onChange={set("goal")}>
                        {Object.entries(GOALS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                      </select>
                    </Field>
                    <Field label="Código de convite do personal (opcional)" hint="Se você ainda não tem, peça ao seu personal. Dá para informar depois.">
                      <input className="input uppercase" value={form.invite_code} onChange={set("invite_code")} maxLength={12} placeholder="EX.: TRAIN123" />
                    </Field>
                  </>
                ) : (
                  <Field label="Código de cadastro de personal" hint="Fornecido pelo administrador do sistema.">
                    <input className="input" value={form.signup_code} onChange={set("signup_code")} required />
                  </Field>
                )}
              </>
            )}
            {mode === "reset" && (
              <Field label="Token de recuperação" hint="No MVP, o token aparece no log do backend: docker compose logs backend">
                <input className="input" value={form.token} onChange={set("token")} required autoComplete="one-time-code" />
              </Field>
            )}
            {mode !== "reset" && (
              <Field label="E-mail"><input type="email" className="input" value={form.email} onChange={set("email")} required autoComplete="email" /></Field>
            )}
            {mode !== "forgot" && (
              <Field label={mode === "reset" ? "Nova senha" : "Senha"} hint={mode !== "login" ? "Mínimo de 8 caracteres, com letras e números." : undefined}>
                <input type="password" className="input" value={form.password} onChange={set("password")} required minLength={mode === "login" ? 1 : 8}
                  autoComplete={mode === "login" ? "current-password" : "new-password"} />
              </Field>
            )}
            {msg.text && (
              <p className={`rounded-xl px-3 py-2 text-sm ${msg.type === "error" ? "bg-red-50 text-danger" : "bg-accent-soft text-ink"}`} role={msg.type === "error" ? "alert" : "status"}>{msg.text}</p>
            )}
            <button className="btn w-full py-3" disabled={busy}>{busy ? "Aguarde..." : cta[mode]}</button>
          </form>

          {mode === "login" && (
            <div className="space-y-2 text-center text-sm">
              <button className="font-semibold text-brand-deeper" onClick={() => go("forgot")}>Esqueci minha senha</button>
              <p className="text-muted">Ainda não tem conta? <button className="font-semibold text-brand-deeper" onClick={() => go("register")}>Cadastre-se</button></p>
            </div>
          )}
          {mode === "register" && (
            <p className="text-center text-sm text-muted">Já tem conta? <button className="font-semibold text-brand-deeper" onClick={() => go("login")}>Entrar</button></p>
          )}
        </div>
      </main>
    </div>
  );
}
