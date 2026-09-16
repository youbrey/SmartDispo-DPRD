from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.entities import DocumentTemplate, DocumentTemplateVersion, DocumentType

TEMPLATE_DEFINITIONS = {
    DocumentType.MEETING_REQUEST: ("MEETING_REQUEST_DPRD", "Permintaan Rapat DPRD", "meeting-request-v1.docx"),
    DocumentType.TRAVEL_REQUEST: (
        "TRAVEL_REQUEST_DPRD",
        "Permintaan Perjalanan Dinas DPRD",
        "travel-request-v1.docx",
    ),
    DocumentType.INCOMING_CHAIRMAN: (
        "DISPOSITION_DPRD",
        "Lembar Disposisi DPRD",
        "disposition-dprd-v1.docx",
    ),
    DocumentType.INCOMING_SECRETARY: (
        "DISPOSITION_SETWAN",
        "Lembar Disposisi Setwan",
        "disposition-setwan-v1.docx",
    ),
}

CODE_TO_TYPE = {definition[0]: document_type for document_type, definition in TEMPLATE_DEFINITIONS.items()}


async def active_template_version(
    session: AsyncSession,
    document_type: DocumentType,
) -> DocumentTemplateVersion | None:
    code = TEMPLATE_DEFINITIONS[document_type][0]
    return (
        await session.execute(
            select(DocumentTemplateVersion)
            .join(DocumentTemplate, DocumentTemplate.id == DocumentTemplateVersion.template_id)
            .where(DocumentTemplate.code == code, DocumentTemplateVersion.active.is_(True))
            .order_by(DocumentTemplateVersion.version.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


def resolve_template_path(version: DocumentTemplateVersion | None, document_type: DocumentType) -> Path:
    settings = get_settings()
    if version:
        if version.object_key.startswith("builtin/"):
            return Path(settings.template_dir) / version.object_key.removeprefix("builtin/")
        return Path(settings.template_upload_dir) / version.object_key.removeprefix("custom/")
    return Path(settings.template_dir) / TEMPLATE_DEFINITIONS[document_type][2]


def resolve_version_path(version: DocumentTemplateVersion) -> Path:
    settings = get_settings()
    if version.object_key.startswith("builtin/"):
        return Path(settings.template_dir) / version.object_key.removeprefix("builtin/")
    return Path(settings.template_upload_dir) / version.object_key.removeprefix("custom/")
