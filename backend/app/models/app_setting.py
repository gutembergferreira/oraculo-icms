from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    updated_by: Mapped["User" | None] = relationship("User")
