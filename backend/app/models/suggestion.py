from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class Suggestion(Base):
    __tablename__ = "suggestions"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body_pt: Mapped[str] = mapped_column(String(1000), nullable=False)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    requires_accountant_review: Mapped[bool] = mapped_column(Boolean, default=False)
