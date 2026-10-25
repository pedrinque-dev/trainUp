"""Captura as telas do TrainUp em 1440 px (desktop) e 375 px (celular) e verifica rolagem horizontal (RNF04).

Uso (front-end em http://localhost:5173 com proxy para a API com SEED_DEMO=true):
    pip install playwright && playwright install chromium
    python docs/evidencias/capturar_telas.py [http://localhost:5173]
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173"
OUT = pathlib.Path(__file__).parent / "prints"
OUT.mkdir(exist_ok=True)
TAMANHOS = {"desktop-1440": (1440, 900), "celular-375": (375, 812)}

PERSONAL = [("02-visao-geral", "/personal"), ("03-alunos", "/personal/alunos"), ("04-perfil-aluno", "/personal/alunos/2"),
            ("05-treinos", "/personal/treinos"), ("06-agenda-personal", "/agendamento"), ("07-exercicios", "/personal/exercicios"),
            ("08-relatorios", "/personal/relatorios"), ("09-catraca", "/automacao")]
ALUNO = [("10-inicio-aluno", "/aluno"), ("11-treinar", "/aluno/treinar"), ("12-evolucao", "/aluno/evolucao"), ("13-agenda-aluno", "/agendamento")]


def entrar(page, email):
    page.goto(f"{URL}/login")
    page.fill("input[type=email]", email)
    page.fill("input[type=password]", "trainup123")
    page.click("form button.btn")
    page.wait_for_url(lambda u: "/login" not in u, timeout=15000)


resultado = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for nome, (w, h) in TAMANHOS.items():
        def tirar(page, rotulo, rota):
            page.goto(f"{URL}{rota}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(700)
            overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            page.screenshot(path=str(OUT / f"{rotulo}_{nome}.png"), full_page=True)
            resultado.append((rotulo, nome, overflow))

        ctx = b.new_context(viewport={"width": w, "height": h})
        pg = ctx.new_page()
        pg.goto(f"{URL}/login")
        pg.wait_for_load_state("networkidle")
        ov = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        pg.screenshot(path=str(OUT / f"01-login_{nome}.png"), full_page=True)
        resultado.append(("01-login", nome, ov))
        entrar(pg, "personal@trainup.com")
        for rotulo, rota in PERSONAL:
            tirar(pg, rotulo, rota)
        ctx.close()
        ctx = b.new_context(viewport={"width": w, "height": h})
        pg = ctx.new_page()
        entrar(pg, "aluno@trainup.com")
        for rotulo, rota in ALUNO:
            tirar(pg, rotulo, rota)
        ctx.close()
    b.close()

linhas = ["Verificação de rolagem horizontal (scrollWidth - clientWidth; 0 = sem rolagem horizontal)", ""]
for rotulo, nome, ov in resultado:
    linhas.append(f"{rotulo:<22} {nome:<14} excesso = {ov:>3} px  {'OK' if ov <= 0 else 'ROLAGEM HORIZONTAL'}")
ruins = [r for r in resultado if r[2] > 0]
linhas += ["", f"{len(resultado)} capturas; telas com rolagem horizontal: {len(ruins)}"]
(OUT.parent / "rnf04-overflow.txt").write_text("\n".join(linhas), encoding="utf-8")
print("\n".join(linhas))
