import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../AuthContext";
import api from "../services/api";
import Login from "./Login";

function renderLogin(url = "/login") {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/personal" element={<p>área do personal</p>} />
          <Route path="/aluno" element={<p>área do aluno</p>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

const erro = (status, detail) => ({ response: { status, data: { detail } } });
const digitar = async (email, senha) => {
  await userEvent.type(screen.getByLabelText("E-mail"), email);
  await userEvent.type(screen.getByLabelText("Senha"), senha);
};

describe("Login", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("mostra a mensagem do servidor quando a senha está errada (CT045)", async () => {
    vi.spyOn(api, "post").mockRejectedValue(erro(401, "E-mail ou senha incorretos"));
    renderLogin();
    await digitar("ana@trainup.com", "errada123");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByText("E-mail ou senha incorretos")).toBeInTheDocument();
    expect(localStorage.getItem("token")).toBeNull();
  });

  it("aluno autenticado vai para /aluno e a sessão fica salva", async () => {
    const post = vi.spyOn(api, "post").mockResolvedValue({ data: { access_token: "tok", user: { id: 3, role: "aluno" } } });
    renderLogin();
    await digitar("ana@trainup.com", "trainup123");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByText("área do aluno")).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith("/auth/login", { email: "ana@trainup.com", password: "trainup123" });
    expect(localStorage.getItem("token")).toBe("tok");
  });

  it("personal autenticado vai para /personal", async () => {
    vi.spyOn(api, "post").mockResolvedValue({ data: { access_token: "t", user: { id: 1, role: "personal" } } });
    renderLogin();
    await digitar("personal@trainup.com", "trainup123");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByText("área do personal")).toBeInTheDocument();
  });

  it("desabilita o botão enquanto envia (evita envio duplo)", async () => {
    let liberar;
    vi.spyOn(api, "post").mockReturnValue(new Promise((r) => { liberar = r; }));
    renderLogin();
    await digitar("a@b.com", "x");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    expect(screen.getByRole("button", { name: "Aguarde..." })).toBeDisabled();
    liberar({ data: { access_token: "t", user: { role: "aluno" } } });
    await screen.findByText("área do aluno");
  });

  it("cadastro de aluno envia convite em maiúsculas e depois faz login", async () => {
    const post = vi.spyOn(api, "post")
      .mockResolvedValueOnce({ data: {} })
      .mockResolvedValueOnce({ data: { access_token: "t", user: { role: "aluno" } } });
    renderLogin("/login?convite=train123");
    await userEvent.click(screen.getByRole("button", { name: "Cadastre-se" }));
    await userEvent.type(screen.getByLabelText("Nome completo"), "Ana Clara");
    await userEvent.type(screen.getByLabelText("E-mail"), "ana@x.com");
    await userEvent.type(screen.getByLabelText("Senha"), "Senha1234");
    await userEvent.click(screen.getByRole("button", { name: "Criar conta e entrar" }));
    await screen.findByText("área do aluno");
    expect(post.mock.calls[0][0]).toBe("/auth/register");
    expect(post.mock.calls[0][1]).toMatchObject({ role: "aluno", invite_code: "TRAIN123", signup_code: null, email: "ana@x.com" });
    expect(post.mock.calls[1][0]).toBe("/auth/login");
  });

  it("exibe o erro de senha fraca vindo da validação do servidor", async () => {
    vi.spyOn(api, "post").mockRejectedValue(erro(422, [{ msg: "Value error, A senha deve conter letras e números" }]));
    renderLogin();
    await userEvent.click(screen.getByRole("button", { name: "Cadastre-se" }));
    await userEvent.type(screen.getByLabelText("Nome completo"), "Ana Clara");
    await userEvent.type(screen.getByLabelText("E-mail"), "ana@x.com");
    await userEvent.type(screen.getByLabelText("Senha"), "12345678");
    await userEvent.click(screen.getByRole("button", { name: "Criar conta e entrar" }));
    expect(await screen.findByText("A senha deve conter letras e números")).toBeInTheDocument();
  });

  it("recuperação de senha: pede o token e depois a nova senha", async () => {
    const post = vi.spyOn(api, "post")
      .mockResolvedValueOnce({ data: { detail: "Se o e-mail existir, geramos um token." } })
      .mockResolvedValueOnce({ data: { detail: "Senha alterada. Faça login." } });
    renderLogin();
    await userEvent.click(screen.getByRole("button", { name: "Esqueci minha senha" }));
    await userEvent.type(screen.getByLabelText("E-mail"), "ana@x.com");
    await userEvent.click(screen.getByRole("button", { name: "Gerar token" }));
    expect(await screen.findByText(/geramos um token/)).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Token de recuperação"), "abc123");
    await userEvent.type(screen.getByLabelText("Nova senha"), "NovaSenha123");
    await userEvent.click(screen.getByRole("button", { name: "Salvar nova senha" }));
    expect(await screen.findByText("Senha alterada. Faça login.")).toBeInTheDocument();
    expect(post.mock.calls[1]).toEqual(["/auth/reset", { token: "abc123", password: "NovaSenha123" }]);
    await waitFor(() => expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument());
  });

  it("voltar limpa a mensagem de erro", async () => {
    vi.spyOn(api, "post").mockRejectedValue(erro(401, "E-mail ou senha incorretos"));
    renderLogin();
    await digitar("a@b.com", "x");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    await screen.findByText("E-mail ou senha incorretos");
    await userEvent.click(screen.getByRole("button", { name: "Esqueci minha senha" }));
    expect(screen.queryByText("E-mail ou senha incorretos")).toBeNull();
  });
});
