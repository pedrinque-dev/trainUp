import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useFetch, useInterval } from "./hooks";

describe("useFetch", () => {
  it("começa carregando e entrega os dados", async () => {
    const { result } = renderHook(() => useFetch(async () => ({ ok: 1 })));
    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual({ ok: 1 });
    expect(result.current.error).toBeNull();
  });

  it("converte falhas em mensagem amigável", async () => {
    const fn = async () => { throw { response: { status: 403, data: { detail: "Acesso negado" } } }; };
    const { result } = renderHook(() => useFetch(fn));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe("Acesso negado");
  });

  it("reload busca de novo e a versão silenciosa não volta ao estado de loading", async () => {
    let n = 0;
    const { result } = renderHook(() => useFetch(async () => ++n));
    await waitFor(() => expect(result.current.data).toBe(1));
    await act(async () => { await result.current.reload(true); });
    expect(result.current.data).toBe(2);
    expect(result.current.loading).toBe(false);
  });

  it("refaz a busca quando as dependências mudam", async () => {
    const fn = vi.fn(async () => "x");
    const { rerender } = renderHook(({ id }) => useFetch(fn, [id]), { initialProps: { id: 1 } });
    await waitFor(() => expect(fn).toHaveBeenCalledTimes(1));
    rerender({ id: 2 });
    await waitFor(() => expect(fn).toHaveBeenCalledTimes(2));
  });
});

describe("useInterval", () => {
  afterEach(() => vi.useRealTimers());

  it("chama a função no intervalo e para ao desmontar", () => {
    vi.useFakeTimers();
    const fn = vi.fn();
    const { unmount } = renderHook(() => useInterval(fn, 1000));
    vi.advanceTimersByTime(3000);
    expect(fn).toHaveBeenCalledTimes(3);
    unmount();
    vi.advanceTimersByTime(3000);
    expect(fn).toHaveBeenCalledTimes(3);
  });

  it("não dispara quando inativo", () => {
    vi.useFakeTimers();
    const fn = vi.fn();
    renderHook(() => useInterval(fn, 1000, false));
    vi.advanceTimersByTime(5000);
    expect(fn).not.toHaveBeenCalled();
  });
});
