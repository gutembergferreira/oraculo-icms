from __future__ import annotations

from datetime import datetime

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
