from datetime import datetime

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class AuditStatus(str):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class AuditRun(Base):
    __tablename__ = "audit_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()
    ruleset_id: Mapped[int | None] = mapped_column(ForeignKey("rulesets.id"))
    status: Mapped[str] = mapped_column(String(20), default=AuditStatus.PENDING)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="audit_runs"
    )
    requester: Mapped["User"] = relationship("User")
    ruleset: Mapped["RuleSet" | None] = relationship("RuleSet", back_populates="audit_runs")
    findings: Mapped[list["AuditFinding"]] = relationship(
        "AuditFinding", back_populates="audit_run", cascade="all, delete-orphan"
    )
