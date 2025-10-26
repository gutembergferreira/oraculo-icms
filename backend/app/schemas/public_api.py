from __future__ import annotations

from datetime import date, datetime

from app.schemas.base import OraculoBaseModel


class PublicInvoiceSummary(OraculoBaseModel):
    total_invoices: int
    total_amount: float
    last_issue_date: date | None
    generated_at: datetime


class PublicAuditSnapshot(OraculoBaseModel):
    audit_id: int | None
    status: str | None
    requested_at: datetime | None
    finished_at: datetime | None
    findings: int | None
