from datetime import datetime

from typing import Any

from pydantic import Field

from app.schemas.base import OraculoBaseModel


class AuditRunCreate(OraculoBaseModel):
    date_start: datetime
    date_end: datetime
    ruleset_version: str | None = None


class AuditFindingRead(OraculoBaseModel):
    id: int
    rule_id: str
    inconsistency_code: str
    severity: str
    message_pt: str
    suggestion_code: str | None


class AuditTopRule(OraculoBaseModel):
    rule_id: str
    inconsistency_code: str
    severity: str
    message_pt: str
    count: int


class AuditSummary(OraculoBaseModel):
    processed_invoices: int = 0
    total_findings: int = 0
    invoices_with_findings: int = 0
    severity_breakdown: dict[str, int] = Field(default_factory=dict)
    top_rules: list[AuditTopRule] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditRunRead(OraculoBaseModel):
    id: int
    status: str
    summary: AuditSummary
    findings: list[AuditFindingRead] = []


class AuditBaselineSummary(AuditSummary):
    audit_run_id: int
