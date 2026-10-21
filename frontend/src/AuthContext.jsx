import { createContext, useCallback, useContext, useState } from "react";
import api from "./services/api";

const Ctx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("user") || "null"));

  const login = ({ access_token, user }) => {
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(user));
    setUser(user);
  };
  const logout = () => {
    const token = localStorage.getItem("token");
    // revoga o token no servidor (best-effort); o header é passado explícito porque o storage é limpo em seguida
    if (token) api.post("/auth/logout", null, { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});
    localStorage.clear();
    setUser(null);
  };
  // atualiza dados do usuário (ex.: depois que o personal aceita o vínculo)
  const refreshUser = useCallback(async () => {
    const { data } = await api.get("/auth/me");
    localStorage.setItem("user", JSON.stringify(data));
    setUser(data);
    return data;
  }, []);

  return <Ctx.Provider value={{ user, login, logout, refreshUser }}>{children}</Ctx.Provider>;
}

export const useAuth = () => useContext(Ctx);
