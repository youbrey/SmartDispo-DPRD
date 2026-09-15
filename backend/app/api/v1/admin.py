from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser, SessionDep, require_permission
from app.models.entities import (
    Document,
    DocumentType,
    WorkflowDefinition,
    WorkflowState,
    WorkflowStep,
)
from app.schemas.common import WorkflowCreate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
async def dashboard(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("admin.dashboard.read")),
) -> dict:
    by_status = dict((await session.execute(select(Document.status, func.count()).group_by(Document.status))).all())
    return {"documents": {key.value: value for key, value in by_status.items()}}


@router.post("/workflows", status_code=201)
async def create_workflow(
    payload: WorkflowCreate,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("workflow.manage")),
) -> dict:
    try:
        document_type = DocumentType(payload.document_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Jenis dokumen tidak valid") from exc
    latest = (
        await session.execute(
            select(func.max(WorkflowDefinition.version)).where(WorkflowDefinition.document_type == document_type)
        )
    ).scalar() or 0
    definition = WorkflowDefinition(
        name=payload.name,
        document_type=document_type,
        version=latest + 1,
        state=WorkflowState.DRAFT,
    )
    session.add(definition)
    await session.flush()
    for index, data in enumerate(payload.steps):
        session.add(
            WorkflowStep(
                definition_id=definition.id,
                step_key=data["step_key"],
                name=data["name"],
                sort_order=index,
                assignment_rule=data.get("assignment_rule", {}),
                allowed_actions=data.get("allowed_actions", []),
                completion_rule=data.get("completion_rule", "ALL"),
                return_step_key=data.get("return_step_key"),
            )
        )
    await session.commit()
    return {"id": str(definition.id), "version": definition.version, "state": definition.state.value}


@router.post("/workflows/{workflow_id}/publish")
async def publish_workflow(
    workflow_id: UUID,
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("workflow.manage")),
) -> dict:
    definition = await session.get(WorkflowDefinition, workflow_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Workflow tidak ditemukan")
    await session.execute(
        WorkflowDefinition.__table__.update()
        .where(
            WorkflowDefinition.document_type == definition.document_type,
            WorkflowDefinition.state == WorkflowState.PUBLISHED,
        )
        .values(state=WorkflowState.RETIRED)
    )
    definition.state = WorkflowState.PUBLISHED
    await session.commit()
    return {"id": str(definition.id), "state": definition.state.value}
