from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class RuleReference(Base):
    __tablename__ = "rule_references"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    link: Mapped[str | None] = mapped_column(String(255))
    excerpt: Mapped[str | None] = mapped_column(String(500))
