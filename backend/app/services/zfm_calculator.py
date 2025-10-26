from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Sequence

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun, AuditStatus
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem


@dataclass(slots=True)
class FindingResult:
    rule_id: str
    inconsistency_code: str
    severity: str
    message_pt: str
    suggestion_code: str | None = None
    references: Sequence[str] | None = None
    item: InvoiceItem | None = None
    evidence: dict[str, Any] | None = None


class ZFMAuditCalculator:
    """Motor simplificado inspirado no zfm-calculator para validações fiscais."""

    def __init__(
        self,
        *,
        cfop_requires_st: Sequence[str] | None = None,
        ncm_requires_cest: Sequence[str] | None = None,
    ) -> None:
        self.cfop_requires_st = tuple(cfop_requires_st or ['6101', '6102', '6201', '6202'])
        self.ncm_requires_cest = tuple(ncm_requires_cest or ['22030000', '33030010'])

    # ------------------------------------------------------------------
    def evaluate_invoice(self, invoice: Invoice, items: Iterable[InvoiceItem] | None = None) -> list[FindingResult]:
        invoice_items = list(items if items is not None else invoice.items)
        results: list[FindingResult] = []

        total_items = sum(float(item.total_value or 0) for item in invoice_items)
        freight_value = float(invoice.freight_value or 0)
        invoice_total = float(invoice.total_value or 0)
        if abs((total_items + freight_value) - invoice_total) > 0.1:
            results.append(
                FindingResult(
                    rule_id='zfm_total_mismatch',
                    inconsistency_code='TOTAL_DIVERGENTE',
                    severity='alto',
                    message_pt='Valor total da nota difere da soma de itens e frete.',
                    evidence={
                        'soma_itens': round(total_items, 2),
                        'frete': round(freight_value, 2),
                        'total_xml': round(invoice_total, 2),
                    },
                )
            )

        for item in invoice_items:
            if item.cfop and any(item.cfop.startswith(prefix) for prefix in self.cfop_requires_st):
                if not invoice.has_st and (item.icms_st_value or 0) == 0:
                    results.append(
                        FindingResult(
                            rule_id='zfm_st_missing',
                            inconsistency_code='ST_NAO_RECOLHIDO',
                            severity='medio',
                            message_pt='Item com CFOP interestadual sem destaque de ST.',
                            suggestion_code='REGULARIZAR_ST',
                            references=['LC 24/75', 'Convênio ICMS 65/88'],
                            item=item,
                            evidence={
                                'cfop': item.cfop,
                                'cst': item.cst,
                                'valor_icms_st': float(item.icms_st_value or 0),
                            },
                        )
                    )
            if item.ncm and item.ncm in self.ncm_requires_cest and not item.cest:
                results.append(
                    FindingResult(
                        rule_id='zfm_missing_cest',
                        inconsistency_code='CEST_OBRIGATORIO',
                        severity='baixo',
                        message_pt='Item com NCM sujeito a CEST porém sem informação no XML.',
                        suggestion_code='INFORMAR_CEST',
                        references=['Convênio ICMS 60/07'],
                        item=item,
                        evidence={'ncm': item.ncm},
                    )
                )
        return results

    # ------------------------------------------------------------------
    def persist_results(
        self,
        *,
        session: Session,
        audit_run: AuditRun,
        invoice: Invoice,
        items: Iterable[InvoiceItem] | None = None,
    ) -> list[AuditFinding]:
        audit_run.started_at = audit_run.started_at or datetime.utcnow()
        audit_run.status = AuditStatus.RUNNING
        session.flush()

        session.execute(
            delete(AuditFinding).where(
                AuditFinding.audit_run_id == audit_run.id,
                AuditFinding.invoice_id == invoice.id,
            )
        )
        session.flush()

        results = self.evaluate_invoice(invoice, items)
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
            session.add(finding)
            findings.append(finding)

        audit_run.summary = {
            'invoice_id': invoice.id,
            'total_findings': len(findings),
            'rules': [result.rule_id for result in results],
        }
        audit_run.status = AuditStatus.DONE
        audit_run.finished_at = datetime.utcnow()
        session.flush()
        return findings
