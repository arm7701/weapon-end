from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor: str
    event_type: str
    entity_type: str
    entity_id: str
    details_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class UserMeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    user_name: str | None = None
    rank: str | None = None
    fname: str | None = None
    lname: str | None = None
    user_position: str | None = None
    user_orgname: str | None = None
    user_orgname_code: str | None = None
    user_role: str | None = None
