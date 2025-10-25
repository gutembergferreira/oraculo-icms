from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.models.plan import Plan
from app.schemas import PlanPublic

router = APIRouter()


@router.get("/plans", response_model=List[PlanPublic])
def list_plans(db: Session = Depends(get_db_session)) -> list[Plan]:
    return db.query(Plan).order_by(Plan.monthly_price_cents).all()
