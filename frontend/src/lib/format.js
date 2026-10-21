// Tudo é salvo em UTC; a interface sempre exibe e interpreta datas no fuso de São Paulo.
export const TZ = "America/Sao_Paulo";
const fmt = (opts) => new Intl.DateTimeFormat("pt-BR", { timeZone: TZ, ...opts });

export const fmtDateTime = (iso) =>
  fmt({ weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(iso));
export const fmtTime = (iso) => fmt({ hour: "2-digit", minute: "2-digit" }).format(new Date(iso));
export const fmtTimeSec = (iso) => fmt({ hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date(iso));
export const fmtFull = (iso) =>
  fmt({ day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(iso));

// "YYYY-MM-DD" (data civil) -> "dd/mm" / "dd/mm/aaaa", sem passar por fuso
export const dayShort = (d) => `${d.slice(8, 10)}/${d.slice(5, 7)}`;
export const dayLong = (d) => `${d.slice(8, 10)}/${d.slice(5, 7)}/${d.slice(0, 4)}`;

export const dayOf = (iso) => new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(new Date(iso)); // YYYY-MM-DD
export const todayISO = () => dayOf(new Date().toISOString());

export function addDays(d, n) {
  const t = new Date(`${d}T12:00:00Z`);
  t.setUTCDate(t.getUTCDate() + n);
  return t.toISOString().slice(0, 10);
}
export const weekdayIndex = (d) => (new Date(`${d}T12:00:00Z`).getUTCDay() + 6) % 7; // 0 = segunda
export const mondayOf = (d) => addDays(d, -weekdayIndex(d));

const WD = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
export const weekdayShort = (d) => WD[weekdayIndex(d)];

function offsetMs(ts) {
  const o = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone: TZ, hour12: false, year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    }).formatToParts(new Date(ts)).map((p) => [p.type, p.value])
  );
  return Date.UTC(+o.year, +o.month - 1, +o.day, +o.hour % 24, +o.minute, +o.second) - ts;
}
// "YYYY-MM-DDTHH:mm" digitado como horário de Brasília -> ISO em UTC
export function zonedToUtc(value) {
  const [d, t] = value.split("T");
  const [y, m, da] = d.split("-").map(Number);
  const [h, mi] = t.split(":").map(Number);
  const guess = Date.UTC(y, m - 1, da, h, mi);
  const ts = guess - offsetMs(guess - offsetMs(guess));
  return new Date(ts).toISOString();
}
// valor para <input type="datetime-local"> no horário de Brasília
export function inputValue(date = new Date()) {
  const o = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", { timeZone: TZ, hour12: false, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })
      .formatToParts(date).map((p) => [p.type, p.value])
  );
  return `${o.year}-${o.month}-${o.day}T${String(+o.hour % 24).padStart(2, "0")}:${o.minute}`;
}

export const num = (x, d = 1) => Number(x ?? 0).toLocaleString("pt-BR", { maximumFractionDigits: d });
export const initials = (name = "") => name.split(" ").filter(Boolean).slice(0, 2).map((s) => s[0]).join("").toUpperCase();
