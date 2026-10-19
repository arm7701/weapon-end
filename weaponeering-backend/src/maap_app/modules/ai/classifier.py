from __future__ import annotations

from maap_app.modules.ai.schemas import CLASSIFIER_LABELS
from maap_app.modules.guardrail.service import BLOCKED_TERMS, IMPORT_BLOCKED_TERMS

REFRAMING_HINTS = (
    "recommend weapon",
    "select aircraft",
    "best munition",
    "operational plan",
    "mission tasking",
    "real target",
)


def classify_input(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in BLOCKED_TERMS + IMPORT_BLOCKED_TERMS):
        return "blocked_operational"
    if any(hint in lowered for hint in REFRAMING_HINTS):
        return "needs_reframing"
    return "safe_training"


def is_allowed_classifier_result(result: str) -> bool:
    return result in CLASSIFIER_LABELS and result != "blocked_operational"
