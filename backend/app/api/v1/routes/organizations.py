from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.organization import Organization
from app.models.user import User
from app.models.user_org_role import UserOrgRole
from app.schemas import OrganizationRead

router = APIRouter()


@router.get("/me/organizations", response_model=List[OrganizationRead])
def list_user_orgs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[Organization]:
    org_ids = [role.org_id for role in current_user.roles]
    return db.query(Organization).filter(Organization.id.in_(org_ids)).all()


@router.get("/{org_id}/users")
def list_org_users(org_id: int, db: Session = Depends(get_db_session)) -> list[dict]:
    roles = db.query(UserOrgRole).filter(UserOrgRole.org_id == org_id).all()
    result = []
    for role in roles:
        if role.user:
            result.append({
                "user_id": role.user.id,
                "email": role.user.email,
                "role": role.role,
            })
    return result
