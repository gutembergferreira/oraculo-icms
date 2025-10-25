from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun, AuditStatus
from app.schemas import AuditFindingRead, AuditRunCreate, AuditRunRead

router = APIRouter()


@router.post("/{org_id}/audits/run", response_model=AuditRunRead)
def run_audit(
    org_id: int,
    payload: AuditRunCreate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> AuditRun:
    audit = AuditRun(
        org_id=org_id,
        requested_by=current_user.id,
        status=AuditStatus.PENDING,
        summary={"status": "em processamento", "range": [payload.date_start.isoformat(), payload.date_end.isoformat()]},
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


@router.get("/{org_id}/audits", response_model=List[AuditRunRead])
def list_audits(org_id: int, db: Session = Depends(get_db_session)) -> list[AuditRun]:
    return db.query(AuditRun).filter(AuditRun.org_id == org_id).all()


@router.get("/{org_id}/audits/{audit_id}", response_model=AuditRunRead)
def get_audit(org_id: int, audit_id: int, db: Session = Depends(get_db_session)) -> AuditRun:
    audit = db.get(AuditRun, audit_id)
    if not audit or audit.org_id != org_id:
        raise HTTPException(status_code=404, detail="Auditoria não encontrada")
    return audit


@router.get("/{org_id}/audits/{audit_id}/findings", response_model=List[AuditFindingRead])
def list_findings(org_id: int, audit_id: int, db: Session = Depends(get_db_session)) -> list[AuditFinding]:
    return (
        db.query(AuditFinding)
        .join(AuditRun)
        .filter(AuditFinding.audit_run_id == audit_id, AuditRun.org_id == org_id)
        .all()
    )
