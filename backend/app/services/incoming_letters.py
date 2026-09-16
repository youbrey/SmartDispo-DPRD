from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AgendaEntry, DispositionSheet, Document, IncomingLetter
from app.schemas.common import DocumentCreate, IncomingLetterCreate, IncomingLetterView
from app.services.documents import add_document


def incoming_content(payload: IncomingLetterCreate) -> dict:
    content = payload.model_dump(mode="json")
    content["sheet_type"] = f"DISPOSITION_{payload.route_type}"
    return content


async def create_incoming_letter(
    session: AsyncSession, payload: IncomingLetterCreate, user_id: UUID
) -> tuple[Document, IncomingLetter]:
    document = await add_document(
        session,
        DocumentCreate(
            document_type="INCOMING_CHAIRMAN" if payload.route_type == "DPRD" else "INCOMING_SECRETARY",
            title=f"Surat Masuk - {payload.subject[:120]}",
            content=incoming_content(payload),
        ),
        user_id,
    )
    document.agenda_number = payload.agenda_number
    letter = IncomingLetter(
        document_id=document.id,
        sender=payload.sender.strip(),
        letter_number=payload.letter_number.strip(),
        letter_date=payload.letter_date,
        received_date=payload.received_date,
        subject=payload.subject.strip(),
        priority=payload.priority,
    )
    session.add_all(
        [
            letter,
            AgendaEntry(
                document_id=document.id,
                agenda_number=payload.agenda_number.strip(),
                agenda_date=payload.agenda_date,
                created_by=user_id,
            ),
            DispositionSheet(
                document_id=document.id,
                sheet_type=f"DISPOSITION_{payload.route_type}",
                structured_data={},
            ),
        ]
    )
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Nomor agenda sudah digunakan") from exc
    await session.refresh(document)
    await session.refresh(letter)
    return document, letter


async def incoming_letter_view(
    session: AsyncSession, document: Document, letter: IncomingLetter, actions: list[str] | None = None
) -> IncomingLetterView:
    agenda = (await session.execute(select(AgendaEntry).where(AgendaEntry.document_id == document.id))).scalar_one()
    return IncomingLetterView(
        route_type="DPRD" if document.document_type.value == "INCOMING_CHAIRMAN" else "SETWAN",
        sender=letter.sender,
        letter_number=letter.letter_number,
        letter_date=letter.letter_date,
        received_date=letter.received_date,
        agenda_number=agenda.agenda_number,
        agenda_date=agenda.agenda_date,
        subject=letter.subject,
        priority=letter.priority,
        notes=None,
        document_id=document.id,
        document_status=document.status.value,
        title=document.title,
        current_version=document.current_version,
        lock_version=document.lock_version,
        available_actions=actions or [],
        created_at=document.created_at,
    )
