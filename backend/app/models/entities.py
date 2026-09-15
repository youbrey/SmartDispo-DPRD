from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentType(StrEnum):
    TRAVEL_REQUEST = "TRAVEL_REQUEST"
    MEETING_REQUEST = "MEETING_REQUEST"
    INCOMING_CHAIRMAN = "INCOMING_CHAIRMAN"
    INCOMING_SECRETARY = "INCOMING_SECRETARY"


class DocumentStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    RETURNED = "RETURNED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    OPENED = "OPENED"
    COMPLETED = "COMPLETED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class WorkflowState(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    RETIRED = "RETIRED"


class OrganizationalUnit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizational_units"
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizational_units.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(Text)
    unit_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizational_units.id"), index=True)
    access_level: Mapped[int] = mapped_column(Integer, default=10)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    token_version: Mapped[int] = mapped_column(Integer, default=0)


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    system: Mapped[bool] = mapped_column(Boolean, default=False)


class Permission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "permissions"
    code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255))


class UserRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), index=True)


class RolePermission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))
    permission_id: Mapped[UUID] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"))


class RoleAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "role_assignments"
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    unit_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizational_units.id"), index=True)
    valid_from: Mapped[date] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_type_status", "document_type", "status"),)
    document_number: Mapped[str | None] = mapped_column(String(120), unique=True)
    agenda_number: Mapped[str | None] = mapped_column(String(120), index=True)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, native_enum=False))
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False), default=DocumentStatus.DRAFT, index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    current_step_key: Mapped[str | None] = mapped_column(String(120))
    lock_version: Mapped[int] = mapped_column(Integer, default=0)


class DocumentVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version_number"),)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict] = mapped_column(JSONB)
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    change_reason: Mapped[str | None] = mapped_column(Text)
    template_version_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))


class Attachment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attachments"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    document_version: Mapped[int] = mapped_column(Integer)
    original_name: Mapped[str] = mapped_column(String(255))
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256_hash: Mapped[str] = mapped_column(String(64))


class TravelRequest(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "travel_requests"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    activity_type: Mapped[str] = mapped_column(String(80))
    destination: Mapped[str] = mapped_column(String(500))
    purpose: Mapped[str] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)


class TravelRequestMember(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "travel_request_members"
    travel_request_id: Mapped[UUID] = mapped_column(ForeignKey("travel_requests.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    position: Mapped[str | None] = mapped_column(String(255))
    member_group: Mapped[str] = mapped_column(String(30))
    sort_order: Mapped[int] = mapped_column(Integer)


class MeetingType(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meeting_types"
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class MeetingRequest(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "meeting_requests"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    meeting_type_code: Mapped[str] = mapped_column(String(80))
    purpose: Mapped[str] = mapped_column(Text)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    place: Mapped[str] = mapped_column(String(500))
    attire: Mapped[str | None] = mapped_column(String(255))


class MeetingRequestInvitee(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "meeting_request_invitees"
    meeting_request_id: Mapped[UUID] = mapped_column(ForeignKey("meeting_requests.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    institution: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer)


class IncomingLetter(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "incoming_letters"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    sender: Mapped[str] = mapped_column(String(500))
    letter_number: Mapped[str] = mapped_column(String(160))
    letter_date: Mapped[date] = mapped_column(Date)
    received_date: Mapped[date] = mapped_column(Date)
    subject: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(30), default="BIASA")


class AgendaEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agenda_entries"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"), unique=True)
    agenda_number: Mapped[str] = mapped_column(String(120), unique=True)
    agenda_date: Mapped[date] = mapped_column(Date)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class WorkflowDefinition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_definitions"
    __table_args__ = (UniqueConstraint("document_type", "version"),)
    name: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, native_enum=False))
    version: Mapped[int] = mapped_column(Integer)
    state: Mapped[WorkflowState] = mapped_column(Enum(WorkflowState, native_enum=False))


class WorkflowStep(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "workflow_steps"
    __table_args__ = (UniqueConstraint("definition_id", "step_key"),)
    definition_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_definitions.id", ondelete="CASCADE"))
    step_key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer)
    assignment_rule: Mapped[dict] = mapped_column(JSONB)
    allowed_actions: Mapped[list] = mapped_column(JSONB)
    completion_rule: Mapped[str] = mapped_column(String(20), default="ALL")
    return_step_key: Mapped[str | None] = mapped_column(String(120))
    note_required_on_return: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkflowInstance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_instances"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"), unique=True)
    definition_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_definitions.id"))
    current_step_key: Mapped[str] = mapped_column(String(120))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lock_version: Mapped[int] = mapped_column(Integer, default=0)


class WorkflowTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_tasks"
    __table_args__ = (Index("ix_tasks_assignee_status", "assignee_user_id", "status"),)
    instance_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_instances.id", ondelete="CASCADE"))
    step_key: Mapped[str] = mapped_column(String(120))
    assignee_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    assignee_role_id: Mapped[UUID | None] = mapped_column(ForeignKey("roles.id"))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, native_enum=False), default=TaskStatus.PENDING)
    available_actions: Mapped[list] = mapped_column(JSONB)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Approval(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "approvals"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    document_version: Mapped[int] = mapped_column(Integer)
    document_hash: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    role_code: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    device_id: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(64))


class DispositionSheet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "disposition_sheets"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"), unique=True)
    sheet_type: Mapped[str] = mapped_column(String(40))
    structured_data: Mapped[dict] = mapped_column(JSONB, default=dict)


class Disposition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dispositions"
    sheet_id: Mapped[UUID] = mapped_column(ForeignKey("disposition_sheets.id", ondelete="CASCADE"))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    actor_role: Mapped[str] = mapped_column(String(80))
    directives: Mapped[list] = mapped_column(JSONB)
    note: Mapped[str | None] = mapped_column(Text)


class DispositionTarget(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "disposition_targets"
    disposition_id: Mapped[UUID] = mapped_column(ForeignKey("dispositions.id", ondelete="CASCADE"))
    unit_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizational_units.id"))
    role_id: Mapped[UUID | None] = mapped_column(ForeignKey("roles.id"))
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserDevice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_devices"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    device_fingerprint: Mapped[str] = mapped_column(String(255), unique=True)
    fcm_token: Mapped[str | None] = mapped_column(Text)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChatRoom(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_rooms"
    name: Mapped[str] = mapped_column(String(255))
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id"), index=True)


class ChatMember(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "chat_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id"),)
    room_id: Mapped[UUID] = mapped_column(ForeignKey("chat_rooms.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"
    room_id: Mapped[UUID] = mapped_column(ForeignKey("chat_rooms.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)


class DocumentTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_templates"
    code: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(255))


class DocumentTemplateVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_template_versions"
    __table_args__ = (UniqueConstraint("template_id", "version"),)
    template_id: Mapped[UUID] = mapped_column(ForeignKey("document_templates.id"))
    version: Mapped[int] = mapped_column(Integer)
    object_key: Mapped[str] = mapped_column(String(500))
    sha256_hash: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=False)


class IntegrationEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "integration_events"
    event_uuid: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    aggregate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)


class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refresh_tokens"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(120))
    entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    before_data: Mapped[dict | None] = mapped_column(JSONB)
    after_data: Mapped[dict | None] = mapped_column(JSONB)
    request_id: Mapped[str | None] = mapped_column(String(100), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64))
