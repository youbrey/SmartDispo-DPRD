from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import has_permission
from app.models.entities import Document, UserRole, WorkflowInstance, WorkflowTask


async def ensure_document_access(session: AsyncSession, document: Document, user_id: UUID) -> None:
    if document.created_by == user_id or await has_permission(session, user_id, "document.read"):
        return
    assigned = (
        await session.execute(
            select(WorkflowTask.id)
            .join(WorkflowInstance, WorkflowInstance.id == WorkflowTask.instance_id)
            .where(
                WorkflowInstance.document_id == document.id,
                (
                    (WorkflowTask.assignee_user_id == user_id)
                    | (WorkflowTask.assignee_role_id.in_(select(UserRole.role_id).where(UserRole.user_id == user_id)))
                ),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if not assigned:
        raise HTTPException(status_code=403, detail="Izin tidak mencukupi")
