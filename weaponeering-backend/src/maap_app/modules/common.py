from __future__ import annotations

from enum import StrEnum


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    REQUIRES_REVIEW = "requires_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED_BY_GUARDRAIL = "blocked_by_guardrail"


def clamp_score(value: int, *, minimum: int = 1, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))

