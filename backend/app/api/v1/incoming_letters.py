from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep, require_permission
from app.models.entities import Document, IncomingLetter
from app.schemas.common import IncomingLetterCreate, IncomingLetterView
from app.services.access import ensure_document_access
from app.services.incoming_letters import create_incoming_letter, incoming_letter_view

router = APIRouter(prefix="/incoming-letters", tags=["incoming letters"])


@router.post("", response_model=IncomingLetterView, status_code=201)
async def create(
    payload: IncomingLetterCreate,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("incoming_letter.create")),
) -> IncomingLetterView:
    document, letter = await create_incoming_letter(session, payload, user.id)
    return await incoming_letter_view(session, document, letter, ["SUBMIT", "EDIT"])


@router.get("/{document_id}", response_model=IncomingLetterView)
async def get(document_id: UUID, session: SessionDep, user: CurrentUser) -> IncomingLetterView:
    document = await session.get(Document, document_id)
    letter = (
        await session.execute(select(IncomingLetter).where(IncomingLetter.document_id == document_id))
    ).scalar_one_or_none()
    if not document or not letter:
        raise HTTPException(status_code=404, detail="Surat masuk tidak ditemukan")
    await ensure_document_access(session, document, user.id)
    return await incoming_letter_view(session, document, letter, ["SUBMIT"] if document.created_by == user.id else [])
