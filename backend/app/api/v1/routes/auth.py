from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.core.config import settings
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.organization import Organization
from app.models.org_setting import OrgSetting
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.user import User
from app.models.user_org_role import UserOrgRole
from app.schemas import (
    SSOCallbackPayload,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.services.sso import SSOClient, SSOConfigurationError

router = APIRouter()


def _serialize_user(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/providers")
def list_providers() -> dict:
    providers = [
        {"type": "password", "name": "E-mail e senha"},
    ]
    if settings.sso_enabled:
        providers.append(
            {
                "type": "sso",
                "name": settings.sso_provider_name or "SSO",
            }
        )
    return {"providers": providers}


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    return _serialize_user(current_user)


@router.post("/register", response_model=UserRead)
def register_user(payload: UserCreate, db: Session = Depends(get_db_session)) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já utilizado")

    user = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.flush()

    if payload.organization_name:
        org = Organization(
            name=payload.organization_name,
            slug=payload.organization_name.lower().replace(" ", "-"),
            cnpj="00000000000000",
        )
        db.add(org)
        db.flush()

        free_plan = db.query(Plan).filter(Plan.code == "FREE").first()
        if free_plan:
            subscription = Subscription(
                organization=org,
                plan=free_plan,
                status="active",
            )
            db.add(subscription)
            db.add(
                OrgSetting(
                    org_id=org.id,
                    current_plan_id=free_plan.id,
                    billing_email=payload.email,
                    plan_limits=free_plan.limits or {},
                    plan_features=free_plan.features or {},
                    flags={
                        **{k: bool(v) for k, v in (free_plan.features or {}).items()},
                        "plan_code": free_plan.code,
                    },
                )
            )
        db.add(UserOrgRole(user_id=user.id, org_id=org.id, role="admin_empresa"))

    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db_session)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(token: str) -> TokenResponse:
    try:
        payload = decode_token(token, token_type="refresh")
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc

    subject = str(payload["sub"])
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.get("/sso/authorize")
def sso_authorize(state: str) -> dict:
    if not settings.sso_enabled:
        raise HTTPException(status_code=404, detail="SSO desabilitado")
    try:
        client = SSOClient()
    except SSOConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"url": client.build_authorization_url(state)}


@router.post("/sso/callback", response_model=TokenResponse)
def sso_callback(
    payload: SSOCallbackPayload,
    db: Session = Depends(get_db_session),
) -> TokenResponse:
    if not settings.sso_enabled:
        raise HTTPException(status_code=404, detail="SSO desabilitado")
    try:
        client = SSOClient()
    except SSOConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    token_response = client.exchange_code(payload.code)
    access_token = token_response.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Resposta do SSO sem access_token")
    userinfo = client.fetch_userinfo(access_token)
    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Usuário SSO sem e-mail")

    first_name = userinfo.get("given_name") or userinfo.get("name") or "Usuário"
    last_name = userinfo.get("family_name") or userinfo.get("preferred_username") or "SSO"

    user = db.query(User).filter(User.email == email).one_or_none()
    if not user:
        user = User(
            email=email,
            first_name=str(first_name)[:100],
            last_name=str(last_name)[:100],
            password_hash=get_password_hash(secrets.token_urlsafe(16)),
            is_active=True,
        )
        db.add(user)
        db.flush()

    db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
