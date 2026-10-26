# TrainUp

Plataforma web para gestão de treinos entre **Personal Trainers** e **alunos**: fichas de treino, agendamento de aulas, registro de cargas, análise de evolução, relatórios em PDF e controle de acesso às aulas por check-in.

![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Stack](#stack)
- [Arquitetura](#arquitetura)
- [Início rápido (Docker)](#início-rápido-docker)
- [Desenvolvimento local](#desenvolvimento-local)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Contas de demonstração](#contas-de-demonstração)
- [Catraca virtual](#catraca-virtual)
- [Ciência de dados e relatórios](#ciência-de-dados-e-relatórios)
- [API](#api)
- [Testes e CI](#testes-e-ci)
- [Segurança](#segurança)
- [Documentação](#documentação)
- [Estrutura do projeto](#estrutura-do-projeto)

---

## Funcionalidades

### Personal Trainer
- Painel geral com visão dos alunos e da operação do dia
- Gestão de alunos e **aprovação de solicitações de vínculo**
- Cadastro de exercícios e montagem de fichas de treino
- Agenda de aulas com controle de status
- Perfil individual do aluno com evolução de cargas
- **Alertas de estagnação** (aluno sem bater recorde de carga)
- **Relatórios** de evolução por período, com exportação em PDF e observações do personal
- Monitoramento da **catraca virtual** (logs, estatísticas do dia, simulação de cenários e rearme)

### Aluno
- Início com o treino do dia e próximos agendamentos
- Execução do treino com registro de séries (carga e repetições)
- Gráficos de **evolução** por exercício
- Solicitação de vínculo com um personal (por código de convite)
- **Check-in** na catraca para liberar o acesso à aula agendada
- Dicas educativas conforme o objetivo (ganho de massa, emagrecimento, resistência, saúde)

### Geral
- Autenticação JWT com logout que invalida tokens, recuperação e redefinição de senha
- Controle de acesso por perfil (`personal` / `aluno`)
- Datas e horários tratados no fuso `America/Sao_Paulo`

---

## Stack

| Camada | Tecnologias |
| --- | --- |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, python-jose (JWT), bcrypt, ReportLab (PDF) |
| **Frontend** | React 18, Vite 5, React Router 6, Tailwind CSS 3, Recharts, Axios, lucide-react |
| **Banco de dados** | PostgreSQL 16 (Docker) · SQLite (desenvolvimento local) |
| **Infra** | Docker Compose, Nginx (reverse proxy + servidor estático) |
| **Qualidade** | pytest + pytest-cov, Vitest + Testing Library, Ruff, GitHub Actions |

---

## Arquitetura

```
 Navegador ──► Nginx :80 ──┬──► /        → SPA React (build estático)
                           └──► /api/*   → FastAPI :8000 (rede interna)
                                              │
                                              └──► PostgreSQL :5432 (rede interna)
```

Por padrão, **somente o Nginx (porta 80) é exposto**. Backend e banco ficam na rede interna do Compose. As migrações do Alembic rodam automaticamente na inicialização da API.

---

## Início rápido (Docker)

Pré-requisitos: [Docker](https://docs.docker.com/get-docker/) com Docker Compose.

```bash
# 1. Configure o ambiente
cp .env.example .env
#    edite o .env e defina, no mínimo, SECRET_KEY e POSTGRES_PASSWORD
openssl rand -hex 32     # use a saída como SECRET_KEY

# 2. Suba os serviços
docker compose up -d --build
```

Acesse:

| Recurso | URL |
| --- | --- |
| Aplicação | http://localhost |
| Swagger (se `ENABLE_DOCS=true`) | http://localhost/api/docs |
| Health check | http://localhost/api/health |

Para expor também a API (`:8000`) e o banco (`:5432`) no host durante o desenvolvimento:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Para parar e remover os containers (adicione `-v` para apagar também o volume do banco):

```bash
docker compose down
```

---

## Desenvolvimento local

Sem Docker, o backend usa SQLite (`trainup.db`) por padrão.

### Backend

Pré-requisito: Python 3.12.

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

API em http://127.0.0.1:8000 · documentação em http://127.0.0.1:8000/api/docs

### Frontend

Pré-requisito: Node.js 22.

```bash
cd frontend
npm install
npm run dev
```

App em http://localhost:5173 (o Vite faz proxy de `/api` para `http://localhost:8000`).

### Atalhos para Windows

Os scripts `run_backend.bat` e `run_frontend.bat` (na raiz) criam o ambiente virtual, instalam as dependências e iniciam cada serviço com um duplo clique.

---

## Variáveis de ambiente

Definidas no arquivo `.env` (veja `.env.example`):

| Variável | Descrição | Padrão |
| --- | --- | --- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Credenciais do PostgreSQL | `trainup` |
| `APP_ENV` | `development`, `production` ou `test`. Em `production`, a API **não inicia** sem `SECRET_KEY` (mín. 32 caracteres) | `development` |
| `SECRET_KEY` | Chave de assinatura dos JWT. Gere com `openssl rand -hex 32` | — |
| `PERSONAL_SIGNUP_CODE` | Código exigido para cadastrar novos Personal Trainers. Vazio desabilita o cadastro público de personal | — |
| `SEED_DEMO` | Cria contas e dados de demonstração. **Use `false` em produção real** | `true` |
| `ENABLE_DOCS` | Habilita Swagger e OpenAPI em `/api/docs` | `true` |

Opções adicionais do backend (em `app/core/config.py`) incluem: `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS`, `TIMEZONE`, `LOGIN_MAX_ATTEMPTS`, `LOGIN_WINDOW_SECONDS`, `STAGNATION_N`, `CHECKIN_EARLY_MIN`, `CATRACA_OPEN_SECONDS`, `CATRACA_MAX_DENIALS` e `CATRACA_BLOCK_SECONDS`.

---

## Contas de demonstração

Com `SEED_DEMO=true`, a API popula o banco com um personal, alunos com históricos distintos (evolui, estagnado, irregular, moderado), agendamentos, catracas e uma solicitação de vínculo pendente.

Senha de todas as contas: **`trainup123`**

| Perfil | E-mail | Observação |
| --- | --- | --- |
| Personal | `personal@trainup.com` | Código de convite: `TRAIN123` |
| Aluno | `aluno@trainup.com` | Ana Souza: evolui bem |
| Aluno | `bruno@trainup.com` | Estagnado (bom para ver alertas) |
| Aluno | `carla@trainup.com` | Frequência irregular |
| Aluno | `diego@trainup.com` | Evolução moderada |
| Aluno | `elisa@trainup.com` | Evolui bem |
| Aluno | `fabio@trainup.com` | Com solicitação de vínculo pendente |

> ⚠️ Estas contas têm senha conhecida. Em ambientes reais, defina `SEED_DEMO=false`.

---

## Catraca virtual

Módulo que simula automação industrial com uma **máquina de estados persistida no banco**, o que permite várias catracas (unidades) e mais de um worker.

```
TRAVADA ──► VALIDANDO ──► LIBERADA ──► AGUARDANDO_PASSAGEM ──► TRAVADA
   │             │
   │             └──────► TRAVADA (acesso negado)
   └──► BLOQUEIO ──► TRAVADA (rearme manual)
```

- **Ciclo:** SENSOR (leitura da credencial) → CLP (validação do agendamento) → ATUADOR (trava e LEDs) → SCADA (registro de log)
- **Janela de check-in:** o aluno pode entrar a partir de alguns minutos antes da aula (`CHECKIN_EARLY_MIN`)
- **Proteção:** após negativas consecutivas (`CATRACA_MAX_DENIALS`), a catraca entra em `BLOQUEIO` até o rearme pelo personal
- **Simulador de cenários:** `valida`, `invalida`, `sem_aula`, `fora_janela` e leitura dupla, sem depender de dados preparados
- **Auditoria:** todos os eventos (tentativas, passagens, timeouts, bloqueios, resets) ficam registrados com o rastro de transições

---

## Ciência de dados e relatórios

- **Evolução:** por exercício e por dia, carga média, carga máxima, volume (carga × repetições) e percentual de progressão
- **Estagnação:** alerta quando a carga máxima não bate recorde há `N` sessões (`STAGNATION_N`, padrão 3), com sugestão de ajuste da ficha
- **Dicas educativas:** conteúdo orientado ao objetivo do aluno
- **Relatórios:** consolidado por período com frequência nas aulas, evolução e exercícios estagnados, exportável em **PDF** e com campo de observações do personal

---

## API

Todos os endpoints ficam sob `/api/v1`. A documentação interativa completa está em `/api/docs`.

| Grupo | Prefixo | Descrição |
| --- | --- | --- |
| Autenticação | `/auth` | Cadastro, login, `me`, logout, recuperação e redefinição de senha |
| Usuários | `/users` | CRUD de usuários |
| Vínculos | `/links` | Solicitação, listagem e resposta de vínculo aluno-personal |
| Treinos | `/exercises`, `/workouts` | Exercícios e fichas de treino (incluindo `/workouts/today`) |
| Agendamentos | `/schedules` | Criação, listagem e atualização de status |
| Execução | `/progress`, `/sessions` | Registro de séries e sessões de treino |
| Ciência de dados | `/analytics` | `evolution`, `stagnation`, `tips` |
| Relatórios | `/reports` | Relatório por aluno, PDF e observações |
| Catraca | `/automacao` | `turnstiles`, `status`, `checkin`, `simulate`, `passagem`, `reset`, `logs` |
| Painel | `/dashboard` | Dados do painel do personal |

---

## Testes e CI

### Backend

```bash
cd backend
pytest -q --cov=app --cov-report=term-missing
ruff check app tests --select E9,F63,F7,F82,F401
```

> O Ruff roda com um subconjunto de regras (erros de sintaxe, nomes indefinidos e imports não usados), não com o conjunto completo.

### Frontend

```bash
cd frontend
npm test                 # execução única
npm run test:coverage    # com cobertura
npm run build            # build de produção
```

O workflow `.github/workflows/ci.yml` roda a cada push na `main`/`master` e em pull requests:

1. **Backend:** lint com Ruff e testes com cobertura mínima de **90%**
2. **Frontend:** testes com cobertura e build
3. **Compose:** validação (`docker compose config`) e build das imagens

---

## Segurança

- Senhas com hash **bcrypt**
- **JWT** com versão de token: logout e troca de senha invalidam todos os tokens emitidos antes
- **Rate limit de login** por IP e por e-mail
- Cadastro de personal protegido por código (`PERSONAL_SIGNUP_CODE`)
- API e banco **não expostos** no host por padrão
- Backend roda como usuário não-root no container
- Cabeçalhos de segurança no Nginx (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`)
- `SECRET_KEY` obrigatória e validada em produção

---

## Documentação

| Documento | Local |
|---|---|
| Especificação de Requisitos de Software (ERS v2.2) | [`docs/TrainUp_ERS_v2_2.pdf`](./docs/TrainUp_ERS_v2_2.pdf) |
| ERS v1.0 (Sprint 1, histórico; substituída pela v2.2) | [`docs/historico/TrainUp_ERS_v1_0.pdf`](./docs/historico/TrainUp_ERS_v1_0.pdf) |
| Backlog do produto | [`docs/BACKLOG.md`](./docs/BACKLOG.md) |
| Registro de mudanças e decisões | [`CHANGELOG.md`](./CHANGELOG.md) |
| Documentação da API (Swagger/OpenAPI exportado e prints) | [`docs/api/`](./docs/api) |
| Diagramas UML e DER | [`docs/diagramas/`](./docs/diagramas) |
| Protótipos das telas | [`docs/prototipos/`](./docs/prototipos) |
| Evidências de testes (saídas, cobertura, capturas de tela) | [`docs/evidencias/`](./docs/evidencias) |

---

## Estrutura do projeto

```
trainup/
├── backend/
│   ├── alembic/              # migrações do banco
│   ├── app/
│   │   ├── core/             # config, segurança, rate limit, fuso horário
│   │   ├── models/           # modelos SQLAlchemy
│   │   ├── routers/          # endpoints da API
│   │   ├── schemas/          # schemas Pydantic
│   │   ├── services/         # regras de negócio (analytics, relatórios, PDF, catraca)
│   │   ├── main.py           # aplicação FastAPI
│   │   └── seed.py           # dados de demonstração
│   ├── tests/                # testes pytest
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # UI, layout, gráficos, catraca
│   │   ├── pages/            # telas (personal/, aluno/, agendamento, automação, login)
│   │   ├── services/         # cliente da API
│   │   └── lib/              # utilitários e hooks
│   ├── nginx.conf
│   └── Dockerfile
├── docs/
│   ├── TrainUp_ERS_v2_2.pdf  # especificação de requisitos
│   ├── BACKLOG.md
│   ├── historico/            # versões anteriores da ERS (Sprint 1)
│   ├── api/                  # Swagger: prints e openapi.json
│   ├── diagramas/            # casos de uso, classes, DER, sequência
│   ├── evidencias/           # testes, cobertura e capturas de tela
│   └── prototipos/
├── .github/workflows/ci.yml
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── CHANGELOG.md
├── run_backend.bat
└── run_frontend.bat
```

---

## Sobre o projeto

O TrainUp é um **Projeto Integrador** desenvolvido na **Faculdade de Tecnologia SENAI Félix Guisard**, com finalidade exclusivamente acadêmica e educacional.

## Licença

Este projeto não possui licença de uso definida. Por ser um trabalho acadêmico, não é destinado a uso comercial.