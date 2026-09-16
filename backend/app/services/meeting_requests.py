from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    Document,
    DocumentStatus,
    DocumentVersion,
    MeetingRequest,
    MeetingRequestInvitee,
    MeetingType,
)
from app.schemas.common import (
    DocumentCreate,
    DocumentUpdate,
    MeetingRequestCreate,
    MeetingRequestPayload,
    MeetingRequestUpdate,
    MeetingRequestView,
)
from app.services.documents import add_document, update_document


def meeting_content(payload: MeetingRequestPayload, meeting_type_name: str) -> dict:
    content = MeetingRequestPayload.model_validate(payload.model_dump()).model_dump(mode="json")
    content["meeting_type_name"] = meeting_type_name
    content["recipient"] = "PIMPINAN DPRD KOTA BITUNG"
    content["subject"] = "Permintaan Rapat"
    return content


async def _active_meeting_type(session: AsyncSession, code: str) -> MeetingType:
    meeting_type = (
        await session.execute(select(MeetingType).where(MeetingType.code == code, MeetingType.active.is_(True)))
    ).scalar_one_or_none()
    if not meeting_type:
        raise HTTPException(status_code=422, detail="Jenis rapat tidak aktif atau tidak ditemukan")
    return meeting_type


async def create_meeting_request(
    session: AsyncSession,
    payload: MeetingRequestCreate,
    user_id: UUID,
) -> tuple[Document, MeetingRequest, MeetingType]:
    meeting_type = await _active_meeting_type(session, payload.meeting_type_code)
    document = await add_document(
        session,
        DocumentCreate(
            document_type="MEETING_REQUEST",
            title=f"Permintaan Rapat - {meeting_type.name}",
            content=meeting_content(payload, meeting_type.name),
        ),
        user_id,
    )
    request = MeetingRequest(
        document_id=document.id,
        meeting_type_code=meeting_type.code,
        purpose=payload.purpose,
        scheduled_at=payload.scheduled_at,
        place=payload.place,
        attire=payload.attire,
    )
    session.add(request)
    await session.flush()
    session.add_all(
        [
            MeetingRequestInvitee(
                meeting_request_id=request.id,
                name=invitee.name.strip(),
                institution=invitee.institution.strip() if invitee.institution else None,
                sort_order=index,
            )
            for index, invitee in enumerate(payload.invitees, start=1)
        ]
    )
    await session.commit()
    await session.refresh(document)
    await session.refresh(request)
    return document, request, meeting_type


async def update_meeting_request(
    session: AsyncSession,
    document_id: UUID,
    payload: MeetingRequestUpdate,
    user_id: UUID,
) -> tuple[Document, MeetingRequest, MeetingType]:
    request = (
        await session.execute(select(MeetingRequest).where(MeetingRequest.document_id == document_id))
    ).scalar_one_or_none()
    document = await session.get(Document, document_id)
    if not request or not document:
        raise HTTPException(status_code=404, detail="Permintaan rapat tidak ditemukan")
    if document.created_by != user_id:
        raise HTTPException(status_code=403, detail="Hanya pembuat yang dapat mengubah permintaan rapat")
    meeting_type = await _active_meeting_type(session, payload.meeting_type_code)
    document = await update_document(
        session,
        document_id,
        DocumentUpdate(
            title=f"Permintaan Rapat - {meeting_type.name}",
            content=meeting_content(payload, meeting_type.name),
            expected_lock_version=payload.expected_lock_version,
            change_reason=payload.change_reason,
        ),
        user_id,
        commit=False,
    )
    request.meeting_type_code = meeting_type.code
    request.purpose = payload.purpose
    request.scheduled_at = payload.scheduled_at
    request.place = payload.place
    request.attire = payload.attire
    await session.execute(delete(MeetingRequestInvitee).where(MeetingRequestInvitee.meeting_request_id == request.id))
    session.add_all(
        [
            MeetingRequestInvitee(
                meeting_request_id=request.id,
                name=invitee.name.strip(),
                institution=invitee.institution.strip() if invitee.institution else None,
                sort_order=index,
            )
            for index, invitee in enumerate(payload.invitees, start=1)
        ]
    )
    await session.commit()
    await session.refresh(document)
    await session.refresh(request)
    return document, request, meeting_type


async def meeting_request_view(
    session: AsyncSession,
    document: Document,
    request: MeetingRequest,
    meeting_type: MeetingType,
    actions: list[str] | None = None,
) -> MeetingRequestView:
    version = (
        await session.execute(
            select(DocumentVersion).where(
                DocumentVersion.document_id == document.id,
                DocumentVersion.version_number == document.current_version,
            )
        )
    ).scalar_one()
    payload = MeetingRequestPayload.model_validate(version.content)
    return MeetingRequestView(
        **payload.model_dump(),
        id=request.id,
        document_id=document.id,
        document_status=document.status.value,
        title=document.title,
        meeting_type_name=meeting_type.name,
        current_version=document.current_version,
        lock_version=document.lock_version,
        available_actions=actions or [],
        created_at=document.created_at,
    )


def creator_actions(document: Document) -> list[str]:
    if document.status in {DocumentStatus.DRAFT, DocumentStatus.RETURNED}:
        return ["EDIT", "SUBMIT"]
    return []
