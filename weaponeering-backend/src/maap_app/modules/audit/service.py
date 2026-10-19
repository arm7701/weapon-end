from __future__ import annotations

from typing import Any
from uuid import uuid4

from maap_app.modules.audit.repository import AuditRepository


class AuditService:
    def __init__(self, repository: AuditRepository) -> None:
        self.repository = repository

    def record_event(
        self,
        actor: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.repository.insert(
            event_id=str(uuid4()),
            actor=actor,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )

