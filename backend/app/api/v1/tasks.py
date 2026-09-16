from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import or_, select

from app.core.dependencies import CurrentUser, SessionDep, ensure_active_device
from app.models.entities import Document, TaskStatus, UserRole, WorkflowInstance, WorkflowTask
from app.schemas.common import TaskActionRequest
from app.services.workflows import execute_task_action

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/mine")
async def my_tasks(session: SessionDep, user: CurrentUser) -> list[dict]:
    role_ids = select(UserRole.role_id).where(UserRole.user_id == user.id)
    query = (
        select(WorkflowTask, WorkflowInstance.lock_version, Document)
        .join(WorkflowInstance, WorkflowInstance.id == WorkflowTask.instance_id)
        .join(Document, Document.id == WorkflowInstance.document_id)
        .where(
            or_(WorkflowTask.assignee_user_id == user.id, WorkflowTask.assignee_role_id.in_(role_ids)),
            WorkflowTask.status.in_([TaskStatus.PENDING, TaskStatus.OPENED]),
        )
        .order_by(WorkflowTask.created_at.desc())
    )
    return [
        {
            "id": str(task.id),
            "document_id": str(document.id),
            "document_title": document.title,
            "document_type": document.document_type.value,
            "step_key": task.step_key,
            "status": task.status.value,
            "available_actions": task.available_actions,
            "instance_lock_version": lock_version,
            "created_at": task.created_at,
        }
        for task, lock_version, document in (await session.execute(query)).all()
    ]


@router.post("/{task_id}/actions")
async def action(
    task_id: UUID, payload: TaskActionRequest, request: Request, session: SessionDep, user: CurrentUser
) -> dict:
    action_name = payload.action.upper()
    header_device = request.headers.get("X-Device-ID")
    if action_name in {"SIGN", "VERIFY", "COORDINATE", "APPROVE", "DISPOSITION"}:
        if payload.device_id and payload.device_id != header_device:
            raise HTTPException(status_code=422, detail="Identitas perangkat tidak cocok")
        await ensure_active_device(session, user.id, header_device)
    task = await execute_task_action(
        session,
        task_id,
        user.id,
        payload.action,
        payload.note,
        payload.expected_instance_lock_version,
        header_device,
        request.client.host if request.client else None,
    )
    return {"id": str(task.id), "status": task.status.value}
