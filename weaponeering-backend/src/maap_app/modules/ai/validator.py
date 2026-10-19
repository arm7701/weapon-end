from __future__ import annotations

from maap_app.modules.guardrail.service import BLOCKED_TERMS, IMPORT_BLOCKED_TERMS


def validate_output(text: str) -> tuple[bool, str]:
    lowered = text.lower()
    blocked = any(term in lowered for term in BLOCKED_TERMS + IMPORT_BLOCKED_TERMS)
    if blocked:
        return False, "blocked_unsafe_output"
    return True, "allowed_training_output"
