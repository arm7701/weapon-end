from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditEvent:
    id: str
    actor: str
    event_type: str
    entity_type: str
    entity_id: str
    details_json: str
    created_at: str | None = None

