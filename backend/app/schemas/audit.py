from datetime import datetime

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


class AuditRunRead(OraculoBaseModel):
    id: int
    status: str
    summary: dict
    findings: list[AuditFindingRead] = []
