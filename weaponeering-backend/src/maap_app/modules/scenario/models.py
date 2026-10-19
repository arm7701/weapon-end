from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    description: str
    status: str
    ruleset_version: str
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class MapNode:
    id: str
    scenario_id: str
    label: str
    node_type: str
    map_lat: float
    map_lng: float
    review_status: str

