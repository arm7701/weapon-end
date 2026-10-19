from __future__ import annotations

from uuid import uuid4

from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository


BLOCKED_TERMS = (
    "real target",
    "real weapon",
    "munition quantity",
    "probability of kill",
    "jmem formula",
    "operational route",
    "mission tasking",
    "live intelligence",
    "operational coordinates",
    "weapon recommendation",
    "real aircraft",
    "live readiness",
    "real depot",
    "real stockpile",
    "real weapon inventory",
    "operational logistics",
    "navigation instruction",
    "real unit location",
)

IMPORT_BLOCKED_TERMS = BLOCKED_TERMS + (
    "pk=",
    "pd=",
    "cep",
    "tle",
    "mae",
    "impact angle",
    "fuze",
    "delivery profile",
    "jdam",
    "gbu-",
    "aim-",
    "f-16",
    "f-15",
    "f-35",
    "b-52",
    "vulnerability model",
    "weapon pairing",
    "munition count",
    "equation",
    "formula:",
)


class GuardrailService:
    def __init__(
        self,
        repository: GuardrailRepository,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def validate_training_text(
        self,
        text: str,
        entity_type: str,
        entity_id: str,
    ) -> bool:
        lowered = text.lower()
        blocked = any(term in lowered for term in BLOCKED_TERMS)
        decision = "blocked" if blocked else "allowed"
        summary = "blocked operational wording" if blocked else "training-safe text"
        self.repository.insert_event(
            event_id=str(uuid4()),
            event_type="text_validation",
            entity_type=entity_type,
            entity_id=entity_id,
            decision=decision,
            sanitized_summary=summary,
        )
        if blocked:
            self.audit_service.record_event(
                actor="system",
                event_type="guardrail_blocked",
                entity_type=entity_type,
                entity_id=entity_id,
                details={"summary": summary},
            )
        return not blocked

    def validate_import_payload(self, text: str, entity_type: str, entity_id: str) -> bool:
        lowered = text.lower()
        blocked = any(term in lowered for term in IMPORT_BLOCKED_TERMS)
        decision = "blocked" if blocked else "allowed"
        summary = (
            "blocked unsafe import content"
            if blocked
            else "import payload passed guardrail"
        )
        self.repository.insert_event(
            event_id=str(uuid4()),
            event_type="import_validation",
            entity_type=entity_type,
            entity_id=entity_id,
            decision=decision,
            sanitized_summary=summary,
        )
        if blocked:
            self.audit_service.record_event(
                actor="system",
                event_type="guardrail_blocked",
                entity_type=entity_type,
                entity_id=entity_id,
                details={"summary": summary, "context": "import"},
            )
        return not blocked

