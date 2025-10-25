# Guia Stripe

1. Configure os produtos `plan_free`, `plan_pro`, `plan_business` e `plan_enterprise` no Stripe Dashboard.
2. Registre os preços mensais correspondentes e copie os IDs para o seed do banco.
3. No painel Stripe, habilite o modo test e gere chaves públicas/privadas.
4. Configure o webhook apontando para `https://seu-dominio.com/api/v1/billing/webhook` com os eventos:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Preencha as variáveis `STRIPE_*` no `.env`.
6. Para testar localmente, utilize o Stripe CLI com `stripe listen --forward-to localhost:8000/api/v1/billing/webhook`.
