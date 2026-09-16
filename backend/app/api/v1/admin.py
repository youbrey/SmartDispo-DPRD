from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import UUID
from zipfile import BadZipFile, ZipFile

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.dependencies import CurrentUser, SessionDep, require_permission
from app.core.security import hash_password
from app.models.entities import (
    AuditLog,
    ChatMember,
    ChatRoom,
    Document,
    DocumentTemplate,
    DocumentTemplateVersion,
    DocumentType,
    OrganizationalUnit,
    Permission,
    Role,
    RoleAssignment,
    RolePermission,
    User,
    UserRole,
    WorkflowDefinition,
    WorkflowState,
    WorkflowStep,
)
from app.schemas.common import WorkflowCreate
from app.services.audit import record_audit
from app.services.templates import CODE_TO_TYPE, resolve_version_path

router = APIRouter(prefix="/admin", tags=["admin"])
WORKFLOW_ACTIONS = {
    "CREATE",
    "EDIT",
    "SUBMIT",
    "SIGN",
    "VERIFY",
    "COORDINATE",
    "APPROVE",
    "RETURN",
    "REJECT",
    "DISPOSITION",
    "FORWARD",
    "COMPLETE",
}


class UserCreate(BaseModel):
    username: str = Field(pattern=r"^[a-zA-Z0-9._-]{3,80}$")
    full_name: str = Field(min_length=2, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    unit_id: UUID | None = None
    access_level: int = Field(default=10, ge=0, le=1000)
    role_ids: list[UUID] = Field(default_factory=list)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    unit_id: UUID | None = None
    access_level: int | None = Field(default=None, ge=0, le=1000)
    active: bool | None = None


class PasswordReset(BaseModel):
    password: str = Field(min_length=12, max_length=128)


class RoleCreate(BaseModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{1,79}$")
    name: str = Field(min_length=2, max_length=160)
    permission_ids: list[UUID] = Field(default_factory=list)


class RolePermissionsUpdate(BaseModel):
    permission_ids: list[UUID]


class UserRolesUpdate(BaseModel):
    role_ids: list[UUID]


class UnitCreate(BaseModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_-]{1,49}$")
    name: str = Field(min_length=2, max_length=255)
    parent_id: UUID | None = None


class AssignmentCreate(BaseModel):
    role_id: UUID
    user_id: UUID
    unit_id: UUID | None = None
    valid_from: date
    valid_until: date | None = None
    metadata: dict = Field(default_factory=dict)


def _user_dict(user: User, role_codes: list[str] | None = None) -> dict:
    return {
        "id": str(user.id),
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "unit_id": str(user.unit_id) if user.unit_id else None,
        "access_level": user.access_level,
        "active": user.active,
        "roles": role_codes or [],
        "created_at": user.created_at,
    }


@router.get("/dashboard")
async def dashboard(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("admin.dashboard.read")),
) -> dict:
    by_status = dict((await session.execute(select(Document.status, func.count()).group_by(Document.status))).all())
    users = (await session.execute(select(func.count()).select_from(User).where(User.active.is_(True)))).scalar_one()
    workflows = (
        await session.execute(
            select(func.count())
            .select_from(WorkflowDefinition)
            .where(WorkflowDefinition.state == WorkflowState.PUBLISHED)
        )
    ).scalar_one()
    return {
        "documents": {key.value: value for key, value in by_status.items()},
        "active_users": users,
        "published_workflows": workflows,
    }


@router.get("/users")
async def list_users(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("user.manage")),
) -> list[dict]:
    users = list((await session.execute(select(User).order_by(User.full_name))).scalars())
    role_rows = (
        await session.execute(select(UserRole.user_id, Role.code).join(Role, Role.id == UserRole.role_id))
    ).all()
    roles: dict[UUID, list[str]] = {}
    for user_id, code in role_rows:
        roles.setdefault(user_id, []).append(code)
    return [_user_dict(user, sorted(roles.get(user.id, []))) for user in users]


@router.post("/users", status_code=201)
async def create_user(
    payload: UserCreate,
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("user.manage")),
) -> dict:
    if payload.unit_id and not await session.get(OrganizationalUnit, payload.unit_id):
        raise HTTPException(status_code=422, detail="Unit organisasi tidak ditemukan")
    roles = list((await session.execute(select(Role).where(Role.id.in_(payload.role_ids)))).scalars())
    if len(roles) != len(set(payload.role_ids)):
        raise HTTPException(status_code=422, detail="Satu atau lebih role tidak ditemukan")
    user = User(
        username=payload.username.lower(),
        full_name=payload.full_name.strip(),
        email=payload.email.lower() if payload.email else None,
        password_hash=hash_password(payload.password),
        unit_id=payload.unit_id,
        access_level=payload.access_level,
        active=True,
    )
    session.add(user)
    try:
        await session.flush()
        session.add_all(UserRole(user_id=user.id, role_id=role.id) for role in roles)
        general_room = (
            await session.execute(select(ChatRoom).where(ChatRoom.name == "Umum", ChatRoom.document_id.is_(None)))
        ).scalar_one_or_none()
        if general_room:
            session.add(ChatMember(room_id=general_room.id, user_id=user.id))
        record_audit(
            session,
            actor_user_id=actor.id,
            action="USER_CREATED",
            entity_type="User",
            entity_id=user.id,
            after={"username": user.username, "roles": [role.code for role in roles]},
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Username atau email sudah digunakan") from exc
    await session.refresh(user)
    return _user_dict(user, sorted(role.code for role in roles))


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("user.manage")),
) -> dict:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    before = _user_dict(user)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("unit_id") and not await session.get(OrganizationalUnit, changes["unit_id"]):
        raise HTTPException(status_code=422, detail="Unit organisasi tidak ditemukan")
    if "email" in changes and changes["email"]:
        changes["email"] = changes["email"].lower()
    for field, value in changes.items():
        setattr(user, field, value)
    if user.id == actor.id and user.active is False:
        raise HTTPException(status_code=409, detail="Administrator tidak dapat menonaktifkan akun sendiri")
    record_audit(
        session,
        actor_user_id=actor.id,
        action="USER_UPDATED",
        entity_type="User",
        entity_id=user.id,
        before=before,
        after=changes,
    )
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Email sudah digunakan") from exc
    await session.refresh(user)
    return _user_dict(user)


@router.post("/users/{user_id}/reset-password", status_code=204)
async def reset_password(
    user_id: UUID,
    payload: PasswordReset,
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("user.manage")),
) -> None:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    user.password_hash = hash_password(payload.password)
    user.token_version += 1
    record_audit(
        session,
        actor_user_id=actor.id,
        action="PASSWORD_RESET",
        entity_type="User",
        entity_id=user.id,
    )
    await session.commit()


@router.put("/users/{user_id}/roles")
async def update_user_roles(
    user_id: UUID,
    payload: UserRolesUpdate,
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("role.manage")),
) -> dict:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    roles = list((await session.execute(select(Role).where(Role.id.in_(payload.role_ids)))).scalars())
    if len(roles) != len(set(payload.role_ids)):
        raise HTTPException(status_code=422, detail="Satu atau lebih role tidak ditemukan")
    existing = list((await session.execute(select(UserRole).where(UserRole.user_id == user_id))).scalars())
    before = [str(item.role_id) for item in existing]
    await session.execute(delete(UserRole).where(UserRole.user_id == user_id))
    session.add_all(UserRole(user_id=user_id, role_id=role.id) for role in roles)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="USER_ROLES_UPDATED",
        entity_type="User",
        entity_id=user_id,
        before={"role_ids": before},
        after={"role_ids": [str(role.id) for role in roles]},
    )
    await session.commit()
    return {"user_id": str(user_id), "roles": [role.code for role in roles]}


@router.get("/permissions")
async def list_permissions(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("role.manage")),
) -> list[dict]:
    rows = list((await session.execute(select(Permission).order_by(Permission.code))).scalars())
    return [{"id": str(row.id), "code": row.code, "description": row.description} for row in rows]


@router.get("/roles")
async def list_roles(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("role.manage")),
) -> list[dict]:
    roles = list((await session.execute(select(Role).order_by(Role.name))).scalars())
    permission_rows = (
        await session.execute(
            select(RolePermission.role_id, Permission.id, Permission.code).join(
                Permission, Permission.id == RolePermission.permission_id
            )
        )
    ).all()
    mapped: dict[UUID, list[dict]] = {}
    for role_id, permission_id, code in permission_rows:
        mapped.setdefault(role_id, []).append({"id": str(permission_id), "code": code})
    return [
        {
            "id": str(role.id),
            "code": role.code,
            "name": role.name,
            "system": role.system,
            "permissions": mapped.get(role.id, []),
        }
        for role in roles
    ]


@router.post("/roles", status_code=201)
async def create_role(
    payload: RoleCreate,
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("role.manage")),
) -> dict:
    permissions = list(
        (await session.execute(select(Permission).where(Permission.id.in_(payload.permission_ids)))).scalars()
    )
    if len(permissions) != len(set(payload.permission_ids)):
        raise HTTPException(status_code=422, detail="Satu atau lebih permission tidak ditemukan")
    role = Role(code=payload.code, name=payload.name.strip(), system=False)
    session.add(role)
    try:
        await session.flush()
        session.add_all(RolePermission(role_id=role.id, permission_id=item.id) for item in permissions)
        record_audit(
            session,
            actor_user_id=actor.id,
            action="ROLE_CREATED",
            entity_type="Role",
            entity_id=role.id,
            after={"code": role.code, "permission_ids": [str(item.id) for item in permissions]},
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Kode role sudah digunakan") from exc
    return {"id": str(role.id), "code": role.code, "name": role.name, "system": role.system}


@router.put("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: UUID,
    payload: RolePermissionsUpdate,
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("role.manage")),
) -> dict:
    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    permissions = list(
        (await session.execute(select(Permission).where(Permission.id.in_(payload.permission_ids)))).scalars()
    )
    if len(permissions) != len(set(payload.permission_ids)):
        raise HTTPException(status_code=422, detail="Satu atau lebih permission tidak ditemukan")
    before = list(
        (await session.execute(select(RolePermission.permission_id).where(RolePermission.role_id == role.id))).scalars()
    )
    await session.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    session.add_all(RolePermission(role_id=role.id, permission_id=item.id) for item in permissions)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="ROLE_PERMISSIONS_UPDATED",
        entity_type="Role",
        entity_id=role.id,
        before={"permission_ids": [str(item) for item in before]},
        after={"permission_ids": [str(item.id) for item in permissions]},
    )
    await session.commit()
    return {"role_id": str(role.id), "permissions": [item.code for item in permissions]}


@router.get("/units")
async def list_units(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("user.manage")),
) -> list[dict]:
    rows = list((await session.execute(select(OrganizationalUnit).order_by(OrganizationalUnit.name))).scalars())
    return [
        {
            "id": str(row.id),
            "code": row.code,
            "name": row.name,
            "parent_id": str(row.parent_id) if row.parent_id else None,
            "active": row.active,
        }
        for row in rows
    ]


@router.post("/units", status_code=201)
async def create_unit(
    payload: UnitCreate,
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("user.manage")),
) -> dict:
    if payload.parent_id and not await session.get(OrganizationalUnit, payload.parent_id):
        raise HTTPException(status_code=422, detail="Unit induk tidak ditemukan")
    unit = OrganizationalUnit(code=payload.code, name=payload.name.strip(), parent_id=payload.parent_id, active=True)
    session.add(unit)
    try:
        await session.flush()
        record_audit(
            session,
            actor_user_id=actor.id,
            action="UNIT_CREATED",
            entity_type="OrganizationalUnit",
            entity_id=unit.id,
            after={"code": unit.code, "name": unit.name},
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Kode unit sudah digunakan") from exc
    return {"id": str(unit.id), "code": unit.code, "name": unit.name}


@router.get("/role-assignments")
async def list_role_assignments(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("role.manage")),
) -> list[dict]:
    rows = (
        await session.execute(
            select(RoleAssignment, Role.code, User.full_name)
            .join(Role, Role.id == RoleAssignment.role_id)
            .join(User, User.id == RoleAssignment.user_id)
            .order_by(Role.code, RoleAssignment.valid_from.desc())
        )
    ).all()
    return [
        {
            "id": str(item.id),
            "role_id": str(item.role_id),
            "role_code": role_code,
            "user_id": str(item.user_id),
            "user_name": user_name,
            "unit_id": str(item.unit_id) if item.unit_id else None,
            "valid_from": item.valid_from,
            "valid_until": item.valid_until,
            "active": item.active,
            "metadata": item.metadata_,
        }
        for item, role_code, user_name in rows
    ]


@router.post("/role-assignments", status_code=201)
async def create_role_assignment(
    payload: AssignmentCreate,
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("role.manage")),
) -> dict:
    if payload.valid_until and payload.valid_until < payload.valid_from:
        raise HTTPException(status_code=422, detail="Tanggal akhir tidak boleh sebelum tanggal mulai")
    if not await session.get(Role, payload.role_id) or not await session.get(User, payload.user_id):
        raise HTTPException(status_code=422, detail="Role atau pengguna tidak ditemukan")
    if payload.unit_id and not await session.get(OrganizationalUnit, payload.unit_id):
        raise HTTPException(status_code=422, detail="Unit organisasi tidak ditemukan")
    assignment = RoleAssignment(
        role_id=payload.role_id,
        user_id=payload.user_id,
        unit_id=payload.unit_id,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        active=True,
        metadata_=payload.metadata,
    )
    session.add(assignment)
    await session.flush()
    record_audit(
        session,
        actor_user_id=actor.id,
        action="ROLE_ASSIGNMENT_CREATED",
        entity_type="RoleAssignment",
        entity_id=assignment.id,
        after=payload.model_dump(mode="json"),
    )
    await session.commit()
    return {"id": str(assignment.id), "active": assignment.active}


@router.get("/workflows")
async def list_workflows(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("workflow.manage")),
) -> list[dict]:
    definitions = list(
        (
            await session.execute(
                select(WorkflowDefinition).order_by(WorkflowDefinition.document_type, WorkflowDefinition.version.desc())
            )
        ).scalars()
    )
    counts = dict(
        (
            await session.execute(select(WorkflowStep.definition_id, func.count()).group_by(WorkflowStep.definition_id))
        ).all()
    )
    return [
        {
            "id": str(item.id),
            "name": item.name,
            "document_type": item.document_type.value,
            "version": item.version,
            "state": item.state.value,
            "step_count": counts.get(item.id, 0),
            "created_at": item.created_at,
        }
        for item in definitions
    ]


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
    step_keys = [step.get("step_key") for step in payload.steps]
    if any(not key for key in step_keys) or len(step_keys) != len(set(step_keys)):
        raise HTTPException(status_code=422, detail="Step key wajib unik")
    for data in payload.steps:
        actions = {str(action).upper() for action in data.get("allowed_actions", [])}
        if not actions or actions - WORKFLOW_ACTIONS:
            raise HTTPException(status_code=422, detail="Action workflow kosong atau tidak valid")
        return_step = data.get("return_step_key")
        if return_step and return_step not in step_keys:
            raise HTTPException(status_code=422, detail="Tujuan RETURN tidak ditemukan")
        rule = data.get("assignment_rule", {})
        if not any(rule.get(key) for key in ("user_id", "user_ids", "role_id", "role_ids", "role_code")):
            raise HTTPException(status_code=422, detail="Setiap langkah wajib memiliki assignment")
        if rule.get("role_code"):
            role_exists = (
                await session.execute(select(Role.id).where(Role.code == str(rule["role_code"]).upper()))
            ).scalar_one_or_none()
            if not role_exists:
                raise HTTPException(status_code=422, detail=f"Role {rule['role_code']} tidak ditemukan")
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
        completion_rule = data.get("completion_rule", "ALL")
        if completion_rule not in {"ALL", "ANY", "SELECTED"}:
            raise HTTPException(status_code=422, detail="Completion rule tidak valid")
        session.add(
            WorkflowStep(
                definition_id=definition.id,
                step_key=data["step_key"],
                name=data["name"],
                sort_order=index,
                assignment_rule=data.get("assignment_rule", {}),
                allowed_actions=data.get("allowed_actions", []),
                completion_rule=completion_rule,
                return_step_key=data.get("return_step_key"),
                note_required_on_return=data.get("note_required_on_return", True),
            )
        )
    record_audit(
        session,
        actor_user_id=user.id,
        action="WORKFLOW_CREATED",
        entity_type="WorkflowDefinition",
        entity_id=definition.id,
        after={"document_type": document_type.value, "version": definition.version},
    )
    await session.commit()
    return {"id": str(definition.id), "version": definition.version, "state": definition.state.value}


@router.post("/workflows/{workflow_id}/publish")
async def publish_workflow(
    workflow_id: UUID,
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("workflow.manage")),
) -> dict:
    definition = await session.get(WorkflowDefinition, workflow_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Workflow tidak ditemukan")
    step_count = (
        await session.execute(
            select(func.count()).select_from(WorkflowStep).where(WorkflowStep.definition_id == workflow_id)
        )
    ).scalar_one()
    if not step_count:
        raise HTTPException(status_code=409, detail="Workflow tanpa langkah tidak dapat dipublikasikan")
    await session.execute(
        WorkflowDefinition.__table__.update()
        .where(
            WorkflowDefinition.document_type == definition.document_type,
            WorkflowDefinition.state == WorkflowState.PUBLISHED,
        )
        .values(state=WorkflowState.RETIRED)
    )
    definition.state = WorkflowState.PUBLISHED
    record_audit(
        session,
        actor_user_id=actor.id,
        action="WORKFLOW_PUBLISHED",
        entity_type="WorkflowDefinition",
        entity_id=definition.id,
        after={"version": definition.version},
    )
    await session.commit()
    return {"id": str(definition.id), "state": definition.state.value}


@router.get("/audit-logs")
async def list_audit_logs(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("audit.read")),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    rows = list((await session.execute(select(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(limit))).scalars())
    return [
        {
            "id": str(row.id),
            "occurred_at": row.occurred_at,
            "actor_user_id": str(row.actor_user_id) if row.actor_user_id else None,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": str(row.entity_id) if row.entity_id else None,
            "before": row.before_data,
            "after": row.after_data,
        }
        for row in rows
    ]


@router.get("/templates")
async def list_templates(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("template.manage")),
) -> list[dict]:
    templates = list((await session.execute(select(DocumentTemplate).order_by(DocumentTemplate.code))).scalars())
    versions = list(
        (
            await session.execute(
                select(DocumentTemplateVersion).order_by(
                    DocumentTemplateVersion.template_id, DocumentTemplateVersion.version.desc()
                )
            )
        ).scalars()
    )
    mapped: dict[UUID, list[dict]] = {}
    for version in versions:
        mapped.setdefault(version.template_id, []).append(
            {
                "id": str(version.id),
                "version": version.version,
                "sha256_hash": version.sha256_hash,
                "active": version.active,
                "created_at": version.created_at,
            }
        )
    return [
        {"id": str(item.id), "code": item.code, "name": item.name, "versions": mapped.get(item.id, [])}
        for item in templates
    ]


@router.post("/templates/upload", status_code=201)
async def upload_template(
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("template.manage")),
    code: str = Form(..., min_length=2, max_length=100),
    name: str = Form(..., min_length=2, max_length=255),
    upload: UploadFile = File(...),
) -> dict:
    normalized_code = code.strip().upper()
    if not normalized_code.replace("_", "").isalnum():
        raise HTTPException(status_code=422, detail="Kode template tidak valid")
    if normalized_code not in CODE_TO_TYPE:
        raise HTTPException(status_code=422, detail="Kode template tidak dikenali")
    data = await upload.read(10 * 1024 * 1024 + 1)
    if not data or len(data) > 10 * 1024 * 1024 or not data.startswith(b"PK\x03\x04"):
        raise HTTPException(status_code=422, detail="Template DOCX tidak valid atau terlalu besar")
    try:
        with ZipFile(BytesIO(data)) as archive:
            if "word/document.xml" not in archive.namelist():
                raise HTTPException(status_code=422, detail="Berkas bukan dokumen Word yang valid")
    except BadZipFile as exc:
        raise HTTPException(status_code=422, detail="Template DOCX rusak") from exc
    template = (
        await session.execute(select(DocumentTemplate).where(DocumentTemplate.code == normalized_code))
    ).scalar_one_or_none()
    if not template:
        template = DocumentTemplate(code=normalized_code, name=name.strip())
        session.add(template)
        await session.flush()
    latest = (
        await session.execute(
            select(func.max(DocumentTemplateVersion.version)).where(DocumentTemplateVersion.template_id == template.id)
        )
    ).scalar() or 0
    version_number = latest + 1
    object_key = f"custom/{normalized_code.lower()}-v{version_number}.docx"
    target = Path(get_settings().template_upload_dir) / object_key.removeprefix("custom/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    active_count = (
        await session.execute(
            select(func.count())
            .select_from(DocumentTemplateVersion)
            .where(
                DocumentTemplateVersion.template_id == template.id,
                DocumentTemplateVersion.active.is_(True),
            )
        )
    ).scalar_one()
    version = DocumentTemplateVersion(
        template_id=template.id,
        version=version_number,
        object_key=object_key,
        sha256_hash=sha256(data).hexdigest(),
        active=active_count == 0,
    )
    session.add(version)
    await session.flush()
    record_audit(
        session,
        actor_user_id=actor.id,
        action="TEMPLATE_VERSION_UPLOADED",
        entity_type="DocumentTemplateVersion",
        entity_id=version.id,
        after={"code": normalized_code, "version": version_number, "sha256": version.sha256_hash},
    )
    await session.commit()
    return {
        "id": str(version.id),
        "code": normalized_code,
        "version": version.version,
        "active": version.active,
    }


@router.post("/templates/versions/{version_id}/activate")
async def activate_template(
    version_id: UUID,
    session: SessionDep,
    actor: CurrentUser,
    _: object = Depends(require_permission("template.manage")),
) -> dict:
    version = await session.get(DocumentTemplateVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Versi template tidak ditemukan")
    if not resolve_version_path(version).exists():
        raise HTTPException(status_code=409, detail="Berkas template tidak tersedia")
    await session.execute(
        DocumentTemplateVersion.__table__.update()
        .where(DocumentTemplateVersion.template_id == version.template_id)
        .values(active=False)
    )
    version.active = True
    record_audit(
        session,
        actor_user_id=actor.id,
        action="TEMPLATE_VERSION_ACTIVATED",
        entity_type="DocumentTemplateVersion",
        entity_id=version.id,
        after={"version": version.version},
    )
    await session.commit()
    return {"id": str(version.id), "active": True}
