# Documentação Geral

Este diretório centraliza guias para operação da plataforma Oráculo ICMS.

## Upload e auditoria multi-tenant

- **Uploads**: o endpoint `POST /api/v1/orgs/{org_id}/uploads/{xml|zip}` salva os arquivos por organização utilizando `InvoiceIngestor`.
- **Parser**: `XMLParser` transforma o XML em estruturas enriquecidas (cabeçalho, itens, tributos) reutilizadas pelo motor.
- **Auditoria**: `ZFMAuditCalculator` aplica regras herdadas do projeto `zfm-calculator`, grava achados em `audit_findings` e atualiza o status de `audit_runs`.
- **Baseline consolidado**: o serviço `AuditSummaryBuilder` agrega gravidade, recorrência e metadados para `GET /api/v1/orgs/{org_id}/audits/baseline/summary`, usado pelo dashboard do front-end.
- **Relatórios**: `AuditReportBuilder` gera PDF via WeasyPrint e planilhas XLSX com openpyxl por `GET /api/v1/orgs/{org_id}/audits/{audit_id}/reports/{pdf|xlsx}`.
- **Front-end**: as páginas `InvoicesPage` e `AuditPage` consomem os novos endpoints para exibir notas, itens, achados, indicadores baseline e realizar downloads de relatórios.

## Execução local

1. Inicie a API com `poetry run uvicorn app.main:app --reload` dentro de `backend/`.
2. Em outro terminal, suba o front-end com `npm run dev` dentro de `frontend/`.
3. Utilize `poetry run pytest` para validar parser, motor e fluxo completo de upload → auditoria.
