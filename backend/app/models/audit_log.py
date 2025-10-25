from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(50))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    ip: Mapped[str | None] = mapped_column(String(45))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    user: Mapped["User" | None] = relationship("User", back_populates="audit_logs")
