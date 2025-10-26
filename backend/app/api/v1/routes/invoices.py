from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db_session
from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceDetailRead, InvoiceSummaryRead

router = APIRouter()


@router.get('/{org_id}/invoices', response_model=List[InvoiceSummaryRead])
def list_invoices(
    org_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[InvoiceSummaryRead]:
    findings_subquery = (
        db.query(
            AuditFinding.invoice_id.label('invoice_id'),
            func.count(AuditFinding.id).label('findings_count'),
        )
        .join(AuditRun, AuditRun.id == AuditFinding.audit_run_id)
        .filter(AuditRun.org_id == org_id)
        .group_by(AuditFinding.invoice_id)
        .subquery()
    )

    rows = (
        db.query(Invoice, func.coalesce(findings_subquery.c.findings_count, 0))
        .outerjoin(findings_subquery, findings_subquery.c.invoice_id == Invoice.id)
        .filter(Invoice.org_id == org_id)
        .order_by(Invoice.issue_date.desc())
        .limit(100)
        .all()
    )

    summaries: list[InvoiceSummaryRead] = []
    for invoice, findings_count in rows:
        summaries.append(
            InvoiceSummaryRead(
                id=invoice.id,
                access_key=invoice.access_key,
                emitente_cnpj=invoice.emitente_cnpj,
                destinatario_cnpj=invoice.destinatario_cnpj,
                uf=invoice.uf,
                issue_date=invoice.issue_date,
                total_value=float(invoice.total_value or 0),
                freight_value=float(invoice.freight_value) if invoice.freight_value is not None else None,
                has_st=invoice.has_st,
                findings_count=int(findings_count or 0),
            )
        )
    return summaries


@router.get('/{org_id}/invoices/{invoice_id}', response_model=InvoiceDetailRead)
def get_invoice(
    org_id: int,
    invoice_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> InvoiceDetailRead:
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.org_id == org_id)
        .options(selectinload(Invoice.items))
        .one_or_none()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail='Nota não encontrada.')

    latest_run_id = (
        db.query(AuditRun.id)
        .join(AuditFinding, AuditFinding.audit_run_id == AuditRun.id)
        .filter(AuditRun.org_id == org_id, AuditFinding.invoice_id == invoice_id)
        .order_by(AuditRun.finished_at.desc().nullslast(), AuditRun.id.desc())
        .limit(1)
        .scalar()
    )

    findings: list[AuditFinding] = []
    if latest_run_id:
        findings = (
            db.query(AuditFinding)
            .filter(
                AuditFinding.audit_run_id == latest_run_id,
                AuditFinding.invoice_id == invoice_id,
            )
            .order_by(AuditFinding.severity.desc())
            .all()
        )

    return InvoiceDetailRead(
        id=invoice.id,
        access_key=invoice.access_key,
        emitente_cnpj=invoice.emitente_cnpj,
        destinatario_cnpj=invoice.destinatario_cnpj,
        uf=invoice.uf,
        issue_date=invoice.issue_date,
        total_value=float(invoice.total_value or 0),
        freight_value=float(invoice.freight_value) if invoice.freight_value is not None else None,
        has_st=invoice.has_st,
        findings_count=len(findings),
        items=invoice.items,
        findings=findings,
    )
