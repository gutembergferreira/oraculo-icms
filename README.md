# Oráculo ICMS

Plataforma SaaS multiempresa para auditoria fiscal de XMLs de NF-e.

## Visão Geral

O projeto "Oráculo ICMS" é uma solução completa para ingestão, análise e auditoria de documentos fiscais eletrônicos (NF-e) com foco em conformidade tributária brasileira. A aplicação fornece upload e parsing de XMLs, motor de regras com sugestões de ajustes e relatórios técnicos/gerenciais, além de gestão de planos com Stripe.

### Componentes herdados do `zfm-calculator`

- **Parser NF-e**: `backend/app/utils/xml_parser.py` realiza a leitura estruturada dos XMLs, identificando cabeçalho, itens e tributos utilizados pelo motor de cálculo.
- **Serviço de ingestão**: `backend/app/services/invoice_ingestion.py` grava arquivos no storage local multi-tenant e persiste notas em `invoices`/`invoice_items`.
- **Motor de auditoria ZFM**: `backend/app/services/zfm_calculator.py` aplica regras fiscais (ST, CEST, divergência de total) gerando achados em `audit_findings`.
- **Tarefas assíncronas**: `backend/app/workers/tasks.py` expõe `parse_xml_batch` e `run_audit`, utilizando os componentes acima para lotes ZIP e execuções on-demand.

### Roadmap Interno

- **v0.1**: Upload/parse/consulta.
- **v0.2**: Auditoria baseline + relatórios.
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
3. O `ZFMAuditCalculator` executa as regras herdadas do zfm-calculator e persiste os achados na tabela `audit_findings`, vinculados a um `audit_run` multi-tenant.
4. A listagem/detalhe de notas (`GET /api/v1/orgs/{org_id}/invoices`) e o painel de auditorias (`GET /api/v1/orgs/{org_id}/audits`) consomem diretamente essas entidades.

## Comandos úteis

- `cd backend && poetry install && poetry run pytest` — executa a suíte de testes (unitários e integração do fluxo de upload → auditoria).
- `cd frontend && npm install && npm run dev` — inicia o front-end com a nova UI integrada aos endpoints de upload/auditoria.

## Licença

MIT.
