from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiMessage(BaseModel):
    message: str


class LearningObjectiveCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    priority: int = Field(default=50, ge=0, le=100)


class LearningObjectiveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str
    priority: int
    created_at: datetime
    updated_at: datetime


class MapNodeCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    node_type: str = Field(default="synthetic_node", max_length=64)
    map_lat: float = Field(..., ge=-90, le=90)
    map_lng: float = Field(..., ge=-180, le=180)
    review_status: str = Field(default="draft", max_length=32)


class MapNodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str
    node_type: str
    map_lat: float
    map_lng: float
    review_status: str
    created_at: datetime
    updated_at: datetime


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    status: str = Field(default="draft", max_length=32)
    ruleset_version: str = Field(default="phase-0-web", max_length=64)
    learning_objectives: list[LearningObjectiveCreate] = Field(default_factory=list)
    map_nodes: list[MapNodeCreate] = Field(default_factory=list)

    @field_validator("description", mode="before")
    @classmethod
    def coerce_description(cls, value: object) -> str:
        return "" if value is None else str(value)


class ScenarioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(default=None, max_length=32)
    ruleset_version: str | None = Field(default=None, max_length=64)


class ScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    status: str
    ruleset_version: str
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    learning_objectives: list[LearningObjectiveOut] = Field(default_factory=list)
    map_nodes: list[MapNodeOut] = Field(default_factory=list)


class ScenarioListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    status: str
    ruleset_version: str
    created_at: datetime
    updated_at: datetime
