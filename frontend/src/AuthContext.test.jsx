import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthContext";
import api from "./services/api";

const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
const ana = { id: 3, name: "Ana", role: "aluno" };

describe("AuthContext", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("começa deslogado e restaura a sessão salva", () => {
    expect(renderHook(() => useAuth(), { wrapper }).result.current.user).toBeNull();
    localStorage.setItem("user", JSON.stringify(ana));
    expect(renderHook(() => useAuth(), { wrapper }).result.current.user).toEqual(ana);
  });

  it("login guarda token e usuário", () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    act(() => result.current.login({ access_token: "tok", user: ana }));
    expect(result.current.user).toEqual(ana);
    expect(localStorage.getItem("token")).toBe("tok");
    expect(JSON.parse(localStorage.getItem("user"))).toEqual(ana);
  });

  it("logout revoga o token no servidor e limpa tudo", () => {
    const post = vi.spyOn(api, "post").mockResolvedValue({});
    localStorage.setItem("token", "tok");
    localStorage.setItem("user", JSON.stringify(ana));
    const { result } = renderHook(() => useAuth(), { wrapper });
    act(() => result.current.logout());
    expect(post).toHaveBeenCalledWith("/auth/logout", null, { headers: { Authorization: "Bearer tok" } });
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("token")).toBeNull();
  });

  it("logout funciona mesmo se o servidor estiver fora do ar", async () => {
    vi.spyOn(api, "post").mockRejectedValue(new Error("offline"));
    localStorage.setItem("token", "tok");
    const { result } = renderHook(() => useAuth(), { wrapper });
    act(() => result.current.logout());
    await waitFor(() => expect(result.current.user).toBeNull());
  });

  it("refreshUser atualiza o usuário com os dados do servidor", async () => {
    const vinculado = { ...ana, personal_id: 1 };
    vi.spyOn(api, "get").mockResolvedValue({ data: vinculado });
    const { result } = renderHook(() => useAuth(), { wrapper });
    await act(async () => { await result.current.refreshUser(); });
    expect(result.current.user).toEqual(vinculado);
    expect(JSON.parse(localStorage.getItem("user")).personal_id).toBe(1);
  });
});
