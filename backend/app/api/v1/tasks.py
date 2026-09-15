from uuid import UUID

from fastapi import APIRouter, Request
from sqlalchemy import or_, select

from app.core.dependencies import CurrentUser, SessionDep
from app.models.entities import TaskStatus, UserRole, WorkflowInstance, WorkflowTask
from app.schemas.common import TaskActionRequest
from app.services.workflows import execute_task_action

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/mine")
async def my_tasks(session: SessionDep, user: CurrentUser) -> list[dict]:
    role_ids = select(UserRole.role_id).where(UserRole.user_id == user.id)
    query = (
        select(WorkflowTask, WorkflowInstance.lock_version)
        .join(WorkflowInstance, WorkflowInstance.id == WorkflowTask.instance_id)
        .where(
            or_(WorkflowTask.assignee_user_id == user.id, WorkflowTask.assignee_role_id.in_(role_ids)),
            WorkflowTask.status.in_([TaskStatus.PENDING, TaskStatus.OPENED]),
        )
        .order_by(WorkflowTask.created_at.desc())
    )
    return [
        {
            "id": str(task.id),
            "step_key": task.step_key,
            "status": task.status.value,
            "available_actions": task.available_actions,
            "instance_lock_version": lock_version,
            "created_at": task.created_at,
        }
        for task, lock_version in (await session.execute(query)).all()
    ]


@router.post("/{task_id}/actions")
async def action(
    task_id: UUID, payload: TaskActionRequest, request: Request, session: SessionDep, user: CurrentUser
) -> dict:
    task = await execute_task_action(
        session,
        task_id,
        user.id,
        payload.action,
        payload.note,
        payload.expected_instance_lock_version,
        payload.device_id,
        request.client.host if request.client else None,
    )
    return {"id": str(task.id), "status": task.status.value}
