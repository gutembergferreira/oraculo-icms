from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.rules_dsl import RuleDSLParser
from app.services.rules_engine import RuleEngine


@dataclass
class ItemStub:
    cfop: str | None
    ncm: str | None
    cest: str | None
    cst: str | None
    total_value: float
    icms_st_value: float | None


@dataclass
class InvoiceStub:
    total_value: float
    freight_value: float | None
    has_st: bool
    uf: str
    items: list[ItemStub]


def test_rule_engine_applies_zfm_pack() -> None:
    parser = RuleDSLParser()
    pack_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "rules"
        / "packs"
        / "zfm_baseline.yaml"
    )
    document = parser.parse(pack_path.read_text(encoding="utf-8"))
    engine = RuleEngine(document.rules)

    invoice = InvoiceStub(
        total_value=95.0,
        freight_value=5.0,
        has_st=False,
        uf="AM",
        items=[
            ItemStub(
                cfop="6102",
                ncm="22030000",
                cest=None,
                cst="10",
                total_value=50.0,
                icms_st_value=0.0,
            ),
            ItemStub(
                cfop="6101",
                ncm="33030010",
                cest=None,
                cst="60",
                total_value=30.0,
                icms_st_value=0.0,
            ),
        ],
    )

    results = engine.evaluate(invoice=invoice, items=invoice.items)
    rule_ids = {result.rule_id for result in results}
    assert rule_ids == {"ZFM-TOTAL-001", "ZFM-ST-001", "ZFM-CEST-001"}

    total_rule = next(result for result in results if result.rule_id == "ZFM-TOTAL-001")
    assert total_rule.evidence
    assert total_rule.evidence["variacao"] > 0
