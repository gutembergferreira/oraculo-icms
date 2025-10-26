from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.audit_run import AuditRun, AuditStatus
from app.services.invoice_ingestion import InvoiceIngestor
from app.services.zfm_calculator import ZFMAuditCalculator
from app.services.audit_summary import AuditSummaryBuilder, initialize_summary
from app.services.org_plan_limits import OrgPlanLimiter, PlanLimitError
from app.workers.tasks import parse_xml_batch

router = APIRouter()


@router.post('/{org_id}/uploads/xml')
async def upload_xml(
    org_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    if not file.filename.lower().endswith('.xml'):
        raise HTTPException(status_code=400, detail='Apenas arquivos XML são aceitos.')

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail='Arquivo vazio.')

    limiter = OrgPlanLimiter(db)
    try:
        setting = limiter.ensure_upload_quota(
            org_id, new_files=1, new_bytes=len(payload)
        )
    except PlanLimitError as exc:
        raise HTTPException(status_code=403, detail=exc.message) from exc

    ingestor = InvoiceIngestor()
    result = ingestor.ingest_invoice(
        session=db,
        org_id=org_id,
        payload=payload,
        file_name=file.filename,
        mime=file.content_type or 'application/xml',
        uploaded_by=current_user.id,
    )

    limiter.register_usage(setting, uploaded_files=1, added_bytes=len(payload))

    metadata = {'source': 'single_xml', 'file_name': file.filename}
    audit_run = AuditRun(
        org_id=org_id,
        requested_by=current_user.id,
        status=AuditStatus.PENDING,
        summary=initialize_summary(metadata),
    )
    db.add(audit_run)
    db.flush()

    calculator = ZFMAuditCalculator(db, org_id)
    calculator.bind_to_run(audit_run)
    findings = calculator.persist_results(audit_run=audit_run, invoice=result.invoice)
    metadata = dict(audit_run.summary.get('metadata') if audit_run.summary else {})
    metadata.update({'invoice_id': result.invoice.id})
    summary_builder = AuditSummaryBuilder(db)
    audit_run.summary = summary_builder.build(
        audit_run,
        processed_invoices=1,
        existing_summary={**(audit_run.summary or {}), 'metadata': metadata},
    )
    audit_run.status = AuditStatus.DONE
    audit_run.finished_at = datetime.utcnow()
    db.commit()

    return {
        'invoice_id': result.invoice.id,
        'audit_run_id': audit_run.id,
        'created': result.created,
        'findings': len(findings),
    }


@router.post('/{org_id}/uploads/zip')
async def upload_zip(
    org_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    if not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail='Apenas arquivos ZIP são aceitos.')

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail='Arquivo vazio.')

    limiter = OrgPlanLimiter(db)
    try:
        setting = limiter.ensure_upload_quota(
            org_id, new_bytes=len(payload)
        )
    except PlanLimitError as exc:
        raise HTTPException(status_code=403, detail=exc.message) from exc

    ingestor = InvoiceIngestor()
    stored_file = ingestor.store_file(
        session=db,
        org_id=org_id,
        file_name=file.filename,
        payload=payload,
        mime=file.content_type or 'application/zip',
        uploaded_by=current_user.id,
    )

    limiter.register_usage(setting, added_bytes=len(payload))

    audit_run = AuditRun(
        org_id=org_id,
        requested_by=current_user.id,
        status=AuditStatus.PENDING,
        summary=initialize_summary(
            {'source': 'zip_batch', 'file_id': stored_file.id, 'file_name': file.filename}
        ),
    )
    db.add(audit_run)
    db.flush()

    result = parse_xml_batch(
        zip_path=stored_file.storage_path,
        org_id=org_id,
        audit_run_id=audit_run.id,
        raw_file_id=stored_file.id,
        requested_by=current_user.id,
    )
    db.commit()

    return result
