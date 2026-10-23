# Evidências de testes

Execuções realizadas em 23/10/2026. Os arquivos registram a saída real de cada comando, o horário de início e o código de saída.

| Módulo | Comando | Resultado | Evidência |
| --- | --- | --- | --- |
| Backend | `python -m pytest -v` (em `backend`) | 57 testes aprovados; 1 aviso de depreciação do Starlette | [backend-pytest.txt](./backend-pytest.txt) |
| Frontend | `npm test -- --reporter=verbose` (em `frontend`) | 8 arquivos e 64 testes aprovados | [frontend-vitest.txt](./frontend-vitest.txt) |
| Backend | `python -m ruff check app tests --select E9,F63,F7,F82,F401` (em `backend`) | Verificações aprovadas | [backend-ruff.txt](./backend-ruff.txt) |
| Backend | `python -m pytest -v --cov=app --cov-report=term-missing --cov-fail-under=90 --junitxml=pytest_junit.xml` (em `backend`) | 57 testes aprovados; cobertura total de 94,82% (95% arredondado); mínimo de 90% atingido | [backend-pytest-cobertura.txt](./backend-pytest-cobertura.txt); [relatório JUnit](./pytest_junit.xml) |
| Frontend | `npm run test:coverage` (em `frontend`) | 8 arquivos e 64 testes aprovados; cobertura total de statements de 97,73% | [frontend-vitest-cobertura.txt](./frontend-vitest-cobertura.txt) |
| Frontend | `npm run build` (em `frontend`) | Build concluído com sucesso | [frontend-build.txt](./frontend-build.txt) |

## Cobertura

- **Backend:** 94,82% de cobertura total (95% arredondado; 1.661 statements, 86 missed). O mínimo de 90% foi atingido.
- **Frontend:** 97,73% de cobertura total de statements.

## Ambiente

- Python: `3.14.4` (`python --version`).
- Node.js: `v24.15.0` (`node --version`).
- O workflow de CI configura Python 3.12 e Node.js 22; as evidências desta pasta foram executadas localmente com as versões acima.

## Observações

- O backend emitiu um `StarletteDeprecationWarning`: o uso de `httpx` com `starlette.testclient` está obsoleto; o aviso recomenda `httpx2`.
- O Vitest emitiu avisos de future flags do React Router: `v7_startTransition` e `v7_relativeSplatPath`. Os avisos não impediram os testes.
