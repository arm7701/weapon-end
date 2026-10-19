from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AiInteraction:
    id: str
    scenario_id: str
    entity_type: str
    entity_id: str
    request_type: str
    sanitized_prompt: str
    sanitized_output: str
    classifier_result: str
    validator_result: str
    review_status: str
    created_at: str | None = None
