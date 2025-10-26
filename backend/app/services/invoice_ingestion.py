from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import File
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.utils.xml_parser import ParsedInvoice, ParsedInvoiceItem, XMLParser


@dataclass(slots=True)
class IngestionResult:
    invoice: Invoice
    created: bool


class InvoiceIngestor:
    """Serviço responsável por armazenar e transformar XMLs de NF-e."""

    def __init__(self, parser: XMLParser | None = None, base_path: Path | None = None) -> None:
        self.parser = parser or XMLParser()
        self.base_path = base_path or Path(settings.local_storage_path)

    # ------------------------------------------------------------------
    def store_file(
        self,
        *,
        session: Session,
        org_id: int,
        file_name: str,
        payload: bytes,
        mime: str,
        uploaded_by: int | None,
    ) -> File:
        target_dir = self.base_path / str(org_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        safe_name = file_name.replace('/', '_')
        disk_path = target_dir / f"{timestamp}_{safe_name}"
        disk_path.write_bytes(payload)

        sha256 = hashlib.sha256(payload).hexdigest()
        file = File(
            org_id=org_id,
            file_name=file_name,
            mime=mime,
            size_bytes=len(payload),
            storage_backend=settings.storage_backend,
            storage_path=str(disk_path),
            sha256=sha256,
            uploaded_by=uploaded_by,
        )
        session.add(file)
        session.flush()
        return file

    # ------------------------------------------------------------------
    def ingest_invoice(
        self,
        *,
        session: Session,
        org_id: int,
        payload: bytes,
        file_name: str,
        mime: str,
        uploaded_by: int | None,
        raw_file: File | None = None,
    ) -> IngestionResult:
        file_record = raw_file or self.store_file(
            session=session,
            org_id=org_id,
            file_name=file_name,
            payload=payload,
            mime=mime,
            uploaded_by=uploaded_by,
        )
        parsed = self.parser.parse_bytes(payload)
        invoice, created = self._upsert_invoice(session, org_id, parsed, file_record)
        return IngestionResult(invoice=invoice, created=created)

    # ------------------------------------------------------------------
    def ingest_from_path(
        self,
        *,
        session: Session,
        org_id: int,
        file_path: Path,
        uploaded_by: int | None,
    ) -> IngestionResult:
        payload = file_path.read_bytes()
        return self.ingest_invoice(
            session=session,
            org_id=org_id,
            payload=payload,
            file_name=file_path.name,
            mime='application/xml',
            uploaded_by=uploaded_by,
        )

    # ------------------------------------------------------------------
    def _upsert_invoice(
        self,
        session: Session,
        org_id: int,
        parsed: ParsedInvoice,
        file_record: File,
    ) -> tuple[Invoice, bool]:
        invoice = (
            session.query(Invoice)
            .filter(Invoice.org_id == org_id, Invoice.access_key == parsed.access_key)
            .one_or_none()
        )
        created = False
        if invoice is None:
            invoice = Invoice(org_id=org_id, access_key=parsed.access_key)
            created = True

        invoice.emitente_cnpj = parsed.emitente_cnpj or ''
        invoice.destinatario_cnpj = parsed.destinatario_cnpj or ''
        invoice.uf = parsed.uf or ''
        invoice.issue_date = parsed.issue_date
        invoice.total_value = float(parsed.total_value)
        invoice.freight_value = float(parsed.freight_value) if parsed.freight_value is not None else None
        invoice.has_st = parsed.has_st
        invoice.raw_file_id = file_record.id
        invoice.parsed_at = datetime.utcnow()
        invoice.indexed_at = datetime.utcnow()

        session.add(invoice)
        session.flush()

        self._replace_items(session, invoice, parsed.items)
        return invoice, created

    def _replace_items(
        self,
        session: Session,
        invoice: Invoice,
        items: Iterable[ParsedInvoiceItem],
    ) -> None:
        session.execute(
            delete(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)
        )
        session.flush()

        for index, item in enumerate(items, start=1):
            seq = item.seq or index
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                seq=seq,
                product_code=item.product_code,
                description=item.description,
                ncm=item.ncm,
                cest=item.cest,
                cfop=item.cfop,
                cst=item.cst,
                quantity=float(item.quantity),
                unit_value=float(item.unit_value),
                total_value=float(item.total_value),
                freight_alloc=float(item.freight_alloc) if item.freight_alloc is not None else None,
                discount=float(item.discount) if item.discount is not None else None,
                bc_icms=float(item.bc_icms) if item.bc_icms is not None else None,
                icms_value=float(item.icms_value) if item.icms_value is not None else None,
                bc_st=float(item.bc_st) if item.bc_st is not None else None,
                icms_st_value=float(item.icms_st_value) if item.icms_st_value is not None else None,
                other_taxes=item.other_taxes,
            )
            session.add(invoice_item)
        session.flush()
