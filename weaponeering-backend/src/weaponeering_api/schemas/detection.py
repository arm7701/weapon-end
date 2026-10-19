from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Detection ---


class DetectionObjectIn(BaseModel):
    map_object_id: str = Field(..., min_length=1, max_length=128)
    object_label: str = Field(..., min_length=1, max_length=255)
    object_type: str = Field(..., min_length=1, max_length=64)
    risk_level: str = Field(..., min_length=1, max_length=32)
    confidence: float = Field(..., ge=0, le=1)
    center_lat: float = Field(..., ge=-90, le=90)
    center_lng: float = Field(..., ge=-180, le=180)
    polygon_json: list[Any] | dict[str, Any] = Field(default_factory=list)
    sort_order: int = 0


class DetectionObjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    target_card_id: UUID
    map_object_id: str
    object_label: str
    object_type: str
    risk_level: str
    confidence: float
    center_lat: float
    center_lng: float
    polygon_json: list[Any] | dict[str, Any] = Field(default_factory=list)
    sort_order: int


class DetectionRunUpsert(BaseModel):
    scenario_id: UUID
    target_card_id: UUID
    target_coordinate_id: UUID
    model_name: str = Field(..., min_length=1, max_length=255)
    model_file_name: str | None = None
    radius_m: int = Field(..., gt=0)
    capture_radius_m: int = Field(..., gt=0)
    source_image_name: str | None = None
    detection_message: str | None = None
    objects: list[DetectionObjectIn] = Field(default_factory=list)


class DetectionRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    target_card_id: UUID
    target_coordinate_id: UUID
    model_name: str
    model_file_name: str | None = None
    radius_m: int
    capture_radius_m: int
    source_image_name: str | None = None
    object_count: int
    detection_message: str | None = None
    objects: list[DetectionObjectOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DetectionExecuteOut(BaseModel):
    run: DetectionRunOut
    lowestRiskDirection: dict[str, Any]
    message: str = ""
    objectCount: int = 0
    captureRadiusM: int = 0
    zoomLevel: int = 4
    modelName: str = "Building Detector"
    defaults: dict[str, Any] = Field(default_factory=dict)


class DetectionMapObjectOut(BaseModel):
    id: UUID
    run_id: UUID
    target_card_id: UUID
    target_coordinate_id: UUID
    map_object_id: str
    object_label: str
    object_type: str
    risk_level: str
    confidence: float
    center_lat: float
    center_lng: float
    polygon_json: list[Any] | dict[str, Any] = Field(default_factory=list)
    model_name: str
    radius_m: int


# --- Team markers ---


TeamSide = Literal["blue", "red"]
UnitType = Literal["generic", "radar", "tank", "small_arms", "artillery", "anti_air"]


class TeamMarkerCreate(BaseModel):
    scenario_id: UUID
    side: TeamSide
    label: str = Field(..., min_length=1, max_length=255)
    map_lat: float = Field(..., ge=-90, le=90)
    map_lng: float = Field(..., ge=-180, le=180)
    unit_type: UnitType = "generic"
    radius_m: float | None = Field(default=None, ge=0)


class TeamMarkerUpdate(BaseModel):
    side: TeamSide | None = None
    label: str | None = Field(default=None, min_length=1, max_length=255)
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    unit_type: UnitType | None = None
    radius_m: float | None = Field(default=None, ge=0)


class TeamMarkerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    side: str
    unit_type: str
    label: str
    map_lat: float
    map_lng: float
    radius_m: float | None = None
    created_at: datetime
    updated_at: datetime


# --- Ground transports ---


class GroundTransportCreate(BaseModel):
    scenario_id: UUID
    origin_wing_id: UUID
    destination_wing_id: UUID
    distance_m: float = Field(..., ge=0)
    duration_min: float = Field(..., ge=0)
    product_id: UUID | None = None
    vehicle_id: UUID | None = None
    quantity: int = Field(default=1, ge=1)
    route_mode: str = "direct"
    route_geometry_json: list[Any] | dict[str, Any] | None = None
    label: str = ""
    status: str = "active"


class GroundTransportUpdate(BaseModel):
    origin_wing_id: UUID | None = None
    destination_wing_id: UUID | None = None
    product_id: UUID | None = None
    vehicle_id: UUID | None = None
    quantity: int | None = Field(default=None, ge=1)
    distance_m: float | None = Field(default=None, ge=0)
    duration_min: float | None = Field(default=None, ge=0)
    route_mode: str | None = None
    route_geometry_json: list[Any] | dict[str, Any] | None = None
    label: str | None = None
    status: str | None = None


class GroundTransportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    origin_wing_id: UUID
    destination_wing_id: UUID
    product_id: UUID | None = None
    vehicle_id: UUID | None = None
    quantity: int
    distance_m: float
    duration_min: float
    route_mode: str
    route_geometry_json: list[Any] | dict[str, Any] | None = None
    label: str
    status: str
    created_at: datetime
    updated_at: datetime
