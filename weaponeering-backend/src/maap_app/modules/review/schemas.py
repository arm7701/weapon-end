from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewActionRequest:
    scenario_id: str
    entity_type: str
    entity_id: str
    decision: str
    reviewer: str = "local_user"
    notes: str = ""
