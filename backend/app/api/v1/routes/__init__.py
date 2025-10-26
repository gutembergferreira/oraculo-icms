from fastapi import APIRouter

from . import (
    auth,
    organizations,
    invoices,
    audits,
    billing,
    plans,
    health,
    uploads,
    rules,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(plans.router, prefix="/public", tags=["Planos Públicos"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(organizations.router, prefix="/orgs", tags=["Organizações"])
api_router.include_router(invoices.router, prefix="/orgs", tags=["Notas Fiscais"])
api_router.include_router(audits.router, prefix="/orgs", tags=["Auditorias"])
api_router.include_router(uploads.router, prefix="/orgs", tags=["Uploads"])
api_router.include_router(rules.router, prefix="/rules", tags=["Regras"])
api_router.include_router(health.router, tags=["Sistema"])
