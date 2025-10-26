from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.models.audit_log import AuditLog


def _upload_sample_invoice(client: TestClient, org_id: int) -> dict:
    sample_path = Path(__file__).resolve().parent.parent / "data" / "sample_invoice.xml"
    payload = sample_path.read_bytes()
    response = client.post(
        f"/api/v1/orgs/{org_id}/uploads/xml",
        files={"file": ("nota.xml", payload, "application/xml")},
    )
    assert response.status_code == 200
    return response.json()


def test_baseline_summary_and_reports(client: TestClient, session, seed_data):
    _, org = seed_data
    upload_result = _upload_sample_invoice(client, org.id)

    summary_response = client.get(f"/api/v1/orgs/{org.id}/audits/baseline/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["audit_run_id"] == upload_result["audit_run_id"]
    assert summary["processed_invoices"] >= 1
    assert summary["total_findings"] >= summary["processed_invoices"]

    pdf_response = client.get(
        f"/api/v1/orgs/{org.id}/audits/{upload_result['audit_run_id']}/reports/pdf"
    )
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert len(pdf_response.content) > 100

    xlsx_response = client.get(
        f"/api/v1/orgs/{org.id}/audits/{upload_result['audit_run_id']}/reports/xlsx"
    )
    assert xlsx_response.status_code == 200
    assert (
        xlsx_response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert len(xlsx_response.content) > 100

    logs = session.query(AuditLog).all()
    formats = {log.meta.get("format") for log in logs}
    assert {"pdf", "xlsx"}.issubset(formats)
