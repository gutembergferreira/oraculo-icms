from __future__ import annotations

from datetime import date
from typing import Any

from app.schemas.audit import AuditFindingRead
from app.schemas.base import OraculoBaseModel


class InvoiceItemRead(OraculoBaseModel):
    id: int
    seq: int
    product_code: str
    description: str
    ncm: str | None
    cest: str | None
    cfop: str | None
    cst: str | None
    quantity: float
    unit_value: float
    total_value: float
    freight_alloc: float | None = None
    discount: float | None = None
    bc_icms: float | None = None
    icms_value: float | None = None
    bc_st: float | None = None
    icms_st_value: float | None = None
    other_taxes: dict[str, Any] | None = None


class InvoiceSummaryRead(OraculoBaseModel):
    id: int
    access_key: str
    emitente_cnpj: str
    destinatario_cnpj: str
    uf: str
    issue_date: date
    total_value: float
    freight_value: float | None
    has_st: bool
    findings_count: int = 0


class InvoiceDetailRead(InvoiceSummaryRead):
    items: list[InvoiceItemRead]
    findings: list[AuditFindingRead] = []
