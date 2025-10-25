from datetime import datetime

from celery import shared_task
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.org_setting import OrgSetting


@shared_task
def parse_xml_batch(zip_path: str, org_id: int) -> dict:
    return {"zip_path": zip_path, "org_id": org_id, "status": "queued"}


@shared_task
def run_audit(org_id: int, date_range: tuple[str, str], ruleset_version: str | None) -> dict:
    return {
        "org_id": org_id,
        "date_range": date_range,
        "ruleset_version": ruleset_version,
        "status": "running",
    }


@shared_task
def generate_report_pdf(audit_id: int) -> dict:
    return {"audit_id": audit_id, "report": "pdf"}


@shared_task
def generate_report_xlsx(audit_id: int) -> dict:
    return {"audit_id": audit_id, "report": "xlsx"}


@shared_task
def reset_monthly_limits() -> int:
    session: Session = SessionLocal()
    try:
        count = 0
        for setting in session.query(OrgSetting).all():
            setting.xml_uploaded_count_month = 0
            session.add(setting)
            count += 1
        session.commit()
        return count
    finally:
        session.close()
