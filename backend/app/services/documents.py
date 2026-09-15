import json
from hashlib import sha256
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Document, DocumentStatus, DocumentType, DocumentVersion
from app.schemas.common import DocumentCreate, DocumentUpdate
from app.services.audit import record_audit


def canonical_hash(content: dict) -> str:
    serialized = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(serialized.encode()).hexdigest()


async def create_document(session: AsyncSession, payload: DocumentCreate, user_id: UUID) -> Document:
    try:
        document_type = DocumentType(payload.document_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Jenis dokumen tidak valid") from exc
    document = Document(
        document_type=document_type,
        title=payload.title,
        created_by=user_id,
        status=DocumentStatus.DRAFT,
    )
    session.add(document)
    await session.flush()
    session.add(
        DocumentVersion(
            document_id=document.id,
            version_number=1,
            content=payload.content,
            sha256_hash=canonical_hash(payload.content),
            created_by=user_id,
            change_reason="Versi awal",
        )
    )
    record_audit(
        session,
        actor_user_id=user_id,
        action="DOCUMENT_CREATED",
        entity_type="Document",
        entity_id=document.id,
        after={"version": 1, "type": document_type.value, "title": payload.title},
    )
    await session.commit()
    await session.refresh(document)
    return document


async def update_document(session: AsyncSession, document_id: UUID, payload: DocumentUpdate, user_id: UUID) -> Document:
    document = (
        await session.execute(select(Document).where(Document.id == document_id).with_for_update())
    ).scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    if document.lock_version != payload.expected_lock_version:
        raise HTTPException(status_code=409, detail="Dokumen telah diubah pengguna lain")
    if document.status not in {DocumentStatus.DRAFT, DocumentStatus.RETURNED}:
        raise HTTPException(status_code=409, detail="Dokumen pada status ini tidak dapat diedit")
    before = {"version": document.current_version, "title": document.title}
    document.current_version += 1
    document.lock_version += 1
    if payload.title:
        document.title = payload.title
    session.add(
        DocumentVersion(
            document_id=document.id,
            version_number=document.current_version,
            content=payload.content,
            sha256_hash=canonical_hash(payload.content),
            created_by=user_id,
            change_reason=payload.change_reason,
        )
    )
    record_audit(
        session,
        actor_user_id=user_id,
        action="DOCUMENT_VERSION_CREATED",
        entity_type="Document",
        entity_id=document.id,
        before=before,
        after={"version": document.current_version, "title": document.title},
    )
    await session.commit()
    await session.refresh(document)
    return document
