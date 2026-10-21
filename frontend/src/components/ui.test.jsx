import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Badge, EmptyState, ErrorState, Field, Modal, PageHeader, ProgressBar, SkeletonList, StatCard, Tabs } from "./ui";

describe("ProgressBar", () => {
  const pct = (v, max) => {
    const { unmount } = render(<ProgressBar value={v} max={max} />);
    const now = Number(screen.getByRole("progressbar").getAttribute("aria-valuenow"));
    unmount();
    return now;
  };
  it("calcula a porcentagem", () => expect(pct(25, 50)).toBe(50));
  it("limita entre 0 e 100", () => {
    expect(pct(500, 100)).toBe(100);
    expect(pct(-5, 100)).toBe(0);
  });
  it("não quebra com max = 0", () => expect(pct(10, 0)).toBe(0));
});

describe("Field", () => {
  it("associa o rótulo ao campo (acessibilidade)", () => {
    render(<Field label="E-mail" hint="Use o e-mail da academia"><input /></Field>);
    expect(screen.getByLabelText("E-mail")).toBeInTheDocument();
    expect(screen.getByText("Use o e-mail da academia")).toBeInTheDocument();
  });
});

describe("Tabs", () => {
  it("marca a aba ativa e avisa a troca", async () => {
    const onChange = vi.fn();
    render(<Tabs tabs={[{ value: "a", label: "Alunos" }, { value: "b", label: "Treinos" }]} value="a" onChange={onChange} />);
    expect(screen.getByRole("tab", { name: "Alunos" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Treinos" })).toHaveAttribute("aria-selected", "false");
    await userEvent.click(screen.getByRole("tab", { name: "Treinos" }));
    expect(onChange).toHaveBeenCalledWith("b");
  });
});

describe("Modal", () => {
  it("não renderiza fechado", () => {
    render(<Modal open={false} onClose={() => {}} title="T">x</Modal>);
    expect(screen.queryByRole("dialog")).toBeNull();
  });
  it("abre com título acessível e fecha por botão, fundo e Esc", async () => {
    const onClose = vi.fn();
    render(<Modal open onClose={onClose} title="Novo aluno"><p>conteúdo</p></Modal>);
    expect(screen.getByRole("dialog", { name: "Novo aluno" })).toBeInTheDocument();
    expect(document.body.style.overflow).toBe("hidden");
    await userEvent.click(screen.getByLabelText("Fechar"));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(2);
  });
  it("devolve a rolagem da página ao fechar", () => {
    const { rerender } = render(<Modal open onClose={() => {}} title="T">x</Modal>);
    rerender(<Modal open={false} onClose={() => {}} title="T">x</Modal>);
    expect(document.body.style.overflow).toBe("");
  });
});

describe("estados de tela", () => {
  it("ErrorState mostra o alerta e permite tentar de novo", async () => {
    const retry = vi.fn();
    render(<ErrorState message="Falhou" onRetry={retry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Falhou");
    await userEvent.click(screen.getByText("Tentar de novo"));
    expect(retry).toHaveBeenCalledOnce();
  });
  it("ErrorState sem onRetry não mostra o botão", () => {
    render(<ErrorState message="Falhou" />);
    expect(screen.queryByText("Tentar de novo")).toBeNull();
  });
  it("EmptyState exibe título, texto e ação", () => {
    render(<EmptyState title="Sem alunos" text="Cadastre o primeiro" action={<button>Cadastrar</button>} />);
    expect(screen.getByText("Sem alunos")).toBeInTheDocument();
    expect(screen.getByText("Cadastre o primeiro")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cadastrar" })).toBeInTheDocument();
  });
  it("SkeletonList anuncia carregamento com o número de linhas pedido", () => {
    const { container } = render(<SkeletonList rows={4} />);
    expect(screen.getByRole("status", { name: "Carregando" })).toBeInTheDocument();
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(4);
  });
});

describe("blocos simples", () => {
  it("StatCard mostra valor, rótulo e dica", () => {
    render(<StatCard label="Alunos ativos" value={12} hint="+2 no mês" />);
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Alunos ativos")).toBeInTheDocument();
    expect(screen.getByText("+2 no mês")).toBeInTheDocument();
  });
  it("PageHeader mostra subtítulo e ações só quando informados", () => {
    const { rerender } = render(<PageHeader title="Painel" />);
    expect(screen.getByRole("heading", { name: "Painel" })).toBeInTheDocument();
    expect(screen.queryByText("sub")).toBeNull();
    rerender(<PageHeader title="Painel" subtitle="sub" actions={<button>Novo</button>} />);
    expect(screen.getByText("sub")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Novo" })).toBeInTheDocument();
  });
  it("Badge aplica o tom pedido", () => {
    render(<Badge tone="danger">Atrasado</Badge>);
    expect(screen.getByText("Atrasado").className).toMatch(/text-danger/);
  });
});
