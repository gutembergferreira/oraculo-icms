from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun


SUMMARY_FIELDS = {
    "processed_invoices",
    "total_findings",
    "invoices_with_findings",
    "severity_breakdown",
    "top_rules",
    "metadata",
}


def initialize_summary(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a base summary structure with sane defaults."""

    return {
        "processed_invoices": 0,
        "total_findings": 0,
        "invoices_with_findings": 0,
        "severity_breakdown": {},
        "top_rules": [],
        "metadata": metadata or {},
    }


class AuditSummaryBuilder:
    """Aggregate persisted findings into a consolidated summary."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    def build(
        self,
        audit_run: AuditRun,
        *,
        processed_invoices: int,
        existing_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        summary = initialize_summary()
        summary["processed_invoices"] = processed_invoices

        metadata: Dict[str, Any] = {}
        if existing_summary:
            # Preserve previously stored metadata (legacy keys become metadata entries).
            metadata.update(existing_summary.get("metadata") or {})
            for key, value in existing_summary.items():
                if key not in SUMMARY_FIELDS:
                    metadata[key] = value

        total_findings = (
            self.session.query(func.count(AuditFinding.id))
            .filter(AuditFinding.audit_run_id == audit_run.id)
            .scalar()
        ) or 0
        summary["total_findings"] = int(total_findings)

        invoices_with_findings = (
            self.session.query(func.count(func.distinct(AuditFinding.invoice_id)))
            .filter(AuditFinding.audit_run_id == audit_run.id)
            .scalar()
        ) or 0
        summary["invoices_with_findings"] = int(invoices_with_findings)

        severity_rows = (
            self.session.query(
                AuditFinding.severity,
                func.count(AuditFinding.id).label("count"),
            )
            .filter(AuditFinding.audit_run_id == audit_run.id)
            .group_by(AuditFinding.severity)
            .all()
        )
        summary["severity_breakdown"] = {
            row.severity: int(row.count) for row in severity_rows if row.severity
        }

        top_rule_rows = (
            self.session.query(
                AuditFinding.rule_id,
                AuditFinding.inconsistency_code,
                AuditFinding.severity,
                AuditFinding.message_pt,
                func.count(AuditFinding.id).label("count"),
            )
            .filter(AuditFinding.audit_run_id == audit_run.id)
            .group_by(
                AuditFinding.rule_id,
                AuditFinding.inconsistency_code,
                AuditFinding.severity,
                AuditFinding.message_pt,
            )
            .order_by(func.count(AuditFinding.id).desc())
            .limit(5)
            .all()
        )
        summary["top_rules"] = [
            {
                "rule_id": row.rule_id,
                "inconsistency_code": row.inconsistency_code,
                "severity": row.severity,
                "message_pt": row.message_pt,
                "count": int(row.count),
            }
            for row in top_rule_rows
        ]

        summary["metadata"] = metadata
        return summary
