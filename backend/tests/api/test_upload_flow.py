from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient


def test_single_xml_upload_flow(client: TestClient, seed_data):
    _, org = seed_data
    sample_path = Path(__file__).resolve().parent.parent / "data" / "sample_invoice.xml"
    payload = sample_path.read_bytes()

    response = client.post(
        f"/api/v1/orgs/{org.id}/uploads/xml",
        files={"file": ("nota.xml", payload, "application/xml")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["findings"] >= 3
    invoice_id = data["invoice_id"]

    response = client.get(f"/api/v1/orgs/{org.id}/invoices")
    assert response.status_code == 200
    invoices = response.json()
    assert len(invoices) == 1
    assert invoices[0]["findings_count"] >= 3

    detail = client.get(f"/api/v1/orgs/{org.id}/invoices/{invoice_id}")
    assert detail.status_code == 200
    detail_json = detail.json()
    assert len(detail_json["items"]) == 2
    assert len(detail_json["findings"]) >= 3
    rule_ids = {finding["rule_id"] for finding in detail_json["findings"]}
    assert "ZFM-TOTAL-001" in rule_ids


def test_zip_upload_flow(client: TestClient, seed_data):
    _, org = seed_data
    sample_path = Path(__file__).resolve().parent.parent / "data" / "sample_invoice.xml"
    payload = sample_path.read_bytes()

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("nota1.xml", payload)
        archive.writestr("nota2.xml", payload)
    buffer.seek(0)

    response = client.post(
        f"/api/v1/orgs/{org.id}/uploads/zip",
        files={"file": ("lote.zip", buffer.read(), "application/zip")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["processed_invoices"] == 2
    assert data["total_findings"] >= 3
