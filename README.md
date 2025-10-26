# Oráculo ICMS

Plataforma SaaS multiempresa para auditoria fiscal de XMLs de NF-e.

## Visão Geral

O projeto "Oráculo ICMS" é uma solução completa para ingestão, análise e auditoria de documentos fiscais eletrônicos (NF-e) com foco em conformidade tributária brasileira. A aplicação fornece upload e parsing de XMLs, motor de regras com sugestões de ajustes e relatórios técnicos/gerenciais, além de gestão de planos com Stripe.

### Componentes herdados do `zfm-calculator`

- **Parser NF-e**: `backend/app/utils/xml_parser.py` realiza a leitura estruturada dos XMLs, identificando cabeçalho, itens e tributos utilizados pelo motor de cálculo.
- **Serviço de ingestão**: `backend/app/services/invoice_ingestion.py` grava arquivos no storage local multi-tenant e persiste notas em `invoices`/`invoice_items`.
- **Motor de auditoria baseado em DSL**: `backend/app/services/zfm_calculator.py` carrega o baseline YAML e overrides da organização via `RuleSetService`, avaliando as regras com o `RuleEngine`.
- **Editor/DSL**: `backend/app/api/v1/routes/rules.py` expõe o editor de regras em YAML, compondo baseline global com overrides por organização e disponibilizando o pacote ZFM inicial (`backend/app/rules/packs/zfm_baseline.yaml`).
- **Tarefas assíncronas**: `backend/app/workers/tasks.py` expõe `parse_xml_batch` e `run_audit`, utilizando os componentes acima para lotes ZIP e execuções on-demand.

### Roadmap Interno

- **v0.1**: Upload/parse/consulta.
- **v0.2**: Auditoria baseline consolidada, relatórios PDF/XLSX e painel de indicadores.
- **v0.3**: Planos/Stripe.
- **v0.4**: Editor de regras (DSL) e ZFM pack.
- **v1.0**: API pública + MinIO + SSO opcional.

## Estrutura do Repositório

- `backend/`: Aplicação FastAPI, modelos SQLAlchemy, serviços, workers Celery e migrações Alembic.
- `frontend/`: Aplicação React + Vite + Tailwind + shadcn/ui.
- `infrastructure/`: Arquivos Docker, Nginx/Traefik e configurações de deploy.
- `docs/`: Guias funcionais e técnicos, inclusive especificações de regras e Stripe.
- `.github/workflows`: Pipelines CI/CD com lint, testes e build.

## Executando com Docker Compose

1. Copie o arquivo `.env.example` para `.env` e ajuste as variáveis.
2. Execute `docker compose -f infrastructure/docker-compose.dev.yml up --build`.
3. Acesse a aplicação web em `http://localhost:3000` e a API em `http://localhost:8000`.

## Fluxo de upload e auditoria

1. O front-end envia um XML individual para `POST /api/v1/orgs/{org_id}/uploads/xml` ou um ZIP para `POST /api/v1/orgs/{org_id}/uploads/zip`.
2. O `InvoiceIngestor` grava o arquivo, parseia via `XMLParser` e registra a nota fiscal e seus itens.
3. O `ZFMAuditCalculator` carrega o baseline global e o override da organização, avalia as regras DSL e persiste os achados na tabela `audit_findings`, vinculados a um `audit_run` multi-tenant.
4. O `AuditSummaryBuilder` agrega gravidade, recorrência e metadados de cada auditoria (baseline) e expõe em `GET /api/v1/orgs/{org_id}/audits/baseline/summary`.
5. A listagem/detalhe de notas (`GET /api/v1/orgs/{org_id}/invoices`) e o painel de auditorias (`GET /api/v1/orgs/{org_id}/audits`) consomem diretamente essas entidades, oferecendo download de relatórios PDF/XLSX por `GET /api/v1/orgs/{org_id}/audits/{audit_id}/reports/{pdf|xlsx}`.

## Cobrança recorrente e limites de plano

- Os planos **Free**, **Pro**, **Business** e **Enterprise** são sincronizados com o Stripe via catálogo em `app/services/plan_catalog.py`. Cada plano define limites (XML/mês, armazenamento em MB e número de usuários) e recursos habilitados (exportações, DSL, suporte).
- Durante o seed (`poetry run python -m app.cli`) os planos são criados na base local; execute `StripeBillingService.sync_plan_catalog()` (via shell ou tarefa dedicada) quando quiser gerar/atualizar produtos e preços no Stripe usando as variáveis `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET`.
- O endpoint `POST /api/v1/billing/create-checkout-session` cria a sessão de assinatura no Stripe e associa a organização ao plano escolhido. O webhook (`POST /api/v1/billing/webhook`) reage a `checkout.session.completed`, `customer.subscription.updated/deleted` e `invoice.payment_failed`, atualizando automaticamente `subscriptions` e `org_settings`.
- Os limites são aplicados no momento do upload: `OrgPlanLimiter` bloqueia excesso de XMLs mensais ou armazenamento, registrando consumo em `org_settings`. Para lotes ZIP o mesmo verificador atua dentro da tarefa Celery, evitando que o lote avance quando a cota é ultrapassada.

## Editor de regras (DSL YAML)

- A API fornece endpoints para consulta e edição das regras em `GET/PUT /api/v1/rules/baseline` (baseline global) e `GET/PUT /api/v1/rules/orgs/{org_id}` (override por organização), além do catálogo de pacotes (`GET /api/v1/rules/catalog`).
- O front-end em `frontend/src/pages/RulesPage.tsx` permite visualizar o baseline, editar o YAML de override, carregar o pacote "Pacote ZFM" e consultar a composição final que é aplicada nas auditorias.
- Os arquivos YAML seguem o DSL validado em `backend/app/services/rules_dsl.py`, aceitando campos `scope`, blocos `when` (all/any/not) e ações `then` com códigos de inconsistência, severidade, referências e evidências dinâmicas.

## Comandos úteis

- `cd backend && poetry install && poetry run pytest` — executa a suíte de testes (unitários e integração do fluxo de upload → auditoria).
- `cd frontend && npm install && npm run dev` — inicia o front-end com a nova UI integrada aos endpoints de upload/auditoria.

## Licença

MIT.
