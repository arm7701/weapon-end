from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TargetCoordinateIn(BaseModel):
    id: UUID | None = None
    label: str = ""
    map_lat: float = Field(..., ge=-90, le=90)
    map_lng: float = Field(..., ge=-180, le=180)
    is_primary: bool = False
    selected_product_id: str | None = None


class TargetCoordinateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str
    map_lat: float
    map_lng: float
    sort_order: int
    is_primary: bool
    selected_product_id: str | None = None
    created_at: datetime


class TargetRecognitionIn(BaseModel):
    source_type: str = "manual"
    recognition_summary: str = ""
    recognition_confidence_score: int = Field(default=50, ge=0, le=100)
    missing_data_notes: list[str] = Field(default_factory=list)
    generated_by: str = "user"
    review_status: str = "requires_review"


class TargetRecognitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_type: str
    recognition_summary: str
    recognition_confidence_score: int
    missing_data_json: list = Field(default_factory=list)
    generated_by: str
    review_status: str
    created_at: datetime
    updated_at: datetime


class TargetCardCreate(BaseModel):
    scenario_id: UUID
    label: str = Field(..., min_length=1, max_length=255)
    priority_score: int = Field(default=3, ge=1, le=5)
    complexity_score: int = Field(default=3, ge=1, le=5)
    review_status: str = "draft"
    status: str = "active"
    target_type: str = "BUILDING"
    target_subtype: str = "UNKNOWN"
    material_class: str = "UNKNOWN"
    material_strength: dict[str, float | str] = Field(default_factory=dict)
    target_description: str = ""
    floor_count: str = ""
    width_m: float | None = None
    length_m: float | None = None
    height_m: float | None = None
    heading_deg: float | None = Field(default=None, ge=0, lt=360)
    desired_model_result: str = "STRUCTURAL FAILURE"
    coordinate_error_m: float | None = None
    data_source: str = "manual"
    cep: float | None = None
    target_pk: float | None = None
    reference_pk: float | None = None
    resistance: str = ""
    capacity: str = ""
    damage_fit: str = ""
    model_version: str = ""
    selected_product_id: str | None = None
    coordinates: list[TargetCoordinateIn] = Field(default_factory=list)
    recognition: TargetRecognitionIn | None = None


class TargetCardUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    priority_score: int | None = Field(default=None, ge=1, le=5)
    complexity_score: int | None = Field(default=None, ge=1, le=5)
    review_status: str | None = None
    status: str | None = None
    target_type: str | None = None
    target_subtype: str | None = None
    material_class: str | None = None
    material_strength: dict[str, float | str] | None = None
    target_description: str | None = None
    floor_count: str | None = None
    width_m: float | None = None
    length_m: float | None = None
    height_m: float | None = None
    heading_deg: float | None = Field(default=None, ge=0, lt=360)
    desired_model_result: str | None = None
    coordinate_error_m: float | None = None
    data_source: str | None = None
    cep: float | None = None
    target_pk: float | None = None
    reference_pk: float | None = None
    resistance: str | None = None
    capacity: str | None = None
    damage_fit: str | None = None
    model_version: str | None = None
    selected_product_id: str | None = None
    coordinates: list[TargetCoordinateIn] | None = None


class TargetCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    label: str
    priority_score: int
    complexity_score: int
    map_node_id: UUID | None = None
    review_status: str
    status: str
    target_type: str
    target_subtype: str
    material_class: str
    material_strength: dict = Field(default_factory=dict)
    target_description: str
    floor_count: str
    width_m: float | None = None
    length_m: float | None = None
    height_m: float | None = None
    heading_deg: float | None = None
    desired_model_result: str
    coordinate_error_m: float | None = None
    data_source: str
    cep: float | None = None
    target_pk: float | None = None
    reference_pk: float | None = None
    resistance: str
    capacity: str
    damage_fit: str
    model_version: str
    selected_product_id: str | None = None
    created_at: datetime
    updated_at: datetime
    coordinates: list[TargetCoordinateOut] = Field(default_factory=list)
    recognition_results: list[TargetRecognitionOut] = Field(default_factory=list)


class TargetCardListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    label: str
    priority_score: int
    complexity_score: int
    review_status: str
    status: str
    target_type: str
    data_source: str
    created_at: datetime
    updated_at: datetime


class HumanReviewCreate(BaseModel):
    scenario_id: UUID
    entity_type: str = Field(..., min_length=1, max_length=64)
    entity_id: str = Field(..., min_length=1, max_length=64)
    decision: str = Field(..., min_length=1, max_length=64)
    notes: str = ""
    review_status: str | None = None


class HumanReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    entity_type: str
    entity_id: str
    reviewer: str
    decision: str
    notes: str
    created_at: datetime
