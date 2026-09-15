from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep, require_permission
from app.models.entities import Document, WorkflowInstance, WorkflowTask
from app.schemas.common import DocumentCreate, DocumentUpdate, DocumentView
from app.services.documents import create_document, update_document
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


@router.get("/{document_id}", response_model=DocumentView)
async def get(document_id: UUID, session: SessionDep, user: CurrentUser) -> DocumentView:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    actions: list[str] = []
    task_query = (
        select(WorkflowTask.available_actions)
        .join(WorkflowInstance, WorkflowInstance.id == WorkflowTask.instance_id)
        .where(
            WorkflowInstance.document_id == document_id,
            WorkflowTask.assignee_user_id == user.id,
        )
    )
    for task_actions in (await session.execute(task_query)).scalars():
        actions.extend(task_actions)
    if document.created_by == user.id and document.status.value in {"DRAFT", "RETURNED"}:
        actions.extend(["EDIT", "SUBMIT"])
    return view(document, sorted(set(actions)))


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
