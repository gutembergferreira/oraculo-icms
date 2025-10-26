# Relatórios

Os relatórios podem ser gerados em PDF e XLSX a partir do módulo de auditoria. Utilizamos WeasyPrint para renderização de PDF e openpyxl para planilhas.

1. Execute a auditoria pela interface ou API (`POST /api/v1/orgs/{org_id}/audits/run` ou uploads).
2. Aguarde o processamento pelo worker Celery e consulte o resumo em `GET /api/v1/orgs/{org_id}/audits/baseline/summary`.
3. Baixe o arquivo pelo endpoint apropriado (`GET /api/v1/orgs/{org_id}/audits/{audit_id}/reports/pdf` ou `/reports/xlsx`) ou diretamente na interface React.

As exportações respeitam as permissões do plano contratado e registram logs em `audit_logs`.
