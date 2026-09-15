from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenPair(ApiModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(ApiModel):
    refresh_token: str


class DocumentCreate(ApiModel):
    document_type: str
    title: str = Field(min_length=3, max_length=500)
    content: dict[str, Any]


class DocumentUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=3, max_length=500)
    content: dict[str, Any]
    expected_lock_version: int = Field(ge=0)
    change_reason: str = Field(min_length=3, max_length=1000)


class DocumentView(ApiModel):
    id: UUID
    document_number: str | None
    agenda_number: str | None
    document_type: str
    status: str
    title: str
    current_version: int
    current_step_key: str | None
    lock_version: int
    available_actions: list[str] = Field(default_factory=list)
    created_at: datetime


class TaskActionRequest(ApiModel):
    action: str
    note: str | None = Field(default=None, max_length=4000)
    expected_instance_lock_version: int = Field(ge=0)
    device_id: str | None = Field(default=None, max_length=255)


class WorkflowCreate(ApiModel):
    name: str
    document_type: str
    steps: list[dict[str, Any]] = Field(min_length=1)


class MeetingTypeView(ApiModel):
    code: str
    name: str
    sort_order: int


class MeetingInviteeInput(ApiModel):
    name: str = Field(min_length=1, max_length=255)
    institution: str | None = Field(default=None, max_length=255)


class MeetingRequestPayload(ApiModel):
    sender_name: str = Field(min_length=2, max_length=255)
    sender_position: str = Field(min_length=2, max_length=255)
    meeting_type_code: str = Field(min_length=2, max_length=80)
    purpose: str = Field(min_length=3, max_length=8000)
    scheduled_at: datetime
    place: str = Field(min_length=2, max_length=500)
    attire: str | None = Field(default=None, max_length=255)
    invitees: list[MeetingInviteeInput] = Field(min_length=1, max_length=20)
    notes: str | None = Field(default=None, max_length=4000)
    signer_role_code: str | None = Field(default=None, max_length=80)

    @field_validator("scheduled_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("scheduled_at wajib menyertakan zona waktu")
        return value

    @model_validator(mode="after")
    def unique_invitees(self):
        identities = {
            (invitee.name.strip().casefold(), (invitee.institution or "").strip().casefold())
            for invitee in self.invitees
        }
        if len(identities) != len(self.invitees):
            raise ValueError("Daftar undangan tidak boleh duplikat")
        return self


class MeetingRequestCreate(MeetingRequestPayload):
    pass


class MeetingRequestUpdate(MeetingRequestPayload):
    expected_lock_version: int = Field(ge=0)
    change_reason: str = Field(min_length=3, max_length=1000)


class MeetingRequestView(MeetingRequestPayload):
    id: UUID
    document_id: UUID
    document_status: str
    title: str
    meeting_type_name: str
    current_version: int
    lock_version: int
    available_actions: list[str] = Field(default_factory=list)
    created_at: datetime
