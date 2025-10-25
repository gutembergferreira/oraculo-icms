# Planos e Limites

Os planos disponíveis e seus limites padrão:

| Plano | Preço Mensal | Uploads/Mês | Armazenamento (MB) | Usuários Máx. | Recursos |
|-------|---------------|-------------|--------------------|---------------|----------|
| FREE | R$ 0,00 | 200 | 512 | 3 | Exportações desativadas |
| PRO | R$ 499,00 | 2.000 | 5.120 | 10 | PDF, XLSX, regras ZFM |
| BUSINESS | R$ 1.299,00 | 6.000 | 20.480 | 25 | API pública, storage S3 |
| ENTERPRISE | Sob consulta | Ilimitado sob contrato | 102.400 | 100 | Consultor dedicado |

Os limites são aplicados via `org_settings`. Webhooks do Stripe atualizam os valores quando a assinatura muda de status.
