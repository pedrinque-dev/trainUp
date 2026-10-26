# Atas de reunião — Sprint 2 (21/09 a 26/10/2026)

**Projeto:** TrainUp — Projeto Integrador Interdisciplinar II
**Curso:** Análise e Desenvolvimento de Sistemas — SENAI Taubaté
**Orientador:** Prof. Wesley Fioreze
**Equipe:** Ana Carolina Gonçalves, Bárbara Yasmin Pimenta dos Santos Tobias, Luana Gabrielle Ferreira Guedes Paes, Pedro Augusto Lombardi da Costa, Ruan Monteiro Brito

> Este arquivo complementa o `CHANGELOG.md` e a seção 6 da ERS v2.2 (entregável 9 da Sprint 2).
> As referências D01–D15, RF, RN e RNF correspondem à ERS v2.2.

---

## Ata 01 — 21/09/2026 — Abertura da Sprint 2

**Presentes:** equipe completa 

**Pauta**
1. Revisão das correções da Sprint 1.
2. Planejamento da Sprint 2 e divisão dos entregáveis.
3. Escolha da stack de implementação.

**Discussões e decisões**
- A Sprint 2 passa a converter a especificação em sistema executável: back-end FastAPI + PostgreSQL, front-end React + Tailwind, Docker Compose.
- Banco com migrations Alembic e seed de demonstração (D10, D11).
- Datas gravadas em UTC; interface e relatórios em America/Sao_Paulo (D01).
- Ambiente de desenvolvimento em AWS EC2 com code-server (D08).

**Responsáveis e prazos**
| Item | Responsável | Prazo |
|---|---|---|
| Código-fonte atualizado e versionado | Pedro | 21/09 |
| Banco de dados e migrations | Pedro | 21/09 |
| Fluxo principal ponta a ponta | Ana | 28/09 |

**Dificuldades:** nenhuma crítica registrada.

---

## Ata 02 — 28/09/2026 — Fluxo principal e interface

**Presentes:** equipe completa 

**Pauta**
1. Situação do fluxo cadastro → treino → evolução → relatório.
2. Integração das telas React com a API real.
3. Revisão do núcleo do MVP.

**Discussões e decisões**
- **Mudança de escopo:** a evolução física deixa de ser registrada manualmente pelo Personal (peso, medidas) e passa a ser **calculada das séries executadas pelo Aluno** (carga, repetições, volume, recordes, estagnação). Motivo: gera dados reais pelo uso, elimina retrabalho do Personal e reforça Ciência de Dados (ERS 6.1; RN12 e RN13 substituem as antigas RN04/RN05).
- Relatório passa a ser **calculado sob demanda**, e não persistido como snapshot, para evitar dados desatualizados.
- Modelo de usuário simplificado: tabela única `users` com `role` e `personal_id`.
- Interface clara responsiva, com menu lateral no desktop e barra inferior no celular, substituindo o protótipo em tema escuro (RNF04).

**Dificuldades:** datas aparecendo no horário errado por causa do UTC; tratada com conversão explícita local↔UTC nos formulários (D01).

---

## Ata 03 — 05/10/2026 — Vínculo, segurança e catálogo

**Presentes:** equipe completa 

**Pauta**
1. Regras de vínculo Aluno–Personal.
2. Autenticação e segurança.
3. Catálogo de exercícios.

**Discussões e decisões**
- **Vínculo por código de convite** de 8 caracteres, com solicitação PENDENTE e aprovação do Personal, no lugar da lista pública de personais (privacidade e controle; RN01, RN02).
- Cadastro de Personal passa a exigir **código de cadastro do ambiente** (`PERSONAL_SIGNUP_CODE`), evitando contas falsas (RN10).
- JWT com `sub`, `role` e versão do token (`token_version`); logout e redefinição de senha revogam tokens; bcrypt direto; rate limit de login (RN08, RNF01).
- Catálogo base de 32 exercícios somente leitura + biblioteca própria por Personal (RN11).
- **Suplementos removidos:** substituídos por "Dicas de nutrição e recuperação", conteúdo educativo geral com aviso para procurar nutricionista ou médico (D02, RN14). Motivo: evitar recomendação sem habilitação profissional.

**Dificuldades:** risco de recomendação de suplementos sem habilitação (tratado, D02).

---

## Ata 04 — 12/10/2026 — Automação industrial (catraca virtual)

**Presentes:** equipe completa 

**Pauta**
1. Integração da agenda com o check-in.
2. Catraca virtual e simulador.
3. Segurança e concorrência.

**Discussões e decisões**
- **Mudança de escopo:** Serviços, Disponibilidade e confirmação PENDENTE→CONFIRMADO do Sprint 1 foram removidos. A agenda passa a ter aulas AGENDADO → CHECKIN → CONCLUIDO/CANCELADO, integradas à catraca (RN03, RN04, RN05).
- **Catraca virtual** com máquina de estados persistida no banco, 2 catracas, entradas/saídas de CLP, simulador de 5 cenários, painel SCADA e histórico `access_logs` (RF22–RF26; D03, RN09).
- Eventos do simulador marcados com `simulated = true` e rótulo "Simulação" na tela; a catraca nunca é apresentada como equipamento real (D04, RN16).
- `access_logs.personal_id`, `access_logs.schedule_id` e `turnstiles.last_aluno_id` ficam sem chave estrangeira, para o histórico sobreviver à remoção de aulas (D05).
- Confirmação de passagem restrita ao aluno liberado ou ao seu Personal (D15, RN02).
- Bloqueio de linha (`SELECT FOR UPDATE`) no PostgreSQL para serializar leituras simultâneas.

**Dificuldades**
- Demonstrar automação sem hardware: resolvido com catraca virtual e simulador (D03, D04).
- Concorrência na catraca: mitigada no PostgreSQL; o SQLite dos testes ignora o bloqueio (limitação registrada em 6.4).

---

## Ata 05 — 19/10/2026 — Testes, API e atualização da ERS

**Presentes:** equipe completa 

**Pauta**
1. Testes automatizados e evidências.
2. Documentação da API.
3. Atualização da ERS (versão 2.0).

**Discussões e decisões**
- Documentação Swagger/OpenAPI revisada e exportada para `docs/api/` (prints e `openapi.json`), por Pedro com apoio de Ruan.
- Testes de back-end (pytest) e front-end (vitest) com saídas em `docs/evidencias/`; CI no GitHub Actions executando ruff, pytest, vitest, build e `docker compose` (D14).
- Rate limit de login: o cabeçalho `X-Real-IP` só é aceito atrás do nginx e há teto de 20 falhas por e-mail, independente do IP (D12).
- `PRAGMA foreign_keys=ON` no SQLite, igualando seu comportamento ao do PostgreSQL (D13).
- Backlog atualizado em `docs/BACKLOG.md` (Bárbara).
- ERS atualizada para a versão 2.0 com os entregáveis da Sprint 2.

**Dificuldades**
- Exclusão de exercício em uso passando no SQLite por chaves estrangeiras desligadas (tratado, D13).
- Forjar o IP para burlar o limite de login (tratado, D12).
- Contraste insuficiente das cores da marca em botões e textos; adotado azul #1A73C8 em ações e cores vivas apenas em preenchimentos (D09).

---

## Ata 06 — 24 e 25/10/2026 — Revisão final da Sprint 2

**Presentes:** equipe completa 

**Pauta**
1. Revisão do documento (versões 2.1 e 2.2).
2. Coleta final das evidências.
3. Checklist de entrega no Classroom.

**Discussões e decisões**
- ERS v2.1 (24/10): requisitos alinhados à implementação, tecnologias e evidências de testes nos apêndices.
- ERS v2.2 (25/10): conferência da região da instância EC2 (us-east-1), versões das ferramentas e referências às evidências (`docs/api`, backlog e changelog).
- Evidências coletadas em 24/10: RNF03 (evolução com média de 18,5 ms e máximo de 51,5 ms), RNF08 (ciclos da catraca de 0 a 1 ms) e RNF04 (26 capturas sem rolagem horizontal).
- Resultados finais: 61 testes de back-end (cobertura 95,47%), 64 de front-end (cobertura 97,73%), ruff e build aprovados.
- **Limitações aceitas no MVP** (ERS 6.4): sem envio de e-mail (recuperação de senha pelo log do backend, D06); rate limit em memória (D07); painel de automação por polling a cada 2 s; sem hospedagem de produção.
- **Fora do escopo mantido:** pagamentos, chat, hardware real de catraca, aplicativo nativo, envio e verificação de e-mail.
- Combinado que **todos os integrantes realizam a entrega** no Classroom, com o mesmo link do repositório e o mesmo PDF da ERS v2.2.

**Encaminhamentos para a Sprint 3 (09/11 a 30/11/2026)**
- Conclusão das funcionalidades obrigatórias, testes finais e de integração.
- Manual de instalação, README completo e matriz de rastreabilidade final.
- ERS final, backlog final e preparação da Mostra de Projetos (07 a 11/12/2026).