from __future__ import annotations
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class OrgSetting(Base):
    __tablename__ = "org_settings"

    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), primary_key=True, nullable=False
    )
    current_plan_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id"))
    storage_used_mb: Mapped[int] = mapped_column(default=0)
    xml_uploaded_count_month: Mapped[int] = mapped_column(default=0)
    locale: Mapped[str] = mapped_column(String(10), default="pt-BR")
    billing_email: Mapped[str | None] = mapped_column(String(255))
    legal_consent_at: Mapped[datetime | None] = mapped_column()
    flags: Mapped[dict] = mapped_column(JSON, default=dict)
    plan_limits: Mapped[dict] = mapped_column(JSON, default=dict)
    plan_features: Mapped[dict] = mapped_column(JSON, default=dict)
    usage_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="settings"
    )
    plan: Mapped[Plan] = relationship("Plan")
