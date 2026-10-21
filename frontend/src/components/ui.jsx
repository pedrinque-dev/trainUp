import { Children, cloneElement, createContext, useContext, useEffect, useId, useRef } from "react";
import { X } from "lucide-react";

export function Card({ className = "", children, ...rest }) {
  return <section className={`card ${className}`} {...rest}>{children}</section>;
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <h1>{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}

const TONES = {
  neutral: "bg-paper text-muted ring-line",
  brand: "bg-brand-soft text-brand-deeper ring-brand/20",
  accent: "bg-accent-soft text-ink ring-accent/60",
  ok: "bg-accent-soft text-ok ring-accent/50",
  warn: "bg-amber-50 text-warn ring-amber-200",
  danger: "bg-red-50 text-danger ring-red-200",
};
export function Badge({ tone = "neutral", children, className = "" }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${TONES[tone]} ${className}`}>
      {children}
    </span>
  );
}

export function StatCard({ icon: Icon, label, value, hint, tone = "brand" }) {
  const box = { brand: "bg-brand-soft text-brand-deeper", accent: "bg-accent-soft text-ink", warn: "bg-amber-50 text-warn", neutral: "bg-paper text-muted" }[tone];
  return (
    <div className="card flex items-center gap-4">
      {Icon && <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${box}`}><Icon size={22} aria-hidden="true" /></span>}
      <div className="min-w-0">
        <p className="text-2xl font-extrabold leading-none text-ink">{value}</p>
        <p className="mt-1 text-sm text-muted">{label}</p>
        {hint && <p className="text-xs text-muted/80">{hint}</p>}
      </div>
    </div>
  );
}

export function EmptyState({ icon: Icon, title, text, action }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-line bg-white/60 px-6 py-10 text-center">
      {Icon && <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-soft text-brand-deeper"><Icon size={24} aria-hidden="true" /></span>}
      <h3 className="text-base">{title}</h3>
      {text && <p className="max-w-sm text-sm text-muted">{text}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function Skeleton({ className = "h-4 w-full" }) {
  return <div className={`animate-pulse rounded-lg bg-line/70 ${className}`} aria-hidden="true" />;
}
export function SkeletonList({ rows = 3 }) {
  return (
    <div className="space-y-3" role="status" aria-label="Carregando">
      {Array.from({ length: rows }, (_, i) => <Skeleton key={i} className="h-14 w-full" />)}
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-danger" role="alert">
      {message}
      {onRetry && <button className="ml-3 font-semibold underline" onClick={() => onRetry()}>Tentar de novo</button>}
    </div>
  );
}

export function ProgressBar({ value, max = 100, className = "" }) {
  const pct = Math.max(0, Math.min(100, max ? (value / max) * 100 : 0));
  return (
    <div className={`h-2.5 w-full overflow-hidden rounded-full bg-line ${className}`} role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
      <div className="h-full rounded-full bg-grad transition-all" style={{ width: `${pct}%` }} />
    </div>
  );
}

export function Field({ label, hint, children }) {
  const id = useId();
  const child = cloneElement(Children.only(children), { id });
  return (
    <div>
      <label htmlFor={id} className="label">{label}</label>
      {child}
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export function Tabs({ tabs, value, onChange }) {
  return (
    <div className="flex gap-1 overflow-x-auto rounded-xl bg-white p-1 ring-1 ring-line" role="tablist">
      {tabs.map((t) => (
        <button key={t.value} role="tab" aria-selected={value === t.value} onClick={() => onChange(t.value)}
          className={`whitespace-nowrap rounded-lg px-3.5 py-2 text-sm font-semibold transition ${value === t.value ? "bg-ink text-white" : "text-muted hover:text-ink"}`}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

/** Modal (centralizado no desktop, "bottom sheet" no celular). */
export function Modal({ open, onClose, title, children, wide = false }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    ref.current?.focus();
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = ""; };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-4">
      <div className="absolute inset-0 bg-ink/50" onClick={onClose} aria-hidden="true" />
      <div ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={title}
        className={`relative flex max-h-[92vh] w-full flex-col rounded-t-3xl bg-white shadow-xl sm:rounded-3xl ${wide ? "sm:max-w-3xl" : "sm:max-w-lg"}`}>
        <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-4">
          <h2>{title}</h2>
          <button className="rounded-lg p-1.5 text-muted hover:bg-paper" onClick={onClose} aria-label="Fechar"><X size={20} /></button>
        </div>
        <div className="overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </div>
  );
}
