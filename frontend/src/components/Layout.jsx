import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  Activity, BookOpen, CalendarDays, Dumbbell, FileText, Home, LayoutDashboard, LogOut, MoreHorizontal, TrendingUp, Users,
} from "lucide-react";
import { useAuth } from "../AuthContext";
import { initials } from "../lib/format";
import { LogoMark, Wordmark } from "./Logo";
import { Modal } from "./ui";

const PERSONAL = [
  { to: "/personal", label: "Visão geral", icon: LayoutDashboard, end: true },
  { to: "/personal/alunos", label: "Alunos", icon: Users },
  { to: "/personal/treinos", label: "Treinos", icon: Dumbbell },
  { to: "/agendamento", label: "Agenda", icon: CalendarDays },
  { to: "/personal/exercicios", label: "Exercícios", icon: BookOpen },
  { to: "/personal/relatorios", label: "Relatórios", icon: FileText },
  { to: "/automacao", label: "Catraca", icon: Activity },
];
const ALUNO = [
  { to: "/aluno", label: "Início", icon: Home, end: true },
  { to: "/aluno/treinar", label: "Treinar", icon: Dumbbell },
  { to: "/aluno/evolucao", label: "Evolução", icon: TrendingUp },
  { to: "/agendamento", label: "Agenda", icon: CalendarDays },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [more, setMore] = useState(false);
  const items = user.role === "personal" ? PERSONAL : ALUNO;
  const bottom = user.role === "personal" ? items.slice(0, 4) : items;
  const extra = user.role === "personal" ? items.slice(4) : [];
  const out = () => { logout(); nav("/login"); };

  return (
    <div className="min-h-screen">
      {/* Sidebar (desktop) */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col bg-ink px-4 py-5 lg:flex">
        <div className="flex items-center gap-2.5 px-2 pb-6">
          <LogoMark size={38} /><Wordmark dark />
        </div>
        <nav className="flex flex-1 flex-col gap-1" aria-label="Principal">
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end}
              className={({ isActive }) => `group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition ${isActive ? "bg-white/10 text-white" : "text-white/70 hover:bg-white/5 hover:text-white"}`}>
              {({ isActive }) => (<>
                {isActive && <span className="absolute -left-4 top-2 bottom-2 w-1 rounded-r bg-grad" />}
                <Icon size={19} aria-hidden="true" />{label}
              </>)}
            </NavLink>
          ))}
        </nav>
        <div className="flex items-center gap-3 rounded-xl bg-white/5 p-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-grad text-sm font-bold text-ink">{initials(user.name)}</span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-white">{user.name}</p>
            <p className="text-xs text-white/60">{user.role === "personal" ? "Personal Trainer" : "Aluno"}</p>
          </div>
          <button onClick={out} className="rounded-lg p-2 text-white/70 hover:bg-white/10 hover:text-white" aria-label="Sair"><LogOut size={18} /></button>
        </div>
      </aside>

      {/* Barra superior (mobile) */}
      <header className="sticky top-0 z-30 flex items-center justify-between bg-ink px-4 py-2.5 lg:hidden">
        <div className="flex items-center gap-2"><LogoMark size={30} /><Wordmark dark className="!text-lg" /></div>
        {user.role === "aluno" && (
          <button onClick={out} className="rounded-lg p-2 text-white/80 hover:bg-white/10" aria-label="Sair"><LogOut size={19} /></button>
        )}
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6 pb-28 lg:ml-64 lg:px-8 lg:pb-10">{children}</main>

      {/* Barra inferior (mobile) */}
      <nav className="fixed inset-x-0 bottom-0 z-30 grid border-t border-line bg-white pb-[env(safe-area-inset-bottom)] lg:hidden"
        style={{ gridTemplateColumns: `repeat(${bottom.length + (extra.length ? 1 : 0)}, minmax(0, 1fr))` }} aria-label="Principal">
        {bottom.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) => `flex flex-col items-center gap-0.5 py-2 text-[11px] font-semibold ${isActive ? "text-brand-deeper" : "text-muted"}`}>
            <Icon size={21} aria-hidden="true" />{label}
          </NavLink>
        ))}
        {extra.length > 0 && (
          <button onClick={() => setMore(true)} className="flex flex-col items-center gap-0.5 py-2 text-[11px] font-semibold text-muted">
            <MoreHorizontal size={21} aria-hidden="true" />Mais
          </button>
        )}
      </nav>

      <Modal open={more} onClose={() => setMore(false)} title="Mais opções">
        <div className="space-y-1">
          {extra.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} onClick={() => setMore(false)} className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold hover:bg-paper">
              <Icon size={20} className="text-brand-deeper" aria-hidden="true" />{label}
            </NavLink>
          ))}
          <button onClick={out} className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-danger hover:bg-red-50">
            <LogOut size={20} aria-hidden="true" />Sair da conta
          </button>
        </div>
      </Modal>
    </div>
  );
}
