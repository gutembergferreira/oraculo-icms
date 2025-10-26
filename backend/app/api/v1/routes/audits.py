from typing import List

from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun, AuditStatus
from app.schemas import (
    AuditBaselineSummary,
    AuditFindingRead,
    AuditRunCreate,
    AuditRunRead,
)
from app.services.audit_report import AuditReportBuilder
from app.services.audit_summary import initialize_summary
from app.workers.tasks import run_audit as run_audit_task

router = APIRouter()


@router.post("/{org_id}/audits/run", response_model=AuditRunRead)
def run_audit(
    org_id: int,
    payload: AuditRunCreate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> AuditRun:
    metadata = {
        "range": [payload.date_start.isoformat(), payload.date_end.isoformat()],
        "trigger": "manual",
    }
    audit = AuditRun(
        org_id=org_id,
        requested_by=current_user.id,
        status=AuditStatus.PENDING,
        summary=initialize_summary(metadata),
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    run_audit_task(audit.id)
    db.refresh(audit)
    return audit


@router.get("/{org_id}/audits", response_model=List[AuditRunRead])
def list_audits(org_id: int, db: Session = Depends(get_db_session)) -> list[AuditRun]:
    return db.query(AuditRun).filter(AuditRun.org_id == org_id).all()


@router.get("/{org_id}/audits/baseline/summary", response_model=AuditBaselineSummary)
def get_baseline_summary(
    org_id: int,
    db: Session = Depends(get_db_session),
) -> AuditBaselineSummary:
    audit = (
        db.query(AuditRun)
        .filter(AuditRun.org_id == org_id, AuditRun.status == AuditStatus.DONE)
        .order_by(AuditRun.finished_at.desc().nullslast(), AuditRun.id.desc())
        .first()
    )
    if not audit:
        raise HTTPException(status_code=404, detail="Nenhuma auditoria concluída para esta organização.")

    summary = audit.summary or initialize_summary()
    return AuditBaselineSummary(audit_run_id=audit.id, **summary)


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


@router.get("/{org_id}/audits/{audit_id}/reports/pdf")
def download_audit_pdf(
    org_id: int,
    audit_id: int,
    request: Request,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    audit = db.get(AuditRun, audit_id)
    if not audit or audit.org_id != org_id:
        raise HTTPException(status_code=404, detail="Auditoria não encontrada")
    if audit.status != AuditStatus.DONE:
        raise HTTPException(status_code=400, detail="Auditoria ainda não concluída")

    builder = AuditReportBuilder(db)
    pdf_bytes = builder.generate_pdf(audit)
    builder.register_download(
        audit_run=audit,
        user=current_user,
        file_format="pdf",
        request_ip=request.client.host if request.client else None,
    )
    db.commit()

    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)
    headers = {"Content-Disposition": f"attachment; filename=audit-{audit.id}.pdf"}
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)


@router.get("/{org_id}/audits/{audit_id}/reports/xlsx")
def download_audit_xlsx(
    org_id: int,
    audit_id: int,
    request: Request,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    audit = db.get(AuditRun, audit_id)
    if not audit or audit.org_id != org_id:
        raise HTTPException(status_code=404, detail="Auditoria não encontrada")
    if audit.status != AuditStatus.DONE:
        raise HTTPException(status_code=400, detail="Auditoria ainda não concluída")

    builder = AuditReportBuilder(db)
    xlsx_bytes = builder.generate_xlsx(audit)
    builder.register_download(
        audit_run=audit,
        user=current_user,
        file_format="xlsx",
        request_ip=request.client.host if request.client else None,
    )
    db.commit()

    buffer = BytesIO(xlsx_bytes)
    buffer.seek(0)
    headers = {
        "Content-Disposition": f"attachment; filename=audit-{audit.id}.xlsx",
    }
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
