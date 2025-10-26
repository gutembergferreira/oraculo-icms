from __future__ import annotations
from sqlalchemy import JSON, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.invoice import Invoice  # <- precisa importar o tipo real


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    seq: Mapped[int] = mapped_column(nullable=False)
    product_code: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    ncm: Mapped[str | None] = mapped_column(String(8))
    cest: Mapped[str | None] = mapped_column(String(7))
    cfop: Mapped[str | None] = mapped_column(String(4))
    cst: Mapped[str | None] = mapped_column(String(3))
    quantity: Mapped[float] = mapped_column(Numeric(14, 4))
    unit_value: Mapped[float] = mapped_column(Numeric(14, 4))
    total_value: Mapped[float] = mapped_column(Numeric(14, 2))
    freight_alloc: Mapped[float | None] = mapped_column(Numeric(14, 2))
    discount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    bc_icms: Mapped[float | None] = mapped_column(Numeric(14, 2))
    icms_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    bc_st: Mapped[float | None] = mapped_column(Numeric(14, 2))
    icms_st_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    other_taxes: Mapped[dict] = mapped_column(JSON, default=dict)

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="items")
