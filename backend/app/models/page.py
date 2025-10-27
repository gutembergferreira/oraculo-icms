from __future__ import annotations

from datetime import datetime

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.models.user import User


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    updated_by: Mapped["User" | None] = relationship("User")
