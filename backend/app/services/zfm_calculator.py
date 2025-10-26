from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun, AuditStatus
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.services.rules_engine import RuleEngine
from app.services.ruleset_service import RuleSetService


class RuleAuditCalculator:
    """Executa regras DSL para gerar achados de auditoria."""

    def __init__(self, session: Session, org_id: int) -> None:
        self.session = session
        self.org_id = org_id
        self.rulesets = RuleSetService(session)
        self.composed = self.rulesets.compose_for_org(org_id)
        self.engine = RuleEngine(self.composed.rules)

    def bind_to_run(self, audit_run: AuditRun) -> None:
        target_ruleset = self.composed.override or self.composed.baseline
        audit_run.ruleset_id = target_ruleset.id
        summary = dict(audit_run.summary or {})
        metadata = dict(summary.get("metadata") or {})
        metadata["rules"] = self.composed.metadata["sources"]
        summary["metadata"] = metadata
        audit_run.summary = summary

    def persist_results(
        self,
        *,
        audit_run: AuditRun,
        invoice: Invoice,
        items: Iterable[InvoiceItem] | None = None,
    ) -> list[AuditFinding]:
        audit_run.started_at = audit_run.started_at or datetime.utcnow()
        audit_run.status = AuditStatus.RUNNING
        self.session.flush()

        self.session.execute(
            delete(AuditFinding).where(
                AuditFinding.audit_run_id == audit_run.id,
                AuditFinding.invoice_id == invoice.id,
            )
        )
        self.session.flush()

        results = self.engine.evaluate(invoice=invoice, items=items or invoice.items)
        findings: list[AuditFinding] = []
        for result in results:
            finding = AuditFinding(
                audit_run_id=audit_run.id,
                invoice_id=invoice.id,
                item_id=result.item.id if result.item else None,
                rule_id=result.rule_id,
                inconsistency_code=result.inconsistency_code,
                severity=result.severity,
                message_pt=result.message_pt,
                suggestion_code=result.suggestion_code,
                references=list(result.references) if result.references else None,
                evidence=result.evidence or {},
            )
            self.session.add(finding)
            findings.append(finding)

        self.session.flush()
        return findings


# Compatibilidade com código existente
ZFMAuditCalculator = RuleAuditCalculator
