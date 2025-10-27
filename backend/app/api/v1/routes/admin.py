from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db_session
from app.core.config import settings
from app.models.api_key import ApiKey
from app.models.organization import Organization
from app.models.plan import Plan
from app.models.user import User
from app.schemas import (
    ApiKeyCreatePayload,
    ApiKeyCreateResponse,
    ApiKeyRead,
    AdminOrganizationSummary,
    AdminUserRead,
    AdminUserUpdatePayload,
    ActionMessage,
    NavigationLink,
    PageContent,
    PageUpdatePayload,
    PlanAdminRead,
    StripeConfig,
    StripeConfigUpdatePayload,
)
from app.services.api_keys import generate_api_key
from app.services.app_settings import AppSettingsService
from app.services.page_service import PageService
from app.services.stripe_billing import StripeBillingService, StripeConfigurationError

router = APIRouter()

NAVIGATION_LINKS: list[NavigationLink] = [
    NavigationLink(label="Home", path="/"),
    NavigationLink(label="Dashboard", path="/dashboard"),
    NavigationLink(label="Notas", path="/invoices"),
    NavigationLink(label="Auditorias", path="/audits"),
    NavigationLink(label="Planos", path="/billing"),
    NavigationLink(label="Regras", path="/rules"),
    NavigationLink(label="Administração", path="/admin"),
    NavigationLink(label="Administração de Usuários", path="/admin/users"),
    NavigationLink(label="Administração de Planos", path="/admin/plans"),
    NavigationLink(label="Configurações Stripe", path="/admin/stripe"),
    NavigationLink(label="Portal de Cobranças", path="/admin/billing"),
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


def _serialize_admin_user(user: User) -> AdminUserRead:
    organizations = [
        role.organization.name
        for role in user.roles
        if getattr(role, "organization", None)
    ]
    full_name = " ".join(
        part for part in [user.first_name or "", user.last_name or ""] if part
    )
    return AdminUserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=full_name or user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        organizations=organizations,
    )


@router.get("/users", response_model=List[AdminUserRead])
def list_users(
    db: Session = Depends(get_db_session),
    _: None = Depends(get_current_superuser),
) -> list[AdminUserRead]:
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [_serialize_admin_user(user) for user in users]


@router.put("/users/{user_id}", response_model=AdminUserRead)
def update_user(
    user_id: int,
    payload: AdminUserUpdatePayload,
    db: Session = Depends(get_db_session),
    _: None = Depends(get_current_superuser),
) -> AdminUserRead:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    user.is_active = payload.is_active
    user.is_superuser = payload.is_superuser
    db.add(user)
    db.commit()
    db.refresh(user)
    return _serialize_admin_user(user)


@router.get("/plans", response_model=List[PlanAdminRead])
def list_plans(
    db: Session = Depends(get_db_session),
    _: None = Depends(get_current_superuser),
) -> list[PlanAdminRead]:
    plans = db.query(Plan).order_by(Plan.monthly_price_cents).all()
    return [
        PlanAdminRead(
            id=plan.id,
            code=plan.code,
            name=plan.name,
            monthly_price_cents=plan.monthly_price_cents,
            features=plan.features or {},
            limits=plan.limits or {},
            stripe_product_id=plan.stripe_product_id,
            stripe_price_id=plan.stripe_price_id,
        )
        for plan in plans
    ]


@router.post("/plans/sync", response_model=ActionMessage)
def sync_plans(
    db: Session = Depends(get_db_session),
    _: None = Depends(get_current_superuser),
) -> ActionMessage:
    try:
        service = StripeBillingService(db)
        service.sync_plan_catalog()
        db.commit()
        return ActionMessage(message="Catálogo sincronizado com sucesso.")
    except StripeConfigurationError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/stripe/config", response_model=StripeConfig)
def get_stripe_config(
    db: Session = Depends(get_db_session),
    _: None = Depends(get_current_superuser),
) -> StripeConfig:
    service = AppSettingsService(db)
    stored = service.get_many(
        ["stripe_public_key", "stripe_secret_key", "stripe_webhook_secret"]
    )
    return StripeConfig(
        public_key=stored.get("stripe_public_key") or settings.stripe_public_key,
        secret_key=stored.get("stripe_secret_key") or settings.stripe_secret_key,
        webhook_secret=stored.get("stripe_webhook_secret") or settings.stripe_webhook_secret,
    )


@router.put("/stripe/config", response_model=StripeConfig)
def update_stripe_config(
    payload: StripeConfigUpdatePayload,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_superuser),
) -> StripeConfig:
    service = AppSettingsService(db)

    def _normalize(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    updates = {
        "stripe_public_key": _normalize(payload.public_key),
        "stripe_secret_key": _normalize(payload.secret_key),
        "stripe_webhook_secret": _normalize(payload.webhook_secret),
    }
    for key, value in updates.items():
        if value is None:
            service.delete(key)
        else:
            service.set(key, value, user_id=current_user.id)
    db.commit()
    stored = service.get_many(
        ["stripe_public_key", "stripe_secret_key", "stripe_webhook_secret"]
    )
    return StripeConfig(
        public_key=stored.get("stripe_public_key") or settings.stripe_public_key,
        secret_key=stored.get("stripe_secret_key") or settings.stripe_secret_key,
        webhook_secret=stored.get("stripe_webhook_secret")
        or settings.stripe_webhook_secret,
    )


@router.get("/organizations", response_model=List[AdminOrganizationSummary])
def list_organizations(
    db: Session = Depends(get_db_session),
    _: None = Depends(get_current_superuser),
) -> list[AdminOrganizationSummary]:
    orgs = db.query(Organization).order_by(Organization.name).all()
    return [
        AdminOrganizationSummary(id=org.id, name=org.name, slug=org.slug)
        for org in orgs
    ]
