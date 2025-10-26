from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.audit_run import AuditRun, AuditStatus
from app.services.invoice_ingestion import InvoiceIngestor
from app.services.zfm_calculator import ZFMAuditCalculator
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

    ingestor = InvoiceIngestor()
    result = ingestor.ingest_invoice(
        session=db,
        org_id=org_id,
        payload=payload,
        file_name=file.filename,
        mime=file.content_type or 'application/xml',
        uploaded_by=current_user.id,
    )

    audit_run = AuditRun(
        org_id=org_id,
        requested_by=current_user.id,
        status=AuditStatus.PENDING,
        summary={'source': 'single_xml', 'file_name': file.filename},
    )
    db.add(audit_run)
    db.flush()

    calculator = ZFMAuditCalculator()
    findings = calculator.persist_results(session=db, audit_run=audit_run, invoice=result.invoice)
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

    ingestor = InvoiceIngestor()
    stored_file = ingestor.store_file(
        session=db,
        org_id=org_id,
        file_name=file.filename,
        payload=payload,
        mime=file.content_type or 'application/zip',
        uploaded_by=current_user.id,
    )

    audit_run = AuditRun(
        org_id=org_id,
        requested_by=current_user.id,
        status=AuditStatus.PENDING,
        summary={'source': 'zip_batch', 'file_id': stored_file.id, 'file_name': file.filename},
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
