import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.organization import Organization
from app.schemas import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PortalSessionRequest,
    PortalSessionResponse,
)
from app.services.stripe_billing import StripeBillingService, StripeConfigurationError

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    payload: CheckoutSessionRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> CheckoutSessionResponse:
    org = db.get(Organization, payload.org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organização não encontrada")

    try:
        service = StripeBillingService(db)
        checkout_url = service.create_checkout_session(
            org=org,
            plan_code=payload.plan_code.upper(),
            customer_email=user.email,
        )
        db.commit()
        return CheckoutSessionResponse(checkout_url=checkout_url)
    except StripeConfigurationError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except stripe.error.StripeError as exc:  # pragma: no cover - erro externo
        db.rollback()
        logger.exception("Erro ao criar sessão de checkout no Stripe")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Falha ao comunicar com Stripe") from exc


@router.post("/portal", response_model=PortalSessionResponse)
def create_portal_session(
    payload: PortalSessionRequest,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PortalSessionResponse:
    org = db.get(Organization, payload.org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organização não encontrada")

    try:
        service = StripeBillingService(db)
        portal_url = service.create_portal_session(org=org)
        db.commit()
        return PortalSessionResponse(portal_url=portal_url)
    except StripeConfigurationError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except stripe.error.StripeError as exc:  # pragma: no cover - erro externo
        db.rollback()
        logger.exception("Erro ao criar portal de billing no Stripe")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Falha ao comunicar com Stripe") from exc


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db_session),
) -> dict[str, bool]:
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")
    try:
        service = StripeBillingService(db)
        event = service.parse_webhook(payload, signature)
        service.handle_event(event)
        db.commit()
    except StripeConfigurationError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except stripe.error.SignatureVerificationError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assinatura Stripe inválida") from exc
    except stripe.error.StripeError as exc:  # pragma: no cover - erro externo
        db.rollback()
        logger.exception("Falha ao processar webhook do Stripe")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Erro ao processar evento do Stripe") from exc
    except Exception as exc:  # pragma: no cover - salvaguarda
        db.rollback()
        logger.exception("Erro inesperado ao processar webhook Stripe")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao processar webhook") from exc
    return {"received": True}
