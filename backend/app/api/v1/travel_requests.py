from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep, require_permission
from app.models.entities import Document, TravelRequest
from app.schemas.common import TravelRequestCreate, TravelRequestUpdate, TravelRequestView
from app.services.access import ensure_document_access
from app.services.travel_requests import (
    create_travel_request,
    creator_actions,
    travel_request_view,
    update_travel_request,
)

router = APIRouter(prefix="/travel-requests", tags=["travel requests"])


async def _entities(session: SessionDep, document_id: UUID) -> tuple[Document, TravelRequest]:
    document = await session.get(Document, document_id)
    request = (
        await session.execute(select(TravelRequest).where(TravelRequest.document_id == document_id))
    ).scalar_one_or_none()
    if not document or not request:
        raise HTTPException(status_code=404, detail="Permintaan perjalanan dinas tidak ditemukan")
    return document, request


@router.post("", response_model=TravelRequestView, status_code=201)
async def create(
    payload: TravelRequestCreate,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("travel_request.create")),
) -> TravelRequestView:
    document, request = await create_travel_request(session, payload, user.id)
    return await travel_request_view(session, document, request, creator_actions(document))


@router.get("/{document_id}", response_model=TravelRequestView)
async def get(document_id: UUID, session: SessionDep, user: CurrentUser) -> TravelRequestView:
    document, request = await _entities(session, document_id)
    await ensure_document_access(session, document, user.id)
    actions = creator_actions(document) if document.created_by == user.id else ["PREVIEW"]
    return await travel_request_view(session, document, request, actions)


@router.patch("/{document_id}", response_model=TravelRequestView)
async def update(
    document_id: UUID,
    payload: TravelRequestUpdate,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("travel_request.edit")),
) -> TravelRequestView:
    document, request = await update_travel_request(session, document_id, payload, user.id)
    return await travel_request_view(session, document, request, creator_actions(document))
