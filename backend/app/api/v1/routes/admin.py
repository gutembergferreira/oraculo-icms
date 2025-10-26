from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db_session
from app.models.api_key import ApiKey
from app.models.organization import Organization
from app.schemas import (
    ApiKeyCreatePayload,
    ApiKeyCreateResponse,
    ApiKeyRead,
    NavigationLink,
    PageContent,
    PageUpdatePayload,
)
from app.services.api_keys import generate_api_key
from app.services.page_service import PageService

router = APIRouter()

NAVIGATION_LINKS: list[NavigationLink] = [
    NavigationLink(label="Home", path="/"),
    NavigationLink(label="Dashboard", path="/dashboard"),
    NavigationLink(label="Notas", path="/invoices"),
    NavigationLink(label="Auditorias", path="/audits"),
    NavigationLink(label="Planos", path="/billing"),
    NavigationLink(label="Regras", path="/rules"),
    NavigationLink(label="Administração", path="/admin"),
]


@router.get("/navigation", response_model=List[NavigationLink])
def list_navigation(
    _: None = Depends(get_current_superuser),
) -> list[NavigationLink]:
    return NAVIGATION_LINKS


@router.get("/pages/home", response_model=PageContent)
def get_home_page(
    db: Session = Depends(get_db_session),
    _: None = Depends(get_current_superuser),
) -> PageContent:
    service = PageService(db)
    page = service.get_or_create(
        "home",
        default_title="Oráculo ICMS",
        default_content="Centralize sua gestão tributária.",
    )
    return PageContent(
        slug=page.slug,
        title=page.title,
        content=page.content,
        updated_at=page.updated_at,
    )


@router.put("/pages/home", response_model=PageContent)
def update_home_page(
    payload: PageUpdatePayload,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_superuser),
) -> PageContent:
    service = PageService(db)
    page = service.get_or_create(
        "home",
        default_title="Oráculo ICMS",
        default_content="Centralize sua gestão tributária.",
    )
    page = service.update(
        page,
        title=payload.title,
        content=payload.content,
        user_id=current_user.id,
    )
    db.commit()
    return PageContent(
        slug=page.slug,
        title=page.title,
        content=page.content,
        updated_at=page.updated_at,
    )


def _org_or_404(db: Session, org_id: int) -> Organization:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organização não encontrada")
    return org


@router.get("/orgs/{org_id}/api-keys", response_model=List[ApiKeyRead])
def list_org_api_keys(
    org_id: int,
    db: Session = Depends(get_db_session),
    _: None = Depends(get_current_superuser),
) -> list[ApiKeyRead]:
    _org_or_404(db, org_id)
    keys = (
        db.query(ApiKey)
        .filter(ApiKey.org_id == org_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )
    return [
        ApiKeyRead(
            id=key.id,
            name=key.name,
            prefix=key.prefix,
            is_active=key.is_active,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
        )
        for key in keys
    ]


@router.post("/orgs/{org_id}/api-keys", response_model=ApiKeyCreateResponse)
def create_org_api_key(
    org_id: int,
    payload: ApiKeyCreatePayload,
    db: Session = Depends(get_db_session),
    _: None = Depends(get_current_superuser),
) -> ApiKeyCreateResponse:
    _org_or_404(db, org_id)
    api_key, token = generate_api_key(db, org_id=org_id, name=payload.name)
    db.commit()
    return ApiKeyCreateResponse(
        api_key=ApiKeyRead(
            id=api_key.id,
            name=api_key.name,
            prefix=api_key.prefix,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
        ),
        token=token,
    )
