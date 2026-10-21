import { beforeEach, describe, expect, it, vi } from "vitest";
import api, { errMsg, downloadFile } from "./api";

const resp = (status, data) => ({ response: { status, data } });

describe("errMsg", () => {
  it("usa a mensagem textual do servidor", () => {
    expect(errMsg(resp(401, { detail: "E-mail ou senha incorretos" }))).toBe("E-mail ou senha incorretos");
  });
  it("junta erros de validação e remove o prefixo técnico", () => {
    const e = resp(422, { detail: [{ msg: "Value error, A senha deve ter pelo menos 8 caracteres" }, { msg: "campo obrigatório" }] });
    expect(errMsg(e)).toBe("A senha deve ter pelo menos 8 caracteres; campo obrigatório");
  });
  it("avisa quando não há conexão", () => {
    expect(errMsg(new Error("Network Error"))).toMatch(/Sem conexão/);
  });
  it("cai numa mensagem genérica para erros sem detalhe", () => {
    expect(errMsg(resp(500, {}))).toMatch(/Não foi possível concluir/);
  });
});

describe("interceptors", () => {
  beforeEach(() => {
    delete window.location;
    window.location = { href: "/" };
  });

  const adapterOk = (cfg) => Promise.resolve({ data: {}, status: 200, statusText: "OK", headers: {}, config: cfg });
  const adapterErr = (status) => (cfg) => Promise.reject(Object.assign(new Error("x"), { config: cfg, response: { status, data: {}, config: cfg } }));

  it("envia o token como Bearer quando existe", async () => {
    localStorage.setItem("token", "abc");
    let enviado;
    await api.get("/x", { adapter: (cfg) => { enviado = cfg.headers.Authorization; return adapterOk(cfg); } });
    expect(enviado).toBe("Bearer abc");
  });

  it("não envia Authorization sem token", async () => {
    let enviado = "nenhum";
    await api.get("/x", { adapter: (cfg) => { enviado = cfg.headers.Authorization; return adapterOk(cfg); } });
    expect(enviado).toBeUndefined();
  });

  it("401 com sessão ativa limpa o storage e volta para /login", async () => {
    localStorage.setItem("token", "abc");
    localStorage.setItem("user", "{}");
    await expect(api.get("/x", { adapter: adapterErr(401) })).rejects.toBeTruthy();
    expect(localStorage.getItem("token")).toBeNull();
    expect(window.location.href).toBe("/login");
  });

  it("401 sem sessão (ex.: senha errada no login) não redireciona", async () => {
    await expect(api.get("/x", { adapter: adapterErr(401) })).rejects.toBeTruthy();
    expect(window.location.href).toBe("/");
  });

  it("outros erros (403) não derrubam a sessão", async () => {
    localStorage.setItem("token", "abc");
    await expect(api.get("/x", { adapter: adapterErr(403) })).rejects.toBeTruthy();
    expect(localStorage.getItem("token")).toBe("abc");
  });
});

describe("downloadFile", () => {
  it("baixa o blob e dispara o download com o nome pedido", async () => {
    URL.createObjectURL = vi.fn(() => "blob:fake");
    URL.revokeObjectURL = vi.fn();
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    const get = vi.spyOn(api, "get").mockResolvedValue({ data: new Blob(["pdf"]) });
    await downloadFile("/reports/aluno/1/pdf", "relatorio.pdf");
    expect(get).toHaveBeenCalledWith("/reports/aluno/1/pdf", { responseType: "blob" });
    expect(click).toHaveBeenCalledOnce();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:fake");
    expect(document.querySelector("a[download]")).toBeNull(); // link temporário removido
  });
});
