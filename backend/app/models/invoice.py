from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("access_key", "org_id", name="uq_invoice_access_org"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    access_key: Mapped[str] = mapped_column(String(44), nullable=False)
    emitente_cnpj: Mapped[str] = mapped_column(String(14), nullable=False)
    destinatario_cnpj: Mapped[str] = mapped_column(String(14), nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    freight_value: Mapped[float | None] = mapped_column(Numeric(12, 2))
    has_st: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_file_id: Mapped[int | None] = mapped_column(ForeignKey("files.id"))
    parsed_at: Mapped[datetime | None] = mapped_column()
    indexed_at: Mapped[datetime | None] = mapped_column()

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="invoices"
    )
    file: Mapped["File" | None] = relationship("File")
    items: Mapped[list["InvoiceItem"]] = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    findings: Mapped[list["AuditFinding"]] = relationship(
        "AuditFinding", back_populates="invoice"
    )
