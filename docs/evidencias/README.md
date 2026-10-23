# Evidências de testes

Execuções realizadas em 23/10/2026:

| Módulo | Comando | Resultado | Evidência |
| --- | --- | --- | --- |
| Backend | `python -m pytest -v` (em `backend`) | 57 testes aprovados; 1 aviso de depreciação do Starlette | [backend-pytest.txt](./backend-pytest.txt) |
| Frontend | `npm test -- --reporter=verbose` (em `frontend`) | 8 arquivos e 64 testes aprovados | [frontend-vitest.txt](./frontend-vitest.txt) |

Os arquivos de evidência contêm a saída detalhada de cada execução e o respectivo código de saída.
