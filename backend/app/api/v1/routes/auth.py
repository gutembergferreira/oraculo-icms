from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
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
from app.schemas import TokenResponse, UserCreate, UserRead

router = APIRouter()


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
def login(email: str, password: str, db: Session = Depends(get_db_session)) -> TokenResponse:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
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
