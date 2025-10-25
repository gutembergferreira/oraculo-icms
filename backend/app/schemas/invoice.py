from datetime import date

from app.schemas.base import OraculoBaseModel


class InvoiceItemRead(OraculoBaseModel):
    id: int
    seq: int
    product_code: str
    description: str
    ncm: str | None
    cfop: str | None
    cst: str | None
    total_value: float


class InvoiceRead(OraculoBaseModel):
    id: int
    access_key: str
    emitente_cnpj: str
    destinatario_cnpj: str
    uf: str
    issue_date: date
    total_value: float
    freight_value: float | None
    has_st: bool
    items: list[InvoiceItemRead] = []
