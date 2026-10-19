from __future__ import annotations

from dataclasses import dataclass, field

from maap_app.modules.target.profile_fields import TargetProfileFields


@dataclass(frozen=True)
class CreateTargetCardRequest:
    scenario_id: str
    label: str
    priority_score: int = 3
    complexity_score: int = 3
    profile: TargetProfileFields = field(default_factory=TargetProfileFields)


@dataclass(frozen=True)
class UpdateTargetCardRequest:
    target_card_id: str
    label: str
    priority_score: int
    complexity_score: int
    profile: TargetProfileFields = field(default_factory=TargetProfileFields)
    review_status: str | None = None


@dataclass(frozen=True)
class CreateRecognitionResultRequest:
    target_card_id: str
    source_type: str
    recognition_summary: str
    recognition_confidence_score: int
    missing_data_notes: list[str] = field(default_factory=list)
    generated_by: str = "user"


@dataclass(frozen=True)
class UpdateRecognitionResultRequest:
    recognition_id: str
    recognition_summary: str
    recognition_confidence_score: int
    missing_data_notes: list[str] = field(default_factory=list)
    review_status: str | None = None


@dataclass(frozen=True)
class LinkTargetMapNodeRequest:
    target_card_id: str
    scenario_id: str
    map_lat: float
    map_lng: float
    label: str | None = None


@dataclass(frozen=True)
class TargetCoordinateInput:
    label: str = ""
    map_lat: float = 0.0
    map_lng: float = 0.0
    is_primary: bool = False
    id: str | None = None
    selected_product_id: str | None = None


@dataclass(frozen=True)
class SaveTargetCoordinatesRequest:
    target_card_id: str
    scenario_id: str
    coordinates: list[TargetCoordinateInput]


@dataclass(frozen=True)
class CreateReviewRecordRequest:
    scenario_id: str
    entity_type: str
    entity_id: str
    reviewer: str
    decision: str
    notes: str = ""
    review_status: str = "approved"


@dataclass(frozen=True)
class TargetFilterParams:
    search_text: str = ""
    review_status: str = ""
    priority_min: int = 1
    priority_max: int = 5
    complexity_min: int = 1
    complexity_max: int = 5
    confidence_min: int = 0
    confidence_max: int = 100
