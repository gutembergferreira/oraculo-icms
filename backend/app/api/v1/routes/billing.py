from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.schemas import CheckoutSessionRequest, CheckoutSessionResponse, PortalSessionResponse

router = APIRouter()


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    payload: CheckoutSessionRequest, user=Depends(get_current_user)
) -> CheckoutSessionResponse:
    if payload.plan_code == "FREE":
        raise HTTPException(status_code=400, detail="Plano gratuito não requer checkout")

    url = f"https://stripe.test/checkout/{payload.plan_code.lower()}"
    return CheckoutSessionResponse(checkout_url=url)


@router.post("/portal", response_model=PortalSessionResponse)
def create_portal_session(user=Depends(get_current_user)) -> PortalSessionResponse:
    return PortalSessionResponse(portal_url="https://stripe.test/customer-portal")


@router.post("/webhook")
def stripe_webhook() -> dict:
    # Implementação simplificada apenas para documentação
    return {"received": True}
