from decimal import Decimal
from pathlib import Path

from app.utils.xml_parser import XMLParser


def test_parse_full_invoice(tmp_path: Path) -> None:
    sample = Path(__file__).parent.parent / "data" / "sample_invoice.xml"
    parser = XMLParser()
    result = parser.parse(sample)

    assert result.access_key == "35181111111111111111550010000001231000001234"
    assert result.emitente_cnpj == "12345678000100"
    assert result.destinatario_cnpj == "00987654000191"
    assert result.total_value == Decimal("95.00")
    assert result.freight_value == Decimal("5.00")
    assert len(result.items) == 2
    assert result.items[0].cfop == "6102"
    assert result.items[1].ncm == "33030010"
    assert result.has_st is False
