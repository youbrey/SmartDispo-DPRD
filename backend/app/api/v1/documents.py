from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import or_, select

from app.core.dependencies import CurrentUser, SessionDep, has_permission, require_permission
from app.models.entities import (
    Approval,
    Document,
    DocumentStatus,
    DocumentType,
    DocumentVersion,
    Role,
    TaskStatus,
    User,
    UserRole,
    WorkflowInstance,
    WorkflowTask,
)
from app.schemas.common import DocumentCreate, DocumentUpdate, DocumentView
from app.services.access import ensure_document_access
from app.services.documents import create_document, update_document
from app.services.rendering import generate_document
from app.services.workflows import submit_document

router = APIRouter(prefix="/documents", tags=["documents"])


def view(document: Document, actions: list[str] | None = None) -> DocumentView:
    return DocumentView(
        id=document.id,
        document_number=document.document_number,
        agenda_number=document.agenda_number,
        document_type=document.document_type.value,
        status=document.status.value,
        title=document.title,
        current_version=document.current_version,
        current_step_key=document.current_step_key,
        lock_version=document.lock_version,
        available_actions=actions or [],
        created_at=document.created_at,
    )


@router.post("", response_model=DocumentView, status_code=201)
async def create(
    payload: DocumentCreate,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("document.create")),
) -> DocumentView:
    return view(await create_document(session, payload, user.id), ["EDIT", "SUBMIT"])


@router.get("", response_model=list[DocumentView])
async def list_documents(
    session: SessionDep,
    user: CurrentUser,
    document_type: DocumentType | None = None,
    status: DocumentStatus | None = None,
    q: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DocumentView]:
    query = select(Document)
    if not await has_permission(session, user.id, "document.read"):
        role_ids = select(UserRole.role_id).where(UserRole.user_id == user.id)
        assigned_document_ids = (
            select(WorkflowInstance.document_id)
            .join(WorkflowTask, WorkflowTask.instance_id == WorkflowInstance.id)
            .where(or_(WorkflowTask.assignee_user_id == user.id, WorkflowTask.assignee_role_id.in_(role_ids)))
        )
        query = query.where(or_(Document.created_by == user.id, Document.id.in_(assigned_document_ids)))
    if document_type:
        query = query.where(Document.document_type == document_type)
    if status:
        query = query.where(Document.status == status)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(
                Document.title.ilike(pattern),
                Document.document_number.ilike(pattern),
                Document.agenda_number.ilike(pattern),
            )
        )
    documents = list((await session.execute(query.order_by(Document.created_at.desc()).limit(limit))).scalars())
    return [
        view(
            document,
            ["EDIT", "SUBMIT"]
            if document.created_by == user.id and document.status in {DocumentStatus.DRAFT, DocumentStatus.RETURNED}
            else [],
        )
        for document in documents
    ]


@router.get("/{document_id}", response_model=DocumentView)
async def get(document_id: UUID, session: SessionDep, user: CurrentUser) -> DocumentView:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    await ensure_document_access(session, document, user.id)
    actions: list[str] = []
    task_query = (
        select(WorkflowTask.available_actions)
        .join(WorkflowInstance, WorkflowInstance.id == WorkflowTask.instance_id)
        .where(
            WorkflowInstance.document_id == document_id,
            or_(
                WorkflowTask.assignee_user_id == user.id,
                WorkflowTask.assignee_role_id.in_(select(UserRole.role_id).where(UserRole.user_id == user.id)),
            ),
            WorkflowTask.status.in_([TaskStatus.PENDING, TaskStatus.OPENED]),
        )
    )
    for task_actions in (await session.execute(task_query)).scalars():
        actions.extend(task_actions)
    if document.created_by == user.id and document.status.value in {"DRAFT", "RETURNED"}:
        actions.extend(["EDIT", "SUBMIT"])
    return view(document, sorted(set(actions)))


@router.get("/{document_id}/timeline")
async def timeline(document_id: UUID, session: SessionDep, user: CurrentUser) -> list[dict]:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    await ensure_document_access(session, document, user.id)
    entries: list[dict] = [
        {
            "id": str(version.id),
            "event_type": "DOCUMENT_VERSION",
            "title": f"Versi {version.version_number} dibuat",
            "actor_name": creator_name,
            "note": version.change_reason,
            "occurred_at": version.created_at,
        }
        for version, creator_name in (
            await session.execute(
                select(DocumentVersion, User.full_name)
                .join(User, User.id == DocumentVersion.created_by)
                .where(DocumentVersion.document_id == document_id)
            )
        ).all()
    ]
    entries.extend(
        {
            "id": str(approval.id),
            "event_type": approval.action,
            "title": approval.action.replace("_", " ").title(),
            "actor_name": actor_name,
            "note": approval.note,
            "occurred_at": approval.occurred_at,
        }
        for approval, actor_name in (
            await session.execute(
                select(Approval, User.full_name)
                .join(User, User.id == Approval.user_id)
                .where(Approval.document_id == document_id)
            )
        ).all()
    )
    entries.extend(
        {
            "id": str(task.id),
            "event_type": "TASK_COMPLETED",
            "title": f"Tahap {task.step_key.replace('_', ' ').title()} selesai",
            "actor_name": actor_name or role_name or "Sistem",
            "note": None,
            "occurred_at": task.completed_at,
        }
        for task, actor_name, role_name in (
            await session.execute(
                select(WorkflowTask, User.full_name, Role.name)
                .join(WorkflowInstance, WorkflowInstance.id == WorkflowTask.instance_id)
                .outerjoin(User, User.id == WorkflowTask.assignee_user_id)
                .outerjoin(Role, Role.id == WorkflowTask.assignee_role_id)
                .where(
                    WorkflowInstance.document_id == document_id,
                    WorkflowTask.completed_at.is_not(None),
                )
            )
        ).all()
    )
    return sorted(entries, key=lambda item: item["occurred_at"])


@router.patch("/{document_id}", response_model=DocumentView)
async def update(
    document_id: UUID,
    payload: DocumentUpdate,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("document.edit")),
) -> DocumentView:
    return view(await update_document(session, document_id, payload, user.id), ["EDIT", "SUBMIT"])


@router.post("/{document_id}/submit", response_model=DocumentView)
async def submit(
    document_id: UUID,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("document.submit")),
) -> DocumentView:
    return view(await submit_document(session, document_id, user.id))


@router.get("/{document_id}/generated-docx")
async def generated_docx(document_id: UUID, session: SessionDep, user: CurrentUser) -> FileResponse:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    await ensure_document_access(session, document, user.id)
    path = await generate_document(session, document_id)
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.get("/{document_id}/preview")
async def preview(document_id: UUID, session: SessionDep, user: CurrentUser) -> FileResponse:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    await ensure_document_access(session, document, user.id)
    path = await generate_document(session, document_id, pdf=True)
    return FileResponse(path, media_type="application/pdf")
