import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ToastProvider, useToast } from "./Toast";

function Disparador() {
  const toast = useToast();
  return (
    <>
      <button onClick={() => toast("Salvo com sucesso")}>ok</button>
      <button onClick={() => toast("Algo deu errado", "error")}>erro</button>
    </>
  );
}

describe("Toast", () => {
  afterEach(() => vi.useRealTimers());

  it("mostra a mensagem numa região acessível e some depois de 4,2 s", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(<ToastProvider><Disparador /></ToastProvider>);
    await userEvent.click(screen.getByText("ok"));
    expect(screen.getByRole("status")).toHaveTextContent("Salvo com sucesso");
    act(() => { vi.advanceTimersByTime(4300); });
    expect(screen.queryByText("Salvo com sucesso")).toBeNull();
  });

  it("empilha várias mensagens, inclusive de erro", async () => {
    render(<ToastProvider><Disparador /></ToastProvider>);
    await userEvent.click(screen.getByText("ok"));
    await userEvent.click(screen.getByText("erro"));
    expect(screen.getByText("Salvo com sucesso")).toBeInTheDocument();
    expect(screen.getByText("Algo deu errado")).toBeInTheDocument();
  });

  it("useToast fora do provider não quebra", async () => {
    render(<Disparador />);
    await userEvent.click(screen.getByText("ok"));
    expect(screen.queryByText("Salvo com sucesso")).toBeNull();
  });
});
