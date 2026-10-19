from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TargetCard:
    id: str
    scenario_id: str
    label: str
    priority_score: int
    complexity_score: int
    map_node_id: str | None
    review_status: str
    status: str
    target_type: str = "BUILDING"
    target_subtype: str = "MULTI-STORY BUILDING"
    material_class: str = "UNKNOWN"
    target_description: str = ""
    floor_count: str = ""
    width_m: float | None = None
    length_m: float | None = None
    height_m: float | None = None
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
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class TargetRecognitionResult:
    id: str
    target_card_id: str
    source_type: str
    recognition_summary: str
    recognition_confidence_score: int
    missing_data_json: str
    generated_by: str
    review_status: str
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class HumanReviewRecord:
    id: str
    scenario_id: str
    entity_type: str
    entity_id: str
    reviewer: str
    decision: str
    notes: str
    created_at: str | None = None


@dataclass(frozen=True)
class TargetCardListItem:
    card: TargetCard
    recognition_confidence: int | None = None
    recognition_summary: str | None = None
    warning_count: int = 0


@dataclass(frozen=True)
class TargetCoordinate:
    id: str
    target_card_id: str
    label: str
    map_lat: float
    map_lng: float
    sort_order: int
    is_primary: bool
    selected_product_id: str | None = None
    created_at: str | None = None


@dataclass
class TargetCardDetail:
    card: TargetCard
    recognition: TargetRecognitionResult | None = None
    map_node_label: str | None = None
    map_lat: float | None = None
    map_lng: float | None = None
    coordinates: list[TargetCoordinate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
