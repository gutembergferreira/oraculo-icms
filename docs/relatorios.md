# Relatórios

Os relatórios podem ser gerados em PDF e XLSX a partir do módulo de auditoria. Utilizamos WeasyPrint para renderização de PDF e openpyxl para planilhas.

1. Execute a auditoria pela interface ou API.
2. Aguarde o processamento pelo worker Celery.
3. Baixe o arquivo pelo endpoint apropriado ou diretamente na interface.

As exportações respeitam as permissões do plano contratado e registram logs em `audit_logs`.
