from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.file import File
from app.models.invoice import Invoice
from app.schemas import InvoiceRead

router = APIRouter()


@router.get("/{org_id}/invoices", response_model=List[InvoiceRead])
def list_invoices(
    org_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[Invoice]:
    return (
        db.query(Invoice)
        .filter(Invoice.org_id == org_id)
        .limit(50)
        .all()
    )


@router.post("/{org_id}/uploads/xml")
async def upload_xml(org_id: int, file: UploadFile, db: Session = Depends(get_db_session)) -> dict:
    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="Arquivo inválido")

    stored = File(
        org_id=org_id,
        file_name=file.filename,
        mime=file.content_type or "application/xml",
        size_bytes=0,
        storage_backend="local",
        storage_path=f"/storage/{file.filename}",
        sha256="dummy",
    )
    db.add(stored)
    db.commit()
    db.refresh(stored)
    return {"status": "uploaded", "file_id": stored.id}
