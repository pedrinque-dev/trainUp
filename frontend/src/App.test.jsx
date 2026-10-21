import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import App from "./App";
import { AuthProvider } from "./AuthContext";

// Layout e páginas são trocados por stubs: o alvo aqui é a regra de acesso por perfil (RNF02 no front).
vi.mock("./components/Layout", () => ({ default: ({ children }) => <div data-testid="layout">{children}</div> }));
vi.mock("./pages/Login", () => ({ default: () => <h1>tela de login</h1> }));
vi.mock("./pages/personal/Overview", () => ({ default: () => <p>painel do personal</p> }));
vi.mock("./pages/personal/Alunos", () => ({ default: () => <p>lista de alunos</p> }));
vi.mock("./pages/aluno/Inicio", () => ({ default: () => <p>início do aluno</p> }));
vi.mock("./pages/aluno/Treinar", () => ({ default: () => <p>treinar</p> }));
vi.mock("./pages/Agendamento", () => ({ default: () => <p>agenda</p> }));

function abrir(rota, user) {
  if (user) localStorage.setItem("user", JSON.stringify(user));
  return render(
    <MemoryRouter initialEntries={[rota]}>
      <AuthProvider><App /></AuthProvider>
    </MemoryRouter>
  );
}
const personal = { id: 1, role: "personal" };
const aluno = { id: 3, role: "aluno" };

describe("rotas protegidas", () => {
  it.each(["/", "/personal", "/personal/alunos", "/aluno", "/agendamento", "/rota-inexistente"])(
    "visitante em %s é mandado para o login", async (rota) => {
      abrir(rota);
      expect(await screen.findByText("tela de login")).toBeInTheDocument();
    });

  it("personal logado entra no painel e não vê a tela de aluno", async () => {
    abrir("/", personal);
    expect(await screen.findByText("painel do personal")).toBeInTheDocument();
    expect(screen.getByTestId("layout")).toBeInTheDocument();
  });

  it("aluno logado entra no início", async () => {
    abrir("/", aluno);
    expect(await screen.findByText("início do aluno")).toBeInTheDocument();
  });

  it("aluno tentando abrir área do personal é redirecionado para a sua", async () => {
    abrir("/personal/alunos", aluno);
    expect(await screen.findByText("início do aluno")).toBeInTheDocument();
    expect(screen.queryByText("lista de alunos")).toBeNull();
  });

  it("personal tentando abrir área do aluno é redirecionado para a sua", async () => {
    abrir("/aluno/treinar", personal);
    expect(await screen.findByText("painel do personal")).toBeInTheDocument();
    expect(screen.queryByText("treinar")).toBeNull();
  });

  it("a agenda é compartilhada pelos dois perfis", async () => {
    abrir("/agendamento", aluno);
    expect(await screen.findByText("agenda")).toBeInTheDocument();
  });

  it("rota desconhecida logado volta para a área do perfil", async () => {
    abrir("/qualquer-coisa", aluno);
    expect(await screen.findByText("início do aluno")).toBeInTheDocument();
  });
});
