# DevPortal

A API FastAPI publica documentação Swagger em `/api/v1/docs`. Para exemplos de requisições, utilize tokens obtidos no endpoint `/api/v1/auth/login`.

## Endpoints principais

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/orgs/{org_id}/uploads/xml`
- `POST /api/v1/orgs/{org_id}/audits/run`

## Exportações

Relatórios PDF e XLSX estarão disponíveis após a conclusão da auditoria em:

- `GET /api/v1/orgs/{org_id}/audits/{audit_id}/reports/pdf`
- `GET /api/v1/orgs/{org_id}/audits/{audit_id}/reports/xlsx`
