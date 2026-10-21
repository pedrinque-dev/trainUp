import { useEffect, useState } from "react";
import { Lock, ShieldAlert, Unlock } from "lucide-react";
import { useInterval } from "../lib/hooks";
import api, { errMsg } from "../services/api";

const LOOK = {
  TRAVADA: { Icon: Lock, bg: "bg-danger", label: "Travada" },
  VALIDANDO: { Icon: Lock, bg: "bg-amber-500", label: "Validando" },
  LIBERADA: { Icon: Unlock, bg: "bg-ok", label: "Liberada" },
  AGUARDANDO_PASSAGEM: { Icon: Unlock, bg: "bg-ok", label: "Liberada: aguardando passagem" },
  BLOQUEIO: { Icon: ShieldAlert, bg: "bg-danger", label: "Bloqueada" },
};

/** Check-in do aluno na catraca virtual (simulação). O aluno vê só o estado e o resultado. */
export default function CheckinCard({ scheduleId, onDone }) {
  const [snap, setSnap] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => api.get("/automacao/status").then((r) => setSnap(r.data.turnstile)).catch(() => {});
  useEffect(() => { load(); }, []);
  useInterval(load, 2000);

  async function checkin() {
    setBusy(true);
    try {
      const { data } = await api.post("/automacao/checkin", { schedule_id: scheduleId });
      setResult({ granted: data.granted, text: data.granted ? "Acesso liberado. Passe pela catraca." : `Acesso negado: ${data.reason}` });
      setSnap(data.turnstile);
      onDone?.();
    } catch (e) {
      setResult({ granted: false, text: errMsg(e) });
    } finally { setBusy(false); }
  }
  async function passagem() {
    try { const { data } = await api.post("/automacao/passagem", {}); setSnap(data.turnstile); setResult({ granted: true, text: "Passagem registrada. Bom treino!" }); } catch { /* ignora */ }
  }

  const look = LOOK[snap?.state] || LOOK.TRAVADA;
  const open = snap?.state === "AGUARDANDO_PASSAGEM" || snap?.state === "LIBERADA";
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-white ${look.bg}`}><look.Icon size={22} aria-hidden="true" /></span>
        <div className="min-w-0 flex-1">
          <p className="font-bold">{snap?.name || "Catraca"} · {look.label}</p>
          <p className="text-xs text-muted">{snap?.location}{open && snap?.seconds_left ? ` · fecha em ${snap.seconds_left}s` : ""}</p>
        </div>
        {scheduleId && <button className="btn-accent" onClick={checkin} disabled={busy}>{busy ? "Validando..." : "Fazer check-in"}</button>}
      </div>
      {result && (
        <p className={`rounded-xl px-3 py-2 text-sm font-medium ${result.granted ? "bg-accent-soft text-ink" : "bg-red-50 text-danger"}`} role="status">{result.text}</p>
      )}
      {open && <button className="btn-ghost" onClick={passagem}>Já passei pela catraca</button>}
    </div>
  );
}
