from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TargetMapDetectionObject:
    id: str
    run_id: str
    target_card_id: str
    map_object_id: str
    object_label: str
    object_type: str
    risk_level: str
    confidence: float
    center_lat: float
    center_lng: float
    polygon_json: str
    sort_order: int = 0


@dataclass(frozen=True)
class TargetMapDetectionRun:
    id: str
    scenario_id: str
    target_card_id: str
    target_coordinate_id: str
    model_name: str
    model_file_name: str | None
    radius_m: int
    capture_radius_m: int
    source_image_name: str | None
    object_count: int
    detection_message: str | None
    created_at: str | None = None
    updated_at: str | None = None
    objects: tuple[TargetMapDetectionObject, ...] = ()
