import secrets
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.dependencies import SessionDep
from app.models.entities import Document, DocumentStatus, DocumentType, DocumentVersion, IntegrationEvent

router = APIRouter(prefix="/integrations/sips", tags=["SIPS integration"])


class SipsEvent(BaseModel):
    event_uuid: UUID
    event_type: str = Field(min_length=2, max_length=100)
    aggregate_id: UUID
    payload: dict = Field(default_factory=dict)


def _authenticate(api_key: str | None) -> None:
    configured = get_settings().sips_api_key
    if not configured or not api_key or not secrets.compare_digest(configured, api_key):
        raise HTTPException(status_code=401, detail="Kredensial SIPS tidak valid")


@router.get("/completed-travel-requests")
async def completed_travel_requests(
    session: SessionDep,
    x_sips_api_key: str | None = Header(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    _authenticate(x_sips_api_key)
    rows = (
        await session.execute(
            select(Document, DocumentVersion)
            .join(
                DocumentVersion,
                (DocumentVersion.document_id == Document.id)
                & (DocumentVersion.version_number == Document.current_version),
            )
            .where(
                Document.document_type == DocumentType.TRAVEL_REQUEST,
                Document.status == DocumentStatus.COMPLETED,
            )
            .order_by(Document.updated_at.desc())
            .limit(limit)
        )
    ).all()
    return [
        {
            "document_id": str(document.id),
            "document_number": document.document_number,
            "version": document.current_version,
            "sha256_hash": version.sha256_hash,
            "completed_at": document.updated_at,
            "data": version.content,
        }
        for document, version in rows
    ]


@router.post("/events", status_code=202)
async def receive_event(
    payload: SipsEvent,
    session: SessionDep,
    x_sips_api_key: str | None = Header(default=None),
) -> dict:
    _authenticate(x_sips_api_key)
    existing = (
        await session.execute(select(IntegrationEvent).where(IntegrationEvent.event_uuid == payload.event_uuid))
    ).scalar_one_or_none()
    if existing:
        return {"event_uuid": str(existing.event_uuid), "accepted": True, "duplicate": True}
    event = IntegrationEvent(
        event_uuid=payload.event_uuid,
        event_type=payload.event_type,
        aggregate_id=payload.aggregate_id,
        payload=payload.payload,
        delivered_at=datetime.now(UTC),
        attempts=1,
    )
    session.add(event)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return {"event_uuid": str(payload.event_uuid), "accepted": True, "duplicate": True}
    return {"event_uuid": str(payload.event_uuid), "accepted": True, "duplicate": False}
