# Backlog do produto — TrainUp

Backlog derivado da ERS v2.2. Situação em 25/10/2026 (fim da Sprint 2).

**Legenda de status:** ✅ Concluído · 🔄 Em andamento · 📋 Planejado (Sprint 3) · 💡 Evolução futura

**Prioridade:** Crítica · Alta · Média · Baixa

---

## 1. Requisitos funcionais

### Acesso e vínculo

| ID | Item | Prioridade | Sprint | Status |
| --- | --- | --- | --- | --- |
| RF01 | Registrar-se (Personal ou Aluno) | Alta | 2 | ✅ |
| RF02 | Autenticar-se (login) | Alta | 2 | ✅ |
| RF03 | Recuperar senha | Média | 2 | ✅ |
| RF04 | Solicitar vínculo com Personal (código de convite) | Alta | 2 | ✅ |
| RF05 | Aprovar ou recusar solicitação de vínculo | Alta | 2 | ✅ |
| RF28 | Encerrar sessão (logout) | Alta | 2 | ✅ |

### Alunos

| ID | Item | Prioridade | Sprint | Status |
| --- | --- | --- | --- | --- |
| RF06 | Cadastrar aluno (pelo Personal) | Alta | 2 | ✅ |
| RF07 | Consultar, editar e remover alunos | Média | 2 | ✅ |

### Treinos

| ID | Item | Prioridade | Sprint | Status |
| --- | --- | --- | --- | --- |
| RF08 | Gerenciar exercícios (catálogo base e biblioteca própria) | Alta | 2 | ✅ |
| RF09 | Gerenciar fichas de treino | Alta | 2 | ✅ |
| RF10 | Consultar fichas de treino (ficha do dia) | Alta | 2 | ✅ |
| RF11 | Executar sessão de treino e registrar séries | Crítica | 2 | ✅ |
| RF12 | Finalizar sessão e obter resumo | Crítica | 2 | ✅ |

### Evolução e relatórios (Ciência de Dados)

| ID | Item | Prioridade | Sprint | Status |
| --- | --- | --- | --- | --- |
| RF13 | Consultar sessões, resumos e evolução de carga | Crítica | 2 | ✅ |
| RF14 | Consultar alertas de estagnação | Alta | 2 | ✅ |
| RF15 | Consultar dicas de nutrição e recuperação | Baixa | 2 | ✅ |
| RF16 | Consultar relatório de evolução do aluno | Crítica | 2 | ✅ |
| RF17 | Registrar observação do Personal no relatório | Média | 2 | ✅ |
| RF18 | Baixar relatório em PDF | Alta | 2 | ✅ |
| RF27 | Painel de visão geral do Personal | Média | 2 | ✅ |

### Agenda

| ID | Item | Prioridade | Sprint | Status |
| --- | --- | --- | --- | --- |
| RF19 | Agendar aula | Alta | 2 | ✅ |
| RF20 | Consultar agenda e cancelar aula | Alta | 2 | ✅ |
| RF21 | Concluir aula (Personal) | Média | 2 | ✅ |

### Catraca virtual (Automação Industrial — simulação)

| ID | Item | Prioridade | Sprint | Status |
| --- | --- | --- | --- | --- |
| RF22 | Realizar check-in na catraca | Crítica | 2 | ✅ |
| RF23 | Confirmar passagem na catraca | Alta | 2 | ✅ |
| RF24 | Consultar estado da catraca e histórico de acessos | Alta | 2 | ✅ |
| RF25 | Simular cenários na catraca | Média | 2 | ✅ |
| RF26 | Rearmar catraca | Média | 2 | ✅ |

---

## 2. Requisitos não funcionais

| ID | Item | Status | Evidência |
| --- | --- | --- | --- |
| RNF01 | Segurança de autenticação | ✅ | Testes de backend (`backend/tests`) |
| RNF02 | Controle de acesso por perfil | ✅ | `test_permissions.py` |
| RNF03 | Tempo de resposta (até 3 s) | ✅ | `docs/evidencias/evidencias-api.txt` |
| RNF04 | Usabilidade e responsividade | ✅ | `docs/evidencias/prints/` e `rnf04-overflow.txt` |
| RNF05 | Computação em Nuvem (EC2 + code-server + Docker Compose) | ✅ | `docs/evidencias/prints/14-ec2-code-server.png` |
| RNF06 | Histórico de treino apenas incremental | ✅ | Testes de backend |
| RNF07 | Manutenibilidade (camadas e migrations) | ✅ | Alembic `0001` e `0002` |
| RNF08 | Desempenho da catraca (ciclo até 1 s) | ✅ | `docs/evidencias/evidencias-api.txt` |

---

## 3. Sprint 3 (09/11 a 30/11/2026) — planejado

| # | Item | Prioridade | Status |
| --- | --- | --- | --- |
| S3-01 | Conclusão das funcionalidades obrigatórias e estabilização do MVP | Alta | 📋 |
| S3-02 | Testes finais e de integração (relatório de testes) | Alta | 📋 |
| S3-03 | Manual de instalação (incluindo a execução na EC2 com code-server) | Alta | 📋 |
| S3-04 | README completo | Média | 📋 |
| S3-05 | Matriz de rastreabilidade final | Alta | 📋 |
| S3-06 | ERS final e diagramas atualizados | Alta | 📋 |
| S3-07 | Backlog final, limitações e evolução | Média | 📋 |
| S3-08 | Apresentação da Mostra de Projetos (07 a 11/12/2026) | Alta | 📋 |
| S3-09 | Evidências de participação individual | Alta | 📋 |

---

## 4. Débitos técnicos e melhorias (limitações conhecidas — ERS 6.4)

Candidatos a entrar na Sprint 3 se sobrar tempo, ou a evolução futura.

| ID | Item | Impacto | Status |
| --- | --- | --- | --- |
| TD01 | Retomar a sessão de treino em andamento após recarregar a página | Usabilidade | 💡 |
| TD02 | Tela para editar o cadastro do aluno (`PUT /users/{id}` hoje só pela API) | Usabilidade | 💡 |
| TD03 | Invalidar JWT ao trocar a senha por `PUT /users/{id}` | Segurança | 💡 |
| TD04 | Revalidar nome duplicado na edição de exercício | Qualidade de dados | 💡 |
| TD05 | `GET /workouts/today` sem `weekday` usa o dia em UTC | Fuso horário | 💡 |
| TD06 | Testes de front-end das telas de negócio (Agenda, Treinar, Catraca) | Qualidade | 💡 |
| TD07 | Testes de interface ponta a ponta | Qualidade | 💡 |
| TD08 | Mover regras de CRUD, acesso e conflito de agenda dos routers para `services/` | Manutenibilidade | 💡 |
| TD09 | Painel da catraca com WebSocket/SSE no lugar de consulta a cada 2 s | Desempenho | 💡 |

---

## 5. Evolução futura (fora do MVP)

| ID | Item | Status |
| --- | --- | --- |
| EV01 | Envio e verificação de e-mail (recuperação de senha sem usar o log do backend) | 💡 |
| EV02 | Rate limit de login compartilhado (Redis) para várias instâncias | 💡 |
| EV03 | Leitor físico (RFID/QR) integrado à catraca no lugar do simulador | 💡 |
| EV04 | Hospedagem de produção (HTTPS, domínio, `SEED_DEMO=false`) | 💡 |
| EV05 | Aplicativo nativo | 💡 |
| EV06 | Pagamentos e chat | 💡 |

> Itens EV05 e EV06 estão explicitamente **fora do escopo** do MVP (ERS 6.1).