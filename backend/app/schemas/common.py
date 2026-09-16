from datetime import date, datetime, time
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


class TravelMemberInput(ApiModel):
    name: str = Field(min_length=2, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    member_group: str = Field(pattern="^(EXECUTOR|ACCOMPANYING)$")


class TravelRequestPayload(ApiModel):
    sender_name: str = Field(min_length=2, max_length=255)
    sender_position: str = Field(min_length=2, max_length=255)
    organizational_unit: str = Field(min_length=2, max_length=255)
    activity_type: str = Field(pattern="^(CONSULTATION|WORK_VISIT)$")
    destinations: list[str] = Field(min_length=1, max_length=4)
    purpose: str = Field(min_length=3, max_length=8000)
    material: str = Field(min_length=3, max_length=8000)
    general_problem: str = Field(min_length=3, max_length=8000)
    current_condition: str = Field(min_length=3, max_length=8000)
    efforts: str = Field(min_length=3, max_length=8000)
    start_date: date
    end_date: date
    activity_time: time | None = None
    place: str = Field(min_length=2, max_length=500)
    members: list[TravelMemberInput] = Field(min_length=1, max_length=26)
    notes: str | None = Field(default=None, max_length=4000)
    signer_role_code: str | None = Field(default=None, max_length=80)
    follow_up_directives: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("destinations")
    @classmethod
    def normalize_destinations(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values if value.strip()]
        if not normalized:
            raise ValueError("Minimal satu tujuan wajib diisi")
        if len({value.casefold() for value in normalized}) != len(normalized):
            raise ValueError("Daftar tujuan tidak boleh duplikat")
        return normalized

    @model_validator(mode="after")
    def validate_travel_request(self):
        if self.end_date < self.start_date:
            raise ValueError("Tanggal selesai tidak boleh sebelum tanggal mulai")
        identities = {(member.name.strip().casefold(), member.member_group) for member in self.members}
        if len(identities) != len(self.members):
            raise ValueError("Daftar pelaksana atau pendamping tidak boleh duplikat")
        if not any(member.member_group == "EXECUTOR" for member in self.members):
            raise ValueError("Minimal satu pelaksana wajib diisi")
        return self


class TravelRequestCreate(TravelRequestPayload):
    pass


class TravelRequestUpdate(TravelRequestPayload):
    expected_lock_version: int = Field(ge=0)
    change_reason: str = Field(min_length=3, max_length=1000)


class TravelRequestView(TravelRequestPayload):
    id: UUID
    document_id: UUID
    document_status: str
    title: str
    duration_days: int
    current_version: int
    lock_version: int
    available_actions: list[str] = Field(default_factory=list)
    created_at: datetime


class IncomingLetterCreate(ApiModel):
    route_type: str = Field(pattern="^(DPRD|SETWAN)$")
    sender: str = Field(min_length=2, max_length=500)
    letter_number: str = Field(min_length=1, max_length=160)
    letter_date: date
    received_date: date
    agenda_number: str = Field(min_length=1, max_length=120)
    agenda_date: date
    subject: str = Field(min_length=3, max_length=8000)
    priority: str = Field(pattern="^(BIASA|PENTING|SEGERA|RAHASIA)$")
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.received_date < self.letter_date:
            raise ValueError("Tanggal terima tidak boleh sebelum tanggal surat")
        return self


class IncomingLetterView(IncomingLetterCreate):
    document_id: UUID
    document_status: str
    title: str
    current_version: int
    lock_version: int
    available_actions: list[str] = Field(default_factory=list)
    created_at: datetime


class DispositionTargetInput(ApiModel):
    unit_id: UUID | None = None
    role_id: UUID | None = None
    user_id: UUID | None = None

    @model_validator(mode="after")
    def exactly_one_target(self):
        if sum(value is not None for value in (self.unit_id, self.role_id, self.user_id)) != 1:
            raise ValueError("Tujuan disposisi harus tepat satu unit, role, atau pengguna")
        return self


class DispositionTargetOption(ApiModel):
    target_type: str
    target_id: UUID
    label: str
    subtitle: str | None = None


class DispositionCreate(ApiModel):
    actor_role: str = Field(min_length=2, max_length=80)
    directives: list[str] = Field(min_length=1, max_length=30)
    note: str | None = Field(default=None, max_length=8000)
    targets: list[DispositionTargetInput] = Field(default_factory=list, max_length=30)

    @field_validator("directives")
    @classmethod
    def unique_directives(cls, values: list[str]) -> list[str]:
        normalized = [value.strip().upper() for value in values if value.strip()]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Pilihan disposisi tidak boleh duplikat")
        return normalized


class DispositionView(ApiModel):
    id: UUID
    document_id: UUID
    sheet_type: str
    actor_role: str
    directives: list[str]
    note: str | None
    targets: list[DispositionTargetInput]
    created_at: datetime
