from pathlib import Path

from app.utils.xml_parser import XMLParser


def test_parse_basic_fields(tmp_path: Path) -> None:
    sample = Path(__file__).parent.parent / "data" / "sample_invoice.xml"
    parser = XMLParser()
    result = parser.parse(sample)
    assert result["access_key"] == "12345678"
    assert result["emitente_cnpj"] == "12345678000100"
    assert result["destinatario_cnpj"] == "00987654000191"
