# Changelog — TrainUp

Registro das mudanças de escopo, decisões e correções do projeto, por Sprint.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Detalhamento e justificativas: ERS v2.2, seção 6.

---

## [Sprint 3] — 09/11 a 30/11/2026 (planejada)

### Previsto
- Conclusão das funcionalidades obrigatórias e testes finais.
- Manual de instalação, README completo e matriz de rastreabilidade final.
- ERS final, backlog final e preparação da Mostra de Projetos.

---

## [Sprint 2] — 21/09 a 26/10/2026

Converte a especificação da Sprint 1 no que foi efetivamente construído.

### Adicionado
- Fluxo principal de ponta a ponta: cadastro → treino → evolução → indicadores → relatório.
- Catraca virtual com máquina de estados persistida, 2 catracas, entradas e saídas de CLP, simulador de 5 cenários, painel SCADA e histórico (`access_logs`) — RF22 a RF26. Sempre identificada como simulação.
- Código de convite de 8 caracteres e aprovação do Personal para o vínculo (`link_requests`).
- Código de cadastro do ambiente (`PERSONAL_SIGNUP_CODE`) para criar contas de Personal.
- Catálogo base de 32 exercícios (somente leitura) e biblioteca própria por Personal; fichas com dia da semana.
- Relatório de evolução calculado sob demanda, com observação do Personal e exportação em PDF (reportlab).
- Visão geral do Personal e Início do Aluno (RF27).
- Dicas de nutrição e recuperação (RF15).
- Migrations Alembic (`0001_baseline`, `0002_token_version`) executadas na subida da API.
- Seed de demonstração com 7 contas e históricos distintos (`SEED_DEMO`).
- Docker Compose (db, backend, frontend/nginx), `.env.example` e Swagger em `/api/docs` (`ENABLE_DOCS`).
- Integração contínua (GitHub Actions): ruff, pytest, vitest, build e `docker compose`.
- 61 testes de backend (cobertura 95,47%) e 64 de frontend (cobertura 97,73%), com saídas em `docs/evidencias/`.
- Ambiente de desenvolvimento em AWS EC2 com code-server (RNF05).

### Alterado
- **Núcleo do MVP:** a evolução deixou de ser registrada manualmente pelo Personal (peso, medidas) e passou a ser calculada das séries executadas pelo Aluno (carga, repetições, volume, recordes, estagnação).
- **Relatórios:** deixaram de ser persistidos como snapshot e passaram a ser calculados sob demanda.
- **Modelo de usuário:** tabela única `users` com `role`, chaves inteiras e vínculo por `personal_id`.
- **Vínculo:** deixou de ser imediato por lista pública de Personals; agora exige solicitação PENDENTE e aprovação.
- **Agenda:** serviços e disponibilidade removidos; aulas seguem AGENDADO → CHECKIN → CONCLUIDO ou CANCELADO.
- **Autenticação:** JWT com `sub`, `role` e versão do token, bcrypt direto, rate limit por IP/e-mail, logout com revogação e recuperação de senha por token de 30 minutos.
- **API:** versionada em `/api/v1`, em camadas routers / services / models / schemas.
- **Banco:** 11 tabelas com chaves inteiras; SQLite em testes e desenvolvimento local, PostgreSQL no Compose.
- **Interface:** tema escuro do protótipo substituído por interface clara, responsiva, com contraste AA (menu lateral no desktop, barra inferior no celular).
- **Ambiente EC2:** como a porta 80 é ocupada pelo code-server, o front-end é publicado na porta 8081 apenas na instância (RNF05 do ERS atualizado). O padrão do projeto continua sendo a porta 80.

### Removido
- Lista pública de Personals (`GET /api/personal-trainers`).
- Serviços, disponibilidade e agendamento com confirmação.
- Suplementos (substituídos por dicas educativas com aviso para procurar nutricionista).
- Camada `repository` (consultas via SQLAlchemy nos routers e serviços).

### Corrigido / Segurança
- Datas gravadas em UTC e exibidas em America/Sao_Paulo, com conversão explícita (D01).
- `X-Real-IP` aceito só atrás do nginx (`TRUST_PROXY_HEADERS`) e teto de falhas por e-mail, evitando burlar o limite de login (D12).
- `PRAGMA foreign_keys=ON` no SQLite, igualando o comportamento ao PostgreSQL (D13).
- `POST /automacao/passagem` restrito ao aluno liberado ou ao seu Personal (D15).
- API não inicia em produção sem `SECRET_KEY` de pelo menos 32 caracteres.
- Cores da marca ajustadas para contraste AA em botões e textos (D09).

### Fora do escopo (mantido)
- Pagamentos, chat, hardware real de catraca, aplicativo nativo, envio e verificação de e-mail.

---

## [Sprint 1] — 03/08 a 14/09/2026

### Adicionado
- Levantamento de requisitos, modelagem de dados e do domínio.
- Diagramas UML e protótipo de alta fidelidade (tema escuro).
- Repositório do projeto e documento inicial da demanda.
- Primeira versão da ERS.