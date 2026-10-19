from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewQueueItem:
    entity_type: str
    entity_id: str
    source: str
    label: str
    review_status: str
    created_at: str
    is_blocked: bool = False
