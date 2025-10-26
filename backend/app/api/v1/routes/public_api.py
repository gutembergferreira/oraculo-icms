from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_active_api_key, get_db_session
from app.models.api_key import ApiKey
from app.models.audit_run import AuditRun
from app.models.invoice import Invoice
from app.schemas import PageContent, PublicAuditSnapshot, PublicInvoiceSummary
from app.services.page_service import PageService

router = APIRouter()


@router.get("/organizations/{org_id}/invoices/summary", response_model=PublicInvoiceSummary)
def get_invoice_summary(
    org_id: int,
    db: Session = Depends(get_db_session),
    api_key: ApiKey = Depends(get_active_api_key),
) -> PublicInvoiceSummary:
    if api_key.org_id != org_id:
        raise HTTPException(status_code=403, detail="API key não vinculada à organização")
    total_invoices, total_amount, last_issue = db.query(
        func.count(Invoice.id),
        func.coalesce(func.sum(Invoice.total_value), 0),
        func.max(Invoice.issue_date),
    ).filter(Invoice.org_id == org_id).one()

    return PublicInvoiceSummary(
        total_invoices=total_invoices,
        total_amount=float(total_amount or 0),
        last_issue_date=last_issue,
        generated_at=datetime.utcnow(),
    )


@router.get("/organizations/{org_id}/audits/latest", response_model=PublicAuditSnapshot)
def get_latest_audit(
    org_id: int,
    db: Session = Depends(get_db_session),
    api_key: ApiKey = Depends(get_active_api_key),
) -> PublicAuditSnapshot:
    if api_key.org_id != org_id:
        raise HTTPException(status_code=403, detail="API key não vinculada à organização")
    audit = (
        db.query(AuditRun)
        .filter(AuditRun.org_id == org_id)
        .order_by(AuditRun.created_at.desc())
        .first()
    )
    if not audit:
        return PublicAuditSnapshot(
            audit_id=None,
            status=None,
            requested_at=None,
            finished_at=None,
            findings=None,
        )

    findings = None
    if audit.summary:
        metadata = audit.summary or {}
        findings = metadata.get("total_findings")

    return PublicAuditSnapshot(
        audit_id=audit.id,
        status=audit.status.value if hasattr(audit.status, "value") else str(audit.status),
        requested_at=audit.created_at,
        finished_at=audit.finished_at,
        findings=findings,
    )


@router.get("/content/home", response_model=PageContent)
def get_public_home(db: Session = Depends(get_db_session)) -> PageContent:
    service = PageService(db)
    page = service.get_or_create(
        "home",
        default_title="Oráculo ICMS",
        default_content="Centralize a gestão tributária da sua empresa com automações e auditorias em tempo real.",
    )
    db.commit()
    return PageContent(
        slug=page.slug,
        title=page.title,
        content=page.content,
        updated_at=page.updated_at,
    )
