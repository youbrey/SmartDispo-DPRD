from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep, require_permission
from app.models.entities import Document, MeetingRequest, MeetingType
from app.schemas.common import (
    MeetingRequestCreate,
    MeetingRequestUpdate,
    MeetingRequestView,
    MeetingTypeView,
)
from app.services.access import ensure_document_access
from app.services.meeting_requests import (
    create_meeting_request,
    creator_actions,
    meeting_request_view,
    update_meeting_request,
)

router = APIRouter(tags=["meeting requests"])


@router.get("/meeting-types", response_model=list[MeetingTypeView])
async def list_meeting_types(session: SessionDep, _: CurrentUser) -> list[MeetingType]:
    query = select(MeetingType).where(MeetingType.active.is_(True)).order_by(MeetingType.sort_order, MeetingType.name)
    return list((await session.execute(query)).scalars())


@router.post("/meeting-requests", response_model=MeetingRequestView, status_code=201)
async def create(
    payload: MeetingRequestCreate,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("meeting_request.create")),
) -> MeetingRequestView:
    document, request, meeting_type = await create_meeting_request(session, payload, user.id)
    return await meeting_request_view(session, document, request, meeting_type, creator_actions(document))


async def _entities(session: SessionDep, document_id: UUID) -> tuple[Document, MeetingRequest, MeetingType]:
    document = await session.get(Document, document_id)
    request = (
        await session.execute(select(MeetingRequest).where(MeetingRequest.document_id == document_id))
    ).scalar_one_or_none()
    if not document or not request:
        raise HTTPException(status_code=404, detail="Permintaan rapat tidak ditemukan")
    meeting_type = (
        await session.execute(select(MeetingType).where(MeetingType.code == request.meeting_type_code))
    ).scalar_one_or_none()
    if not meeting_type:
        raise HTTPException(status_code=409, detail="Master jenis rapat tidak ditemukan")
    return document, request, meeting_type


@router.get("/meeting-requests/{document_id}", response_model=MeetingRequestView)
async def get(document_id: UUID, session: SessionDep, user: CurrentUser) -> MeetingRequestView:
    document, request, meeting_type = await _entities(session, document_id)
    await ensure_document_access(session, document, user.id)
    actions = creator_actions(document) if document.created_by == user.id else []
    return await meeting_request_view(session, document, request, meeting_type, actions)


@router.patch("/meeting-requests/{document_id}", response_model=MeetingRequestView)
async def update(
    document_id: UUID,
    payload: MeetingRequestUpdate,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("meeting_request.edit")),
) -> MeetingRequestView:
    document, request, meeting_type = await update_meeting_request(session, document_id, payload, user.id)
    return await meeting_request_view(session, document, request, meeting_type, creator_actions(document))
