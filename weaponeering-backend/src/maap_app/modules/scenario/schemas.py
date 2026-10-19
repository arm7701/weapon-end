from __future__ import annotations

from pydantic import BaseModel, Field


class CreateScenarioRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    ruleset_version: str = Field(default="phase-1-baseline", max_length=80)


class CreateMapNodeRequest(BaseModel):
    scenario_id: str
    label: str = Field(min_length=1, max_length=120)
    node_type: str = Field(default="synthetic_node", max_length=80)
    map_lat: float = Field(ge=-90, le=90)
    map_lng: float = Field(ge=-180, le=180)

