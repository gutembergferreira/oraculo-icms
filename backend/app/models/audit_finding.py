from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class AuditFinding(Base):
    __tablename__ = "audit_findings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    audit_run_id: Mapped[int] = mapped_column(ForeignKey("audit_runs.id"), nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("invoice_items.id"))
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    inconsistency_code: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    message_pt: Mapped[str] = mapped_column(String(500), nullable=False)
    suggestion_code: Mapped[str | None] = mapped_column(String(50))
    references: Mapped[list[str] | None] = mapped_column(JSON)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)

    audit_run: Mapped["AuditRun"] = relationship(
        "AuditRun", back_populates="findings"
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice", back_populates="findings"
    )
    item: Mapped["InvoiceItem" | None] = relationship("InvoiceItem")
