from datetime import date
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    Disposition,
    DispositionSheet,
    DispositionTarget,
    Document,
    DocumentStatus,
    DocumentVersion,
    Role,
    RoleAssignment,
    TaskStatus,
    UserRole,
    WorkflowInstance,
    WorkflowTask,
)
from app.schemas.common import DispositionCreate, DispositionTargetInput, DispositionView
from app.services.audit import record_audit
from app.services.documents import canonical_hash

DPRD_DIRECTIVES = {
    "FORWARD_COMMISSION_I",
    "FORWARD_COMMISSION_II",
    "FORWARD_COMMISSION_III",
    "FORWARD_BAPEMPERDA",
    "FORWARD_BANGGAR",
    "FORWARD_PANSUS",
    "FOLLOW_UP",
    "ACKNOWLEDGE",
    "REMIND",
    "POSTPONE_CANCEL",
    "ARCHIVE",
    "CREATE_SPT",
    "CREATE_SPD",
    "CREATE_RECOMMENDATION",
    "CREATE_APPROVAL",
    "CREATE_SPEECH",
    "STUDY_RESEARCH",
    "APPROVED",
    "SCHEDULE",
    "REPRESENTED_BY",
    "PROCESS_BY_MECHANISM",
    "ADJUST_BUDGET",
    "COORDINATE_CONFIRM",
    "COPY_MULTIPLY",
    "CREATE_INVITATION",
    "CREATE_DESTINATION_NOTICE",
    "FORWARD_GENERAL_FINANCE",
    "FORWARD_LEGISLATION_SESSION_PUBLIC_RELATIONS",
    "FORWARD_FACILITATION_BUDGET_OVERSIGHT",
}
SETWAN_DIRECTIVES = {
    "FURTHER_PROCESS",
    "CREATE_REVIEW_ADVICE",
    "COORDINATE",
    "STUDY_REPORT",
    "MONITOR_INPUT",
    "CONSIDER",
    "GUIDANCE",
    "PREPARE_MATERIAL",
    "ATTENTION",
    "ACKNOWLEDGE",
    "CREATE_SPT",
    "CREATE_SPD",
    "FILE",
}


async def create_disposition(
    session: AsyncSession, document_id: UUID, payload: DispositionCreate, user_id: UUID
) -> DispositionView:
    document = (
        await session.execute(select(Document).where(Document.id == document_id).with_for_update())
    ).scalar_one_or_none()
    sheet = (
        await session.execute(select(DispositionSheet).where(DispositionSheet.document_id == document_id))
    ).scalar_one_or_none()
    if not document or not sheet:
        raise HTTPException(status_code=404, detail="Lembar disposisi tidak ditemukan")
    if document.status != DocumentStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="Disposisi hanya dapat dibuat saat dokumen sedang diproses")
    actor_role = payload.actor_role.upper()
    permitted_roles = {"CHAIRMAN", "SEKWAN"} if sheet.sheet_type == "DISPOSITION_DPRD" else {"SEKWAN"}
    if actor_role not in permitted_roles:
        raise HTTPException(status_code=422, detail="Role aktor tidak sesuai jenis lembar disposisi")
    today = date.today()
    officeholder = (
        await session.execute(
            select(RoleAssignment.id)
            .join(Role, Role.id == RoleAssignment.role_id)
            .where(
                RoleAssignment.user_id == user_id,
                Role.code == actor_role,
                RoleAssignment.active.is_(True),
                RoleAssignment.valid_from <= today,
                (RoleAssignment.valid_until.is_(None) | (RoleAssignment.valid_until >= today)),
            )
        )
    ).scalar_one_or_none()
    if not officeholder:
        raise HTTPException(status_code=403, detail="Akun bukan pejabat aktif untuk disposisi ini")
    role_ids = select(UserRole.role_id).where(UserRole.user_id == user_id)
    tasks = list(
        (
            await session.execute(
                select(WorkflowTask)
                .join(WorkflowInstance, WorkflowInstance.id == WorkflowTask.instance_id)
                .where(
                    WorkflowInstance.document_id == document_id,
                    WorkflowTask.status.in_([TaskStatus.PENDING, TaskStatus.OPENED]),
                    ((WorkflowTask.assignee_user_id == user_id) | (WorkflowTask.assignee_role_id.in_(role_ids))),
                )
            )
        ).scalars()
    )
    if not any("DISPOSITION" in task.available_actions for task in tasks):
        raise HTTPException(status_code=403, detail="Tidak ada task disposisi aktif untuk akun ini")
    allowed = DPRD_DIRECTIVES if sheet.sheet_type == "DISPOSITION_DPRD" else SETWAN_DIRECTIVES
    if sheet.sheet_type == "DISPOSITION_DPRD":
        additional = {
            "FORWARD_GENERAL_FINANCE",
            "FORWARD_LEGISLATION_SESSION_PUBLIC_RELATIONS",
            "FORWARD_FACILITATION_BUDGET_OVERSIGHT",
        }
        allowed = additional if actor_role == "SEKWAN" else DPRD_DIRECTIVES - additional
    invalid = set(payload.directives) - allowed
    if invalid:
        raise HTTPException(status_code=422, detail=f"Pilihan disposisi tidak valid: {', '.join(sorted(invalid))}")
    disposition = Disposition(
        sheet_id=sheet.id,
        created_by=user_id,
        actor_role=actor_role,
        directives=payload.directives,
        note=payload.note,
    )
    session.add(disposition)
    await session.flush()
    for target in payload.targets:
        session.add(
            DispositionTarget(
                disposition_id=disposition.id,
                unit_id=target.unit_id,
                role_id=target.role_id,
                user_id=target.user_id,
            )
        )
    sheet.structured_data = {
        **sheet.structured_data,
        actor_role: {"directives": payload.directives, "note": payload.note},
    }
    current_version = (
        await session.execute(
            select(DocumentVersion).where(
                DocumentVersion.document_id == document.id,
                DocumentVersion.version_number == document.current_version,
            )
        )
    ).scalar_one()
    version_content = {**current_version.content, "dispositions": sheet.structured_data}
    document.current_version += 1
    document.lock_version += 1
    session.add(
        DocumentVersion(
            document_id=document.id,
            version_number=document.current_version,
            content=version_content,
            sha256_hash=canonical_hash(version_content),
            created_by=user_id,
            change_reason=f"Disposisi {actor_role}",
            template_version_id=current_version.template_version_id,
        )
    )
    record_audit(
        session,
        actor_user_id=user_id,
        action="DISPOSITION_CREATED",
        entity_type="Disposition",
        entity_id=disposition.id,
        after={
            "document_id": str(document_id),
            "document_version": document.current_version,
            "directives": payload.directives,
        },
    )
    await session.commit()
    await session.refresh(disposition)
    return DispositionView(
        id=disposition.id,
        document_id=document_id,
        sheet_type=sheet.sheet_type,
        actor_role=disposition.actor_role,
        directives=disposition.directives,
        note=disposition.note,
        targets=payload.targets,
        created_at=disposition.created_at,
    )


async def list_dispositions(session: AsyncSession, document_id: UUID) -> list[DispositionView]:
    sheet = (
        await session.execute(select(DispositionSheet).where(DispositionSheet.document_id == document_id))
    ).scalar_one_or_none()
    if not sheet:
        raise HTTPException(status_code=404, detail="Lembar disposisi tidak ditemukan")
    query = select(Disposition).where(Disposition.sheet_id == sheet.id).order_by(Disposition.created_at)
    rows = list((await session.execute(query)).scalars())
    result = []
    for row in rows:
        target_query = select(DispositionTarget).where(DispositionTarget.disposition_id == row.id)
        targets = list((await session.execute(target_query)).scalars())
        result.append(
            DispositionView(
                id=row.id,
                document_id=document_id,
                sheet_type=sheet.sheet_type,
                actor_role=row.actor_role,
                directives=row.directives,
                note=row.note,
                targets=[
                    DispositionTargetInput(unit_id=t.unit_id, role_id=t.role_id, user_id=t.user_id) for t in targets
                ],
                created_at=row.created_at,
            )
        )
    return result
