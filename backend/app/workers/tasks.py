from __future__ import annotations

import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from celery import shared_task
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.audit_run import AuditRun, AuditStatus
from app.models.file import File
from app.models.invoice import Invoice
from app.models.org_setting import OrgSetting
from app.services.invoice_ingestion import InvoiceIngestor
from app.services.storage import get_storage_backend
from app.services.zfm_calculator import ZFMAuditCalculator
from app.services.audit_summary import AuditSummaryBuilder
from app.services.audit_report import AuditReportBuilder
from app.services.org_plan_limits import OrgPlanLimiter, PlanLimitError


def _get_session() -> Session:
    return SessionLocal()


@shared_task
def parse_xml_batch(
    zip_path: str,
    org_id: int,
    audit_run_id: int,
    raw_file_id: int,
    requested_by: int | None = None,
) -> dict:
    session = _get_session()
    audit_run: AuditRun | None = None
    try:
        audit_run = session.get(AuditRun, audit_run_id)
        if not audit_run:
            raise ValueError('Audit run not found')

        raw_file = session.get(File, raw_file_id)
        if not raw_file:
            raise ValueError('Arquivo de origem não encontrado')

        storage = get_storage_backend(raw_file.storage_backend)
        zip_bytes = storage.read(path=zip_path)

        audit_run.status = AuditStatus.RUNNING
        audit_run.started_at = datetime.utcnow()
        session.flush()

        ingestor = InvoiceIngestor()
        limiter = OrgPlanLimiter(session)
        calculator = ZFMAuditCalculator(session, org_id)
        calculator.bind_to_run(audit_run)
        processed = 0
        total_findings = 0

        with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
            for info in archive.infolist():
                if info.is_dir() or not info.filename.lower().endswith('.xml'):
                    continue
                payload = archive.read(info)
                try:
                    setting = limiter.ensure_upload_quota(org_id, new_files=1)
                except PlanLimitError as exc:
                    raise ValueError(exc.message) from exc
                ingest_result = ingestor.ingest_invoice(
                    session=session,
                    org_id=org_id,
                    payload=payload,
                    file_name=Path(info.filename).name,
                    mime='application/xml',
                    uploaded_by=requested_by,
                    raw_file=raw_file,
                )
                findings = calculator.persist_results(
                    audit_run=audit_run,
                    invoice=ingest_result.invoice,
                )
                limiter.register_usage(setting, uploaded_files=1)
                processed += 1
                total_findings += len(findings)

        metadata = dict((audit_run.summary or {}).get('metadata') or {})
        metadata.update(
            {
                'source': 'zip_batch',
                'file_id': raw_file_id,
                'file_name': raw_file.file_name,
            }
        )
        summary_builder = AuditSummaryBuilder(session)
        audit_run.summary = summary_builder.build(
            audit_run,
            processed_invoices=processed,
            existing_summary={**(audit_run.summary or {}), 'metadata': metadata},
        )
        audit_run.status = AuditStatus.DONE
        audit_run.finished_at = datetime.utcnow()
        session.commit()
        return {
            'audit_run_id': audit_run.id,
            'processed_invoices': processed,
            'total_findings': total_findings,
        }
    except Exception as exc:  # pragma: no cover - erros críticos
        session.rollback()
        if audit_run:
            audit_run.status = AuditStatus.FAILED
            audit_run.finished_at = datetime.utcnow()
            audit_run.summary = {**(audit_run.summary or {}), 'error': str(exc)}
            session.add(audit_run)
            session.commit()
        raise
    finally:
        session.close()


@shared_task
def run_audit(audit_run_id: int, invoice_ids: list[int] | None = None) -> dict:
    session = _get_session()
    audit_run: AuditRun | None = None
    try:
        audit_run = session.get(AuditRun, audit_run_id)
        if not audit_run:
            raise ValueError('Audit run not found')

        calculator = ZFMAuditCalculator(session, audit_run.org_id)
        calculator.bind_to_run(audit_run)
        query = session.query(Invoice).filter(Invoice.org_id == audit_run.org_id)
        if invoice_ids:
            query = query.filter(Invoice.id.in_(invoice_ids))
        invoices = query.order_by(Invoice.issue_date).all()

        audit_run.started_at = datetime.utcnow()
        audit_run.status = AuditStatus.RUNNING
        session.flush()

        processed = 0
        total_findings = 0
        for invoice in invoices:
            findings = calculator.persist_results(
                audit_run=audit_run,
                invoice=invoice,
            )
            total_findings += len(findings)
            processed += 1

        summary_builder = AuditSummaryBuilder(session)
        audit_run.summary = summary_builder.build(
            audit_run,
            processed_invoices=processed,
            existing_summary=audit_run.summary,
        )
        audit_run.status = AuditStatus.DONE
        audit_run.finished_at = datetime.utcnow()
        session.commit()
        return {
            'audit_run_id': audit_run.id,
            'processed_invoices': processed,
            'total_findings': total_findings,
        }
    except Exception as exc:  # pragma: no cover - erros críticos
        session.rollback()
        if audit_run:
            audit_run.status = AuditStatus.FAILED
            audit_run.finished_at = datetime.utcnow()
            audit_run.summary = {**(audit_run.summary or {}), 'error': str(exc)}
            session.add(audit_run)
            session.commit()
        raise
    finally:
        session.close()


@shared_task
def generate_report_pdf(audit_id: int) -> dict:
    session = _get_session()
    try:
        audit = session.get(AuditRun, audit_id)
        if not audit:
            raise ValueError('Audit run not found')
        builder = AuditReportBuilder(session)
        pdf_bytes = builder.generate_pdf(audit)
        builder.register_download(audit_run=audit, user=None, file_format='pdf')
        session.commit()
        return {'audit_id': audit_id, 'size_bytes': len(pdf_bytes)}
    finally:
        session.close()


@shared_task
def generate_report_xlsx(audit_id: int) -> dict:
    session = _get_session()
    try:
        audit = session.get(AuditRun, audit_id)
        if not audit:
            raise ValueError('Audit run not found')
        builder = AuditReportBuilder(session)
        xlsx_bytes = builder.generate_xlsx(audit)
        builder.register_download(audit_run=audit, user=None, file_format='xlsx')
        session.commit()
        return {'audit_id': audit_id, 'size_bytes': len(xlsx_bytes)}
    finally:
        session.close()


@shared_task
def reset_monthly_limits() -> int:
    session: Session = _get_session()
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
