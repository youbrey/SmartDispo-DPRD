from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Document, DocumentStatus, DocumentVersion, TravelRequest, TravelRequestMember
from app.schemas.common import (
    DocumentCreate,
    DocumentUpdate,
    TravelRequestCreate,
    TravelRequestPayload,
    TravelRequestUpdate,
    TravelRequestView,
)
from app.services.documents import add_document, update_document

ACTIVITY_NAMES = {
    "CONSULTATION": "Konsultasi",
    "WORK_VISIT": "Kunjungan Kerja",
}


def travel_content(payload: TravelRequestPayload) -> dict:
    content = TravelRequestPayload.model_validate(payload.model_dump()).model_dump(mode="json")
    content["activity_type_name"] = ACTIVITY_NAMES[payload.activity_type]
    content["recipient"] = "PIMPINAN DPRD KOTA BITUNG"
    content["subject"] = "Permintaan Kunjungan Kerja / Konsultasi"
    content["duration_days"] = (payload.end_date - payload.start_date).days + 1
    return content


def _member_rows(request_id: UUID, payload: TravelRequestPayload) -> list[TravelRequestMember]:
    group_order = {"EXECUTOR": 0, "ACCOMPANYING": 0}
    rows = []
    for member in payload.members:
        group_order[member.member_group] += 1
        rows.append(
            TravelRequestMember(
                travel_request_id=request_id,
                name=member.name.strip(),
                position=member.position.strip() if member.position else None,
                member_group=member.member_group,
                sort_order=group_order[member.member_group],
            )
        )
    return rows


async def create_travel_request(
    session: AsyncSession,
    payload: TravelRequestCreate,
    user_id: UUID,
) -> tuple[Document, TravelRequest]:
    activity_name = ACTIVITY_NAMES[payload.activity_type]
    document = await add_document(
        session,
        DocumentCreate(
            document_type="TRAVEL_REQUEST",
            title=f"Permintaan {activity_name} - {payload.destinations[0]}",
            content=travel_content(payload),
        ),
        user_id,
    )
    request = TravelRequest(
        document_id=document.id,
        activity_type=payload.activity_type,
        destination="; ".join(payload.destinations),
        purpose=payload.purpose,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    session.add(request)
    await session.flush()
    session.add_all(_member_rows(request.id, payload))
    await session.commit()
    await session.refresh(document)
    await session.refresh(request)
    return document, request


async def update_travel_request(
    session: AsyncSession,
    document_id: UUID,
    payload: TravelRequestUpdate,
    user_id: UUID,
) -> tuple[Document, TravelRequest]:
    request = (
        await session.execute(select(TravelRequest).where(TravelRequest.document_id == document_id))
    ).scalar_one_or_none()
    document = await session.get(Document, document_id)
    if not request or not document:
        raise HTTPException(status_code=404, detail="Permintaan perjalanan dinas tidak ditemukan")
    if document.created_by != user_id:
        raise HTTPException(status_code=403, detail="Hanya pembuat yang dapat mengubah permintaan")
    activity_name = ACTIVITY_NAMES[payload.activity_type]
    document = await update_document(
        session,
        document_id,
        DocumentUpdate(
            title=f"Permintaan {activity_name} - {payload.destinations[0]}",
            content=travel_content(payload),
            expected_lock_version=payload.expected_lock_version,
            change_reason=payload.change_reason,
        ),
        user_id,
        commit=False,
    )
    request.activity_type = payload.activity_type
    request.destination = "; ".join(payload.destinations)
    request.purpose = payload.purpose
    request.start_date = payload.start_date
    request.end_date = payload.end_date
    await session.execute(delete(TravelRequestMember).where(TravelRequestMember.travel_request_id == request.id))
    session.add_all(_member_rows(request.id, payload))
    await session.commit()
    await session.refresh(document)
    await session.refresh(request)
    return document, request


async def travel_request_view(
    session: AsyncSession,
    document: Document,
    request: TravelRequest,
    actions: list[str] | None = None,
) -> TravelRequestView:
    version = (
        await session.execute(
            select(DocumentVersion).where(
                DocumentVersion.document_id == document.id,
                DocumentVersion.version_number == document.current_version,
            )
        )
    ).scalar_one()
    payload = TravelRequestPayload.model_validate(version.content)
    return TravelRequestView(
        **payload.model_dump(),
        id=request.id,
        document_id=document.id,
        document_status=document.status.value,
        title=document.title,
        duration_days=(payload.end_date - payload.start_date).days + 1,
        current_version=document.current_version,
        lock_version=document.lock_version,
        available_actions=actions or [],
        created_at=document.created_at,
    )


def creator_actions(document: Document) -> list[str]:
    if document.status in {DocumentStatus.DRAFT, DocumentStatus.RETURNED}:
        return ["EDIT", "SUBMIT", "PREVIEW"]
    return ["PREVIEW"]
