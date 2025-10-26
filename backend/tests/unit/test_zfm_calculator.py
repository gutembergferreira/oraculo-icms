from dataclasses import dataclass

from app.services.zfm_calculator import ZFMAuditCalculator


@dataclass
class ItemStub:
    cfop: str | None
    ncm: str | None
    cest: str | None
    cst: str | None
    total_value: float
    icms_st_value: float | None
    quantity: float


@dataclass
class InvoiceStub:
    total_value: float
    freight_value: float | None
    has_st: bool
    items: list[ItemStub]


def test_calculator_detects_rules() -> None:
    invoice = InvoiceStub(
        total_value=95.0,
        freight_value=5.0,
        has_st=False,
        items=[
            ItemStub(
                cfop="6102",
                ncm="22030000",
                cest=None,
                cst="00",
                total_value=50.0,
                icms_st_value=0.0,
                quantity=10,
            ),
            ItemStub(
                cfop="6101",
                ncm="33030010",
                cest=None,
                cst="60",
                total_value=30.0,
                icms_st_value=0.0,
                quantity=5,
            ),
        ],
    )
    calculator = ZFMAuditCalculator()

    results = calculator.evaluate_invoice(invoice)  # type: ignore[arg-type]
    rule_ids = {result.rule_id for result in results}
    assert rule_ids == {"zfm_total_mismatch", "zfm_st_missing", "zfm_missing_cest"}
