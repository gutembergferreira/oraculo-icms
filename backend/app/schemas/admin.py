from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas.base import OraculoBaseModel


class NavigationLink(OraculoBaseModel):
    label: str
    path: str


class ApiKeyRead(OraculoBaseModel):
    id: int
    name: str
    prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None


class ApiKeyCreateResponse(OraculoBaseModel):
    api_key: ApiKeyRead
    token: str


class ApiKeyCreatePayload(OraculoBaseModel):
    name: str


class PageContent(OraculoBaseModel):
    slug: str
    title: str
    content: str
    updated_at: datetime | None


class PageUpdatePayload(OraculoBaseModel):
    title: str
    content: str


class AdminUserRead(OraculoBaseModel):
    id: int
    email: str
    first_name: str | None
    last_name: str | None
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    organizations: list[str]


class AdminUserUpdatePayload(OraculoBaseModel):
    is_active: bool
    is_superuser: bool


class PlanAdminRead(OraculoBaseModel):
    id: int
    code: str
    name: str
    monthly_price_cents: int
    features: dict[str, Any]
    limits: dict[str, Any]
    stripe_product_id: str | None
    stripe_price_id: str | None


class StripeConfig(OraculoBaseModel):
    public_key: str | None
    secret_key: str | None
    webhook_secret: str | None


class StripeConfigUpdatePayload(OraculoBaseModel):
    public_key: str | None = None
    secret_key: str | None = None
    webhook_secret: str | None = None


class AdminOrganizationSummary(OraculoBaseModel):
    id: int
    name: str
    slug: str


class ActionMessage(OraculoBaseModel):
    message: str
