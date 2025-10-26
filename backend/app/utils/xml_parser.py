from __future__ import annotations

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from lxml import etree


@dataclass(slots=True)
class ParsedInvoiceItem:
    seq: int
    product_code: str
    description: str
    ncm: str | None
    cest: str | None
    cfop: str | None
    cst: str | None
    quantity: Decimal
    unit_value: Decimal
    total_value: Decimal
    freight_alloc: Decimal | None
    discount: Decimal | None
    bc_icms: Decimal | None
    icms_value: Decimal | None
    bc_st: Decimal | None
    icms_st_value: Decimal | None
    other_taxes: dict[str, Any]


@dataclass(slots=True)
class ParsedInvoice:
    access_key: str
    emitente_cnpj: str
    destinatario_cnpj: str
    uf: str
    issue_date: date
    total_value: Decimal
    freight_value: Decimal | None
    has_st: bool
    items: list[ParsedInvoiceItem]
    metadata: dict[str, Any]


class XMLParser:
    """Parser de XMLs de NF-e inspirado no projeto zfm-calculator.

    O parser transforma o conteúdo do XML em estruturas ricas utilizadas pelo
    serviço de importação multi-tenant. Ele extrai cabeçalho, itens e tributos
    relevantes para o motor de auditoria.
    """

    def __init__(self, validate_xsd: bool = False) -> None:
        self.validate_xsd = validate_xsd

    def parse(self, file_path: Path) -> ParsedInvoice:
        tree = etree.parse(str(file_path))
        return self._parse_tree(tree)

    def parse_bytes(self, payload: bytes) -> ParsedInvoice:
        tree = etree.fromstring(payload)
        return self._parse_tree(etree.ElementTree(tree))

    # ------------------------------------------------------------------
    def _parse_tree(self, tree: etree._ElementTree) -> ParsedInvoice:
        root = tree.getroot()
        ide = root.find('.//{*}ide')
        emit = root.find('.//{*}emit')
        dest = root.find('.//{*}dest')
        total = root.find('.//{*}total/{*}ICMSTot')

        access_key = self._extract_access_key(root)
        emit_cnpj = self._text(emit, 'CNPJ')
        dest_cnpj = self._text(dest, 'CNPJ')
        uf = self._text(ide, 'UF') or self._text(dest, 'UF') or ""
        issue_date = self._parse_issue_date(self._text(ide, 'dhEmi') or self._text(ide, 'dEmi'))
        total_value = self._decimal(self._text(total, 'vNF'))
        freight_value = self._decimal(self._text(total, 'vFrete'), allow_none=True)

        items = [self._parse_item(node) for node in root.findall('.//{*}det')]
        has_st = any(item.icms_st_value and item.icms_st_value > 0 for item in items)

        metadata = {
            'model': self._text(ide, 'mod'),
            'series': self._text(ide, 'serie'),
            'number': self._text(ide, 'nNF'),
        }

        return ParsedInvoice(
            access_key=access_key,
            emitente_cnpj=emit_cnpj,
            destinatario_cnpj=dest_cnpj,
            uf=uf,
            issue_date=issue_date,
            total_value=total_value,
            freight_value=freight_value,
            has_st=has_st,
            items=items,
            metadata=metadata,
        )

    def _parse_item(self, node: etree._Element) -> ParsedInvoiceItem:
        prod = node.find('{*}prod')
        imposto = node.find('{*}imposto')
        icms = imposto.find('.//{*}ICMS') if imposto is not None else None
        icms_st_value = None
        bc_st = None
        bc_icms = None
        icms_value = None

        if icms is not None:
            icms_st_value = self._decimal(self._first_text(icms, ['vICMSST', 'vICMSSTDeson']), allow_none=True)
            bc_st = self._decimal(self._first_text(icms, ['vBCST', 'vBCSTRet']), allow_none=True)
            bc_icms = self._decimal(self._first_text(icms, ['vBC', 'vBCOp']), allow_none=True)
            icms_value = self._decimal(self._first_text(icms, ['vICMS', 'vICMSOp']), allow_none=True)

        other_taxes: dict[str, Any] = {}
        if imposto is not None:
            mapping = {
                'IPI': ('ipi', 'vIPI'),
                'PIS': ('pis', 'vPIS'),
                'COFINS': ('cofins', 'vCOFINS'),
            }
            for tag, (alias, value_tag) in mapping.items():
                elem = imposto.find(f'.//{{*}}{tag}')
                text_value = self._first_text(elem, [value_tag])
                value = self._decimal(text_value, allow_none=True) if text_value is not None else None
                if value is not None:
                    other_taxes[alias] = float(value)

        return ParsedInvoiceItem(
            seq=int(node.get('nItem', '0') or 0),
            product_code=self._text(prod, 'cProd') or '',
            description=self._text(prod, 'xProd') or '',
            ncm=self._text(prod, 'NCM'),
            cest=self._text(prod, 'CEST'),
            cfop=self._text(prod, 'CFOP'),
            cst=self._first_text(icms, ['CSOSN', 'CST']),
            quantity=self._decimal(self._text(prod, 'qCom') or '0'),
            unit_value=self._decimal(self._text(prod, 'vUnCom') or '0'),
            total_value=self._decimal(self._text(prod, 'vProd') or '0'),
            freight_alloc=self._decimal(self._text(prod, 'vFrete'), allow_none=True),
            discount=self._decimal(self._text(prod, 'vDesc'), allow_none=True),
            bc_icms=bc_icms,
            icms_value=icms_value,
            bc_st=bc_st,
            icms_st_value=icms_st_value,
            other_taxes=other_taxes,
        )

    # ------------------------------------------------------------------
    def _extract_access_key(self, root: etree._Element) -> str:
        inf_nfe = root.find('.//{*}infNFe')
        if inf_nfe is not None:
            access_key_attr = inf_nfe.get('Id')
            if access_key_attr:
                return access_key_attr.replace('NFe', '')
        key = root.findtext('.//{*}chNFe')
        if key:
            return key
        return root.findtext('.//{*}ide/{*}cNF', default='')

    def _parse_issue_date(self, raw: str | None) -> date:
        if not raw:
            return date.today()
        try:
            if len(raw) == 10:
                return datetime.strptime(raw, '%Y-%m-%d').date()
            return datetime.fromisoformat(raw).date()
        except ValueError:
            return date.today()

    def _text(self, node: etree._Element | None, tag: str) -> str | None:
        if node is None:
            return None
        return node.findtext(f'{{*}}{tag}')

    def _first_text(self, node: etree._Element | None, tags: Iterable[str]) -> str | None:
        if node is None:
            return None
        for tag in tags:
            value = node.findtext(f'.//{{*}}{tag}')
            if value:
                return value
        return None

    def _decimal(self, value: str | None, *, allow_none: bool = False) -> Decimal | None:
        if value is None or value == '':
            return None if allow_none else Decimal('0')
        try:
            return Decimal(value.replace(',', '.'))
        except Exception:  # pragma: no cover - valores inesperados
            return None if allow_none else Decimal('0')
