from __future__ import annotations

from textwrap import dedent

from fastapi.testclient import TestClient

def test_get_baseline_rules(client: TestClient) -> None:
    response = client.get("/api/v1/rules/baseline")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Pacote ZFM"
    assert "rules" in payload["content"]
    assert len(payload["content"]["rules"]) >= 1


def test_get_org_rules_payload(client: TestClient, seed_data) -> None:
    _, org = seed_data
    response = client.get(f"/api/v1/rules/orgs/{org.id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["baseline"]["version"]
    assert payload["effective_rules"]
    assert payload["metadata"]["sources"]["baseline"]["id"] == payload["baseline"]["id"]


def test_put_org_override(client: TestClient, seed_data) -> None:
    _, org = seed_data
    override_yaml = dedent(
        """
        name: "Override Teste"
        rules:
          - id: "ZFM-ST-001"
            name: "ST custom"
            scope: "item"
            when:
              all:
                - invoice.uf == "AM"
                - helpers.value_or(item.icms_st_value, 0) == 0
            then:
              inconsistency_code: "ST_CUSTOM"
              severity: "alto"
              message_pt: "Regra customizada para ST."
        """
    ).strip()

    response = client.put(
        f"/api/v1/rules/orgs/{org.id}",
        json={"yaml": override_yaml, "name": "Override Teste"},
    )
    assert response.status_code == 200
    override_payload = response.json()
    assert override_payload["name"] == "Override Teste"

    effective = client.get(f"/api/v1/rules/orgs/{org.id}").json()
    rule_ids = [rule["id"] for rule in effective["effective_rules"]]
    assert "ZFM-ST-001" in rule_ids
    custom_rule = next(rule for rule in effective["effective_rules"] if rule["id"] == "ZFM-ST-001")
    assert custom_rule["then"]["inconsistency_code"] == "ST_CUSTOM"
