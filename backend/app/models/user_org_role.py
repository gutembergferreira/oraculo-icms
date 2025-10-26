from __future__ import annotations
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class UserOrgRole(Base):
    __tablename__ = "user_org_roles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), primary_key=True, nullable=False
    )
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), primary_key=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="roles")
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="users"
    )
