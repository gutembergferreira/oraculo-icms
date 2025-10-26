# Documentação Geral

Este diretório centraliza guias para operação da plataforma Oráculo ICMS.

## Upload e auditoria multi-tenant

- **Uploads**: o endpoint `POST /api/v1/orgs/{org_id}/uploads/{xml|zip}` salva os arquivos por organização utilizando `InvoiceIngestor`.
- **Parser**: `XMLParser` transforma o XML em estruturas enriquecidas (cabeçalho, itens, tributos) reutilizadas pelo motor.
- **Auditoria**: `ZFMAuditCalculator` compõe o baseline global com o override da organização via `RuleSetService`, avalia as regras DSL com o `RuleEngine` e atualiza `audit_runs`/`audit_findings`.
- **Editor de regras**: `GET/PUT /api/v1/rules/baseline` e `GET/PUT /api/v1/rules/orgs/{org_id}` permitem versionar o YAML (com o pacote `zfm_baseline.yaml` como ponto de partida) e visualizar o resultado efetivo aplicado às auditorias.
- **Baseline consolidado**: o serviço `AuditSummaryBuilder` agrega gravidade, recorrência e metadados para `GET /api/v1/orgs/{org_id}/audits/baseline/summary`, usado pelo dashboard do front-end.
- **Relatórios**: `AuditReportBuilder` gera PDF via WeasyPrint e planilhas XLSX com openpyxl por `GET /api/v1/orgs/{org_id}/audits/{audit_id}/reports/{pdf|xlsx}`.
- **Front-end**: as páginas `InvoicesPage`, `AuditPage` e `RulesPage` consomem os novos endpoints para exibir notas, achados, indicadores baseline, relatórios e o editor de regras DSL.

## Planos, Stripe e enforcement de limites

- **Catálogo de planos**: `app/services/plan_catalog.py` lista Free, Pro, Business e Enterprise com respectivos recursos (`plan_features`) e limites (`plan_limits`). Esses dados são semeados na base e replicados para o Stripe via `StripeBillingService.sync_plan_catalog`.
- **Checkout e portal**: a rota `POST /api/v1/billing/create-checkout-session` utiliza `StripeBillingService` para criar sessões de assinatura com o `plan_code` escolhido; `POST /api/v1/billing/portal` abre o customer portal do Stripe quando a organização possui `stripe_customer_id` associado.
- **Webhooks**: `POST /api/v1/billing/webhook` valida a assinatura (`STRIPE_WEBHOOK_SECRET`) e processa eventos (`checkout.session.completed`, `customer.subscription.updated/deleted`, `invoice.payment_failed`), atualizando `subscriptions` e replicando limites/recursos em `org_settings`.
- **Aplicação de limites**: `OrgPlanLimiter` atua nos uploads (`/uploads/xml` e `/uploads/zip`) e dentro da task `parse_xml_batch`, bloqueando excedentes de XML por mês ou armazenamento antes de persistir dados.

## Execução local

1. Inicie a API com `poetry run uvicorn app.main:app --reload` dentro de `backend/`.
2. Em outro terminal, suba o front-end com `npm run dev` dentro de `frontend/`.
3. Utilize `poetry run pytest` para validar parser, motor e fluxo completo de upload → auditoria.
