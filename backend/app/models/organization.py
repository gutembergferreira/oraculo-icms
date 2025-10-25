from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False)
    zfm_enabled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="organization"
    )
    users: Mapped[list["UserOrgRole"]] = relationship(
        "UserOrgRole", back_populates="organization"
    )
    settings: Mapped["OrgSetting"] = relationship(
        "OrgSetting", back_populates="organization", uselist=False
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="organization"
    )
    audit_runs: Mapped[list["AuditRun"]] = relationship(
        "AuditRun", back_populates="organization"
    )
