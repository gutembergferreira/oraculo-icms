from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from sqlalchemy.orm import Session
from weasyprint import HTML

from app.core.config import settings
from app.models.audit_finding import AuditFinding
from app.models.audit_log import AuditLog
from app.models.audit_run import AuditRun
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.user import User
from app.services.audit_summary import initialize_summary


@dataclass(slots=True)
class AuditReportContext:
    audit_run: AuditRun
    summary: dict[str, Any]
    findings: list[dict[str, Any]]


class AuditReportBuilder:
    """Generate PDF/XLSX reports with the latest audit findings."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    def build_context(self, audit_run: AuditRun) -> AuditReportContext:
        summary = audit_run.summary or initialize_summary()
        findings = (
            self.session.query(
                AuditFinding.id,
                AuditFinding.rule_id,
                AuditFinding.inconsistency_code,
                AuditFinding.severity,
                AuditFinding.message_pt,
                AuditFinding.suggestion_code,
                Invoice.access_key,
                Invoice.issue_date,
                Invoice.emitente_cnpj,
                Invoice.destinatario_cnpj,
                InvoiceItem.description,
            )
            .join(Invoice, Invoice.id == AuditFinding.invoice_id)
            .outerjoin(InvoiceItem, InvoiceItem.id == AuditFinding.item_id)
            .filter(AuditFinding.audit_run_id == audit_run.id)
            .order_by(AuditFinding.severity.desc(), AuditFinding.id)
            .all()
        )

        finding_dicts: list[dict[str, Any]] = []
        for row in findings:
            finding_dicts.append(
                {
                    "id": row.id,
                    "rule_id": row.rule_id,
                    "inconsistency_code": row.inconsistency_code,
                    "severity": row.severity,
                    "message_pt": row.message_pt,
                    "suggestion_code": row.suggestion_code,
                    "access_key": row.access_key,
                    "issue_date": row.issue_date,
                    "emitente_cnpj": row.emitente_cnpj,
                    "destinatario_cnpj": row.destinatario_cnpj,
                    "item_description": row.description,
                }
            )

        return AuditReportContext(audit_run=audit_run, summary=summary, findings=finding_dicts)

    # ------------------------------------------------------------------
    def generate_pdf(self, audit_run: AuditRun) -> bytes:
        context = self.build_context(audit_run)
        summary = context.summary

        metadata = summary.get("metadata", {})
        header_html = f"""
        <h1>Auditoria #{audit_run.id}</h1>
        <p>Organização: {html.escape(str(audit_run.org_id))}</p>
        <p>Período: {html.escape(str(metadata.get('range', 'N/D')))}</p>
        <p>Processadas: {summary.get('processed_invoices', 0)} · Achados: {summary.get('total_findings', 0)}</p>
        """

        severity_rows = "".join(
            f"<li><strong>{html.escape(severity.upper())}</strong>: {count}</li>"
            for severity, count in summary.get("severity_breakdown", {}).items()
        )

        top_rules_rows = "".join(
            """
            <tr>
                <td>{rule['rule_id']}</td>
                <td>{html.escape(rule['inconsistency_code'])}</td>
                <td>{html.escape(rule['severity'])}</td>
                <td>{html.escape(rule['message_pt'])}</td>
                <td>{rule['count']}</td>
            </tr>
            """
            for rule in summary.get("top_rules", [])
        )

        findings_rows = "".join(
            """
            <tr>
                <td>{finding['id']}</td>
                <td>{finding['access_key']}</td>
                <td>{finding['severity']}</td>
                <td>{html.escape(finding['inconsistency_code'])}</td>
                <td>{html.escape(finding['message_pt'])}</td>
                <td>{html.escape(finding.get('item_description') or '-')}</td>
            </tr>
            """
            for finding in context.findings
        )

        html_string = f"""
        <html>
            <head>
                <meta charset='utf-8' />
                <style>
                    body {{ font-family: sans-serif; margin: 24px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
                    th, td {{ border: 1px solid #ccc; padding: 6px 8px; font-size: 12px; }}
                    th {{ background: #f3f4f6; text-align: left; }}
                    h2 {{ margin-top: 24px; }}
                </style>
            </head>
            <body>
                {header_html}
                <h2>Gravidade</h2>
                <ul>{severity_rows or '<li>Sem achados registrados.</li>'}</ul>
                <h2>Top regras</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Inconsistência</th>
                            <th>Gravidade</th>
                            <th>Mensagem</th>
                            <th>Ocorrências</th>
                        </tr>
                    </thead>
                    <tbody>
                        {top_rules_rows or '<tr><td colspan="5">Sem recorrência identificada.</td></tr>'}
                    </tbody>
                </table>
                <h2>Achados</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Chave de acesso</th>
                            <th>Gravidade</th>
                            <th>Código</th>
                            <th>Mensagem</th>
                            <th>Item</th>
                        </tr>
                    </thead>
                    <tbody>
                        {findings_rows or '<tr><td colspan="6">Nenhum achado cadastrado.</td></tr>'}
                    </tbody>
                </table>
            </body>
        </html>
        """

        return HTML(string=html_string).write_pdf()

    # ------------------------------------------------------------------
    def generate_xlsx(self, audit_run: AuditRun) -> bytes:
        context = self.build_context(audit_run)
        summary = context.summary

        workbook = Workbook()
        summary_sheet = workbook.active
        summary_sheet.title = "Resumo"
        summary_sheet.append(["Métrica", "Valor"])
        summary_sheet.append(["Notas processadas", summary.get("processed_invoices", 0)])
        summary_sheet.append(["Notas com achados", summary.get("invoices_with_findings", 0)])
        summary_sheet.append(["Total de achados", summary.get("total_findings", 0)])

        summary_sheet.append([])
        summary_sheet.append(["Gravidade", "Ocorrências"])
        for severity, count in summary.get("severity_breakdown", {}).items():
            summary_sheet.append([severity, count])

        summary_sheet.append([])
        summary_sheet.append(["Regra", "Código", "Gravidade", "Mensagem", "Ocorrências"])
        for rule in summary.get("top_rules", []):
            summary_sheet.append(
                [
                    rule["rule_id"],
                    rule["inconsistency_code"],
                    rule["severity"],
                    rule["message_pt"],
                    rule["count"],
                ]
            )

        findings_sheet = workbook.create_sheet("Achados")
        findings_sheet.append(
            [
                "ID",
                "Chave",
                "Emitente",
                "Destinatário",
                "Data",
                "Código",
                "Mensagem",
                "Gravidade",
                "Item",
                "Sugestão",
            ]
        )
        for finding in context.findings:
            findings_sheet.append(
                [
                    finding["id"],
                    finding["access_key"],
                    finding["emitente_cnpj"],
                    finding["destinatario_cnpj"],
                    finding["issue_date"].strftime("%Y-%m-%d") if isinstance(finding["issue_date"], datetime) else finding["issue_date"],
                    finding["inconsistency_code"],
                    finding["message_pt"],
                    finding["severity"],
                    finding.get("item_description"),
                    finding.get("suggestion_code"),
                ]
            )

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    # ------------------------------------------------------------------
    def register_download(
        self,
        *,
        audit_run: AuditRun,
        user: User | None,
        file_format: str,
        request_ip: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            org_id=audit_run.org_id,
            user_id=user.id if user else None,
            action="download_report",
            entity="audit_run",
            entity_id=str(audit_run.id),
            ip=request_ip,
            meta={
                "format": file_format,
                "generated_at": datetime.utcnow().isoformat(),
                "storage_backend": settings.storage_backend,
            },
        )
        self.session.add(log)
        return log
