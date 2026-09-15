from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    Approval,
    Document,
    DocumentStatus,
    DocumentVersion,
    TaskStatus,
    UserRole,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowState,
    WorkflowStep,
    WorkflowTask,
)
from app.services.audit import record_audit

APPROVAL_ACTIONS = {"SIGN", "VERIFY", "COORDINATE", "APPROVE", "DISPOSITION"}


def create_step_tasks(session: AsyncSession, instance_id: UUID, step: WorkflowStep) -> None:
    rule = step.assignment_rule
    user_ids = [*rule.get("user_ids", [])]
    role_ids = [*rule.get("role_ids", [])]
    if rule.get("user_id"):
        user_ids.append(rule["user_id"])
    if rule.get("role_id"):
        role_ids.append(rule["role_id"])
    if not user_ids and not role_ids:
        raise HTTPException(status_code=409, detail=f"Assignment step {step.step_key} belum dikonfigurasi")
    for assigned_user_id in user_ids:
        session.add(
            WorkflowTask(
                instance_id=instance_id,
                step_key=step.step_key,
                assignee_user_id=UUID(str(assigned_user_id)),
                available_actions=step.allowed_actions,
            )
        )
    for assigned_role_id in role_ids:
        session.add(
            WorkflowTask(
                instance_id=instance_id,
                step_key=step.step_key,
                assignee_role_id=UUID(str(assigned_role_id)),
                available_actions=step.allowed_actions,
            )
        )


async def submit_document(session: AsyncSession, document_id: UUID, user_id: UUID) -> Document:
    document = (
        await session.execute(select(Document).where(Document.id == document_id).with_for_update())
    ).scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    if document.created_by != user_id:
        raise HTTPException(status_code=403, detail="Hanya pembuat yang dapat mengirim draft")
    if document.status not in {DocumentStatus.DRAFT, DocumentStatus.RETURNED}:
        raise HTTPException(status_code=409, detail="Dokumen sudah dikirim")
    if document.status == DocumentStatus.RETURNED:
        instance = (
            await session.execute(
                select(WorkflowInstance).where(WorkflowInstance.document_id == document.id).with_for_update()
            )
        ).scalar_one()
        target_step = (
            await session.execute(
                select(WorkflowStep).where(
                    WorkflowStep.definition_id == instance.definition_id,
                    WorkflowStep.step_key == document.current_step_key,
                )
            )
        ).scalar_one()
        create_step_tasks(session, instance.id, target_step)
        document.status = DocumentStatus.IN_PROGRESS
        document.lock_version += 1
        instance.lock_version += 1
        record_audit(
            session,
            actor_user_id=user_id,
            action="DOCUMENT_RESUBMITTED",
            entity_type="Document",
            entity_id=document.id,
            after={"step": target_step.step_key, "version": document.current_version},
        )
        await session.commit()
        await session.refresh(document)
        return document
    definition = (
        await session.execute(
            select(WorkflowDefinition)
            .where(
                WorkflowDefinition.document_type == document.document_type,
                WorkflowDefinition.state == WorkflowState.PUBLISHED,
            )
            .order_by(WorkflowDefinition.version.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=409, detail="Workflow aktif belum dikonfigurasi")
    first_step = (
        await session.execute(
            select(WorkflowStep)
            .where(WorkflowStep.definition_id == definition.id)
            .order_by(WorkflowStep.sort_order)
            .limit(1)
        )
    ).scalar_one()
    instance = WorkflowInstance(
        document_id=document.id, definition_id=definition.id, current_step_key=first_step.step_key
    )
    session.add(instance)
    await session.flush()
    create_step_tasks(session, instance.id, first_step)
    document.status = DocumentStatus.IN_PROGRESS
    document.current_step_key = first_step.step_key
    document.lock_version += 1
    record_audit(
        session,
        actor_user_id=user_id,
        action="DOCUMENT_SUBMITTED",
        entity_type="Document",
        entity_id=document.id,
        after={"workflow_definition_id": str(definition.id), "step": first_step.step_key},
    )
    await session.commit()
    await session.refresh(document)
    return document


async def execute_task_action(
    session: AsyncSession,
    task_id: UUID,
    user_id: UUID,
    action: str,
    note: str | None,
    expected_lock: int,
    device_id: str | None,
    ip_address: str | None,
) -> WorkflowTask:
    action = action.upper()
    task = (
        await session.execute(select(WorkflowTask).where(WorkflowTask.id == task_id).with_for_update())
    ).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")
    if task.assignee_user_id and task.assignee_user_id != user_id:
        raise HTTPException(status_code=403, detail="Tugas bukan milik pengguna")
    if task.assignee_role_id:
        membership = (
            await session.execute(
                select(UserRole.id).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == task.assignee_role_id,
                )
            )
        ).scalar_one_or_none()
        if membership is None:
            raise HTTPException(status_code=403, detail="Role pengguna tidak sesuai tugas")
    if task.status not in {TaskStatus.PENDING, TaskStatus.OPENED}:
        raise HTTPException(status_code=409, detail="Tugas sudah diselesaikan")
    if action not in task.available_actions:
        raise HTTPException(status_code=403, detail="Aksi tidak tersedia")
    instance = (
        await session.execute(select(WorkflowInstance).where(WorkflowInstance.id == task.instance_id).with_for_update())
    ).scalar_one()
    if instance.lock_version != expected_lock:
        raise HTTPException(status_code=409, detail="Workflow telah berubah; muat ulang dokumen")
    step = (
        await session.execute(
            select(WorkflowStep).where(
                WorkflowStep.definition_id == instance.definition_id,
                WorkflowStep.step_key == task.step_key,
            )
        )
    ).scalar_one()
    if action == "RETURN" and step.note_required_on_return and not note:
        raise HTTPException(status_code=422, detail="Alasan pengembalian wajib diisi")
    document = (
        await session.execute(select(Document).where(Document.id == instance.document_id).with_for_update())
    ).scalar_one()
    version = (
        await session.execute(
            select(DocumentVersion).where(
                DocumentVersion.document_id == document.id,
                DocumentVersion.version_number == document.current_version,
            )
        )
    ).scalar_one()
    now = datetime.now(UTC)
    if action in APPROVAL_ACTIONS:
        session.add(
            Approval(
                document_id=document.id,
                document_version=document.current_version,
                document_hash=version.sha256_hash,
                user_id=user_id,
                role_code="TASK_ASSIGNEE",
                action=action,
                note=note,
                occurred_at=now,
                device_id=device_id,
                ip_address=ip_address,
            )
        )
    task.status = TaskStatus.RETURNED if action == "RETURN" else TaskStatus.COMPLETED
    task.completed_at = now
    instance.lock_version += 1
    document.lock_version += 1
    if action == "RETURN":
        document.status = DocumentStatus.RETURNED
        document.current_step_key = step.return_step_key
    else:
        pending_sibling = (
            (
                await session.execute(
                    select(WorkflowTask.id).where(
                        WorkflowTask.instance_id == instance.id,
                        WorkflowTask.step_key == step.step_key,
                        WorkflowTask.id != task.id,
                        WorkflowTask.status.in_([TaskStatus.PENDING, TaskStatus.OPENED]),
                    )
                )
            )
            .scalars()
            .all()
        )
        if step.completion_rule in {"ALL", "SELECTED"} and pending_sibling:
            record_audit(
                session,
                actor_user_id=user_id,
                action=f"TASK_{action}",
                entity_type="WorkflowTask",
                entity_id=task.id,
                after={"step": step.step_key, "waiting_for": len(pending_sibling)},
            )
            await session.commit()
            await session.refresh(task)
            return task
        if step.completion_rule == "ANY" and pending_sibling:
            await session.execute(
                WorkflowTask.__table__.update()
                .where(WorkflowTask.id.in_(pending_sibling))
                .values(status=TaskStatus.CANCELLED)
            )
        next_step = (
            await session.execute(
                select(WorkflowStep)
                .where(
                    WorkflowStep.definition_id == instance.definition_id,
                    WorkflowStep.sort_order > step.sort_order,
                )
                .order_by(WorkflowStep.sort_order)
                .limit(1)
            )
        ).scalar_one_or_none()
        if next_step:
            instance.current_step_key = next_step.step_key
            document.current_step_key = next_step.step_key
            create_step_tasks(session, instance.id, next_step)
        else:
            document.status = DocumentStatus.COMPLETED
            document.current_step_key = None
            instance.completed_at = now
    record_audit(
        session,
        actor_user_id=user_id,
        action=f"TASK_{action}",
        entity_type="WorkflowTask",
        entity_id=task.id,
        after={"document_id": str(document.id), "document_version": document.current_version},
        ip_address=ip_address,
    )
    await session.commit()
    await session.refresh(task)
    return task
