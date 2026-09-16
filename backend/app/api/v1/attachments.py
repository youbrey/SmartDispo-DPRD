from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.config import get_settings
from app.core.dependencies import CurrentUser, SessionDep, require_permission
from app.models.entities import Attachment, Document
from app.services.access import ensure_document_access
from app.services.audit import record_audit

router = APIRouter(prefix="/documents/{document_id}/attachments", tags=["attachments"])
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def _validate_signature(content_type: str, data: bytes) -> bool:
    if content_type == "application/pdf":
        return data.startswith(b"%PDF-")
    if content_type == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff")
    if content_type.endswith("wordprocessingml.document"):
        return data.startswith(b"PK\x03\x04")
    return False


@router.get("")
async def list_attachments(document_id: UUID, session: SessionDep, user: CurrentUser) -> list[dict]:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    await ensure_document_access(session, document, user.id)
    rows = list(
        (
            await session.execute(
                select(Attachment).where(Attachment.document_id == document_id).order_by(Attachment.created_at)
            )
        ).scalars()
    )
    return [
        {
            "id": str(row.id),
            "original_name": row.original_name,
            "content_type": row.content_type,
            "size_bytes": row.size_bytes,
            "sha256_hash": row.sha256_hash,
            "document_version": row.document_version,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.post("", status_code=201)
async def upload_attachment(
    document_id: UUID,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("document.upload")),
    upload: UploadFile = File(...),
) -> dict:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    await ensure_document_access(session, document, user.id)
    content_type = upload.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Tipe lampiran tidak diizinkan")
    settings = get_settings()
    data = await upload.read(settings.max_attachment_bytes + 1)
    if len(data) > settings.max_attachment_bytes:
        raise HTTPException(status_code=413, detail="Ukuran lampiran melebihi batas")
    if not data or not _validate_signature(content_type, data):
        raise HTTPException(status_code=422, detail="Isi file tidak sesuai tipe lampiran")
    storage = Path(settings.attachment_dir)
    storage.mkdir(parents=True, exist_ok=True)
    object_key = f"{document.id}/{uuid4()}{ALLOWED_TYPES[content_type]}"
    target = storage / object_key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    attachment = Attachment(
        document_id=document.id,
        document_version=document.current_version,
        original_name=Path(upload.filename or "lampiran").name[:255],
        object_key=object_key,
        content_type=content_type,
        size_bytes=len(data),
        sha256_hash=sha256(data).hexdigest(),
    )
    session.add(attachment)
    await session.flush()
    record_audit(
        session,
        actor_user_id=user.id,
        action="ATTACHMENT_UPLOADED",
        entity_type="Attachment",
        entity_id=attachment.id,
        after={"document_id": str(document.id), "sha256": attachment.sha256_hash},
    )
    await session.commit()
    return {"id": str(attachment.id), "sha256_hash": attachment.sha256_hash, "size_bytes": attachment.size_bytes}


@router.get("/{attachment_id}/download")
async def download_attachment(
    document_id: UUID,
    attachment_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> FileResponse:
    document = await session.get(Document, document_id)
    attachment = await session.get(Attachment, attachment_id)
    if not document or not attachment or attachment.document_id != document_id:
        raise HTTPException(status_code=404, detail="Lampiran tidak ditemukan")
    await ensure_document_access(session, document, user.id)
    path = Path(get_settings().attachment_dir) / attachment.object_key
    if not path.exists():
        raise HTTPException(status_code=410, detail="Berkas lampiran tidak tersedia")
    return FileResponse(path, media_type=attachment.content_type, filename=attachment.original_name)
