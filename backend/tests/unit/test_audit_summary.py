from datetime import date

from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun, AuditStatus
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.services.audit_summary import AuditSummaryBuilder, initialize_summary


def test_audit_summary_builder_preserves_metadata(session, seed_data):
    user, org = seed_data

    invoice = Invoice(
        org_id=org.id,
        access_key="12345678901234567890123456789012345678901234",
        emitente_cnpj="12345678000199",
        destinatario_cnpj="99887766000155",
        uf="AM",
        issue_date=date(2024, 1, 1),
        total_value=100.0,
        freight_value=10.0,
        has_st=False,
    )
    session.add(invoice)
    session.flush()

    item = InvoiceItem(
        invoice_id=invoice.id,
        seq=1,
        product_code="001",
        description="Produto teste",
        ncm="22030000",
        cest=None,
        cfop="6101",
        cst="00",
        quantity=1,
        unit_value=90.0,
        total_value=90.0,
        freight_alloc=10.0,
        discount=None,
        bc_icms=None,
        icms_value=None,
        bc_st=None,
        icms_st_value=None,
        other_taxes={},
    )
    session.add(item)
    session.flush()

    audit_run = AuditRun(
        org_id=org.id,
        requested_by=user.id,
        status=AuditStatus.DONE,
        summary=initialize_summary({"source": "unit"}),
    )
    session.add(audit_run)
    session.flush()

    finding_high = AuditFinding(
        audit_run_id=audit_run.id,
        invoice_id=invoice.id,
        item_id=item.id,
        rule_id="rule_high",
        inconsistency_code="ERR1",
        severity="alto",
        message_pt="Erro grave",
        suggestion_code="FIX1",
        references=None,
        evidence={},
    )
    finding_medium = AuditFinding(
        audit_run_id=audit_run.id,
        invoice_id=invoice.id,
        item_id=None,
        rule_id="rule_medium",
        inconsistency_code="ERR2",
        severity="medio",
        message_pt="Erro médio",
        suggestion_code=None,
        references=None,
        evidence={},
    )
    session.add_all([finding_high, finding_medium])
    session.commit()

    builder = AuditSummaryBuilder(session)
    summary = builder.build(
        audit_run,
        processed_invoices=1,
        existing_summary=audit_run.summary,
    )

    assert summary["processed_invoices"] == 1
    assert summary["total_findings"] == 2
    assert summary["severity_breakdown"]["alto"] == 1
    assert summary["severity_breakdown"]["medio"] == 1
    assert summary["metadata"]["source"] == "unit"
    rule_ids = {rule["rule_id"] for rule in summary["top_rules"]}
    assert {"rule_high", "rule_medium"}.issubset(rule_ids)
