import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "/api/v1" });

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && localStorage.getItem("token")) {
      localStorage.clear();
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export function errMsg(e) {
  const d = e.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => x.msg.replace(/^Value error, /, "")).join("; ");
  if (!e.response) return "Sem conexão com o servidor. Verifique sua internet e tente de novo.";
  return "Não foi possível concluir a ação. Tente novamente.";
}

export async function downloadFile(path, filename) {
  const { data } = await api.get(path, { responseType: "blob" });
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export const WEEK = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
export const GOALS = {
  ganho_massa: "Ganho de massa",
  emagrecimento: "Emagrecimento",
  resistencia: "Resistência",
  saude: "Saúde geral",
};
export const MUSCLE_GROUPS = ["Peito", "Costas", "Pernas", "Ombros", "Bíceps", "Tríceps", "Core", "Cardio", "Geral"];
export const STATUS = {
  AGENDADO: { label: "Agendada", tone: "brand" },
  CHECKIN: { label: "Check-in feito", tone: "accent" },
  CONCLUIDO: { label: "Concluída", tone: "ok" },
  CANCELADO: { label: "Cancelada", tone: "neutral" },
};

export default api;
