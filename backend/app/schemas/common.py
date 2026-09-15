from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
