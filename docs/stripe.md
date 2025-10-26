# Guia Stripe

1. Configure o modo test no painel Stripe e gere as chaves `STRIPE_SECRET_KEY`, `STRIPE_PUBLIC_KEY` e `STRIPE_WEBHOOK_SECRET`.
2. Execute o seed padrão (`poetry run python -m app.cli`) e, com a chave secreta definida, utilize o serviço `StripeBillingService.sync_plan_catalog()` para criar/atualizar os produtos `plan_free`, `plan_pro`, `plan_business` e `plan_enterprise`, bem como os preços mensais (`lookup_key` `{plan}_monthly`).
3. Configure o webhook apontando para `https://seu-dominio.com/api/v1/billing/webhook` com os eventos:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Preencha as variáveis `STRIPE_*` no `.env` e reinicie a aplicação para que `StripeBillingService` carregue as credenciais.
5. Para testar localmente, utilize o Stripe CLI com `stripe listen --forward-to localhost:8000/api/v1/billing/webhook` e inicie um checkout por `POST /api/v1/billing/create-checkout-session`.
