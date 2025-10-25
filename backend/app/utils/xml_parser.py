from pathlib import Path
from typing import Any

from lxml import etree


class XMLParser:
    def __init__(self, validate_xsd: bool = False):
        self.validate_xsd = validate_xsd

    def parse(self, file_path: Path) -> dict[str, Any]:
        tree = etree.parse(str(file_path))
        root = tree.getroot()
        return {
            "access_key": root.findtext("{*}infNFe/{*}ide/{*}cNF", default=""),
            "emitente_cnpj": root.findtext("{*}emit/{*}CNPJ", default=""),
            "destinatario_cnpj": root.findtext("{*}dest/{*}CNPJ", default=""),
        }
