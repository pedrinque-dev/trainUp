# Evidências de testes

Os arquivos registram a saída real de cada comando. O backend foi executado em 24/10/2026 e o frontend em 23/10/2026; as medições dos requisitos não funcionais (RNF03, RNF04 e RNF08) foram coletadas em 24/10/2026.

## Testes automatizados

| Módulo | Comando | Resultado | Evidência |
| --- | --- | --- | --- |
| Backend | `python -m pytest -v` (em `backend`) | 61 testes aprovados; 1 aviso de depreciação do Starlette | [backend-pytest.txt](./backend-pytest.txt) |
| Frontend | `npm test -- --reporter=verbose` (em `frontend`) | 8 arquivos e 64 testes aprovados | [frontend-vitest.txt](./frontend-vitest.txt) |
| Backend | `python -m ruff check app tests --select E9,F63,F7,F82,F401` (em `backend`) | Verificações aprovadas | [backend-ruff.txt](./backend-ruff.txt) |
| Backend | `python -m pytest -v --cov=app --cov-report=term --junitxml=pytest_junit.xml` (em `backend`) | 61 testes aprovados; cobertura total de 95,47% (95% arredondado) | [backend-pytest-cobertura.txt](./backend-pytest-cobertura.txt); [relatório JUnit](./pytest_junit.xml) |
| Frontend | `npm run test:coverage` (em `frontend`) | 8 arquivos e 64 testes aprovados; cobertura total de statements de 97,73% | [frontend-vitest-cobertura.txt](./frontend-vitest-cobertura.txt) |
| Frontend | `npm run build` (em `frontend`) | Build concluído com sucesso | [frontend-build.txt](./frontend-build.txt) |

## Requisitos não funcionais

| Requisito | Como reproduzir | Resultado | Evidência |
| --- | --- | --- | --- |
| RNF03 — tempo de resposta (até 3 s) | `python docs/evidencias/coletar_evidencias_api.py` (API no ar com `SEED_DEMO=true`) e teste `test_rnf03_evolucao_responde_em_ate_3_segundos` | Evolução de carga: média de 18,5 ms e máximo de 51,5 ms em 5 chamadas | [evidencias-api.txt](./evidencias-api.txt) |
| RNF08 — ciclo da catraca (até 1 s) | Mesmo script e teste `test_rnf08_ciclo_da_catraca_dentro_de_1_segundo` | 7 ciclos medidos, todos entre 0 e 1 ms | [evidencias-api.txt](./evidencias-api.txt) |
| RNF04 — responsividade | `python docs/evidencias/capturar_telas.py` (front-end em `http://localhost:5173`; requer `pip install playwright` e `playwright install chromium`) | 26 capturas (13 telas em 1440 px e 375 px); nenhuma tela com rolagem horizontal | [rnf04-overflow.txt](./rnf04-overflow.txt); [prints/](./prints) |
| RF13 — evolução de carga | `python -m pytest tests/test_evolucao_e_desempenho.py -v` (em `backend`) | 4 testes aprovados | [backend-pytest.txt](./backend-pytest.txt) |
| RNF05 — ambiente em nuvem | Captura do code-server na instância EC2 com a aplicação em execução | Ambiente de desenvolvimento em nuvem comprovado | [prints/14-ec2-code-server.png](./prints/14-ec2-code-server.png) |

## Cobertura

- **Backend:** 95,47% de cobertura total (1.723 statements, 78 missed).
- **Frontend:** 97,73% de cobertura total de statements.

## Ambiente

- Backend: Python `3.12.3`, 24/10/2026.
- Frontend: Node.js `v24.15.0`, 23/10/2026.
- O workflow de CI configura Python 3.12 e Node.js 22.
- As medições de RNF03 e RNF08 usaram SQLite e os dados de demonstração do seed; os tempos em PostgreSQL podem variar.

## Observações

- O backend emitiu um `StarletteDeprecationWarning`: o uso de `httpx` com `starlette.testclient` está obsoleto; o aviso recomenda `httpx2`.
- O Vitest emitiu avisos de future flags do React Router: `v7_startTransition` e `v7_relativeSplatPath`. Os avisos não impediram os testes.
