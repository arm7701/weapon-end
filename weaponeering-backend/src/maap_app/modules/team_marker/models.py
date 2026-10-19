from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioTeamMarker:
    id: str
    scenario_id: str
    side: str
    unit_type: str
    label: str
    map_lat: float
    map_lng: float
    radius_m: float | None
    created_at: str
    updated_at: str
