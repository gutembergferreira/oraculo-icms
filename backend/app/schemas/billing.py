from app.schemas.base import OraculoBaseModel


class CheckoutSessionRequest(OraculoBaseModel):
    org_id: int
    plan_code: str


class CheckoutSessionResponse(OraculoBaseModel):
    checkout_url: str


class PortalSessionRequest(OraculoBaseModel):
    org_id: int


class PortalSessionResponse(OraculoBaseModel):
    portal_url: str
