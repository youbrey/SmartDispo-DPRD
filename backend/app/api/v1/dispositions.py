from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.dependencies import CurrentUser, SessionDep, ensure_active_device, require_permission
from app.models.entities import Document
from app.schemas.common import DispositionCreate, DispositionView
from app.services.access import ensure_document_access
from app.services.dispositions import create_disposition, list_dispositions

router = APIRouter(prefix="/documents/{document_id}/dispositions", tags=["dispositions"])


@router.get("", response_model=list[DispositionView])
async def list_all(document_id: UUID, session: SessionDep, user: CurrentUser) -> list[DispositionView]:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    await ensure_document_access(session, document, user.id)
    return await list_dispositions(session, document_id)


@router.post("", response_model=DispositionView, status_code=201)
async def create(
    document_id: UUID,
    payload: DispositionCreate,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("disposition.create")),
) -> DispositionView:
    await ensure_active_device(session, user.id, request.headers.get("X-Device-ID"))
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    await ensure_document_access(session, document, user.id)
    return await create_disposition(session, document_id, payload, user.id)
