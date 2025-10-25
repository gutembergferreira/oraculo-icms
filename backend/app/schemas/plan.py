from app.schemas.base import OraculoBaseModel


class PlanPublic(OraculoBaseModel):
    code: str
    name: str
    monthly_price_cents: int
    features: dict
    limits: dict
