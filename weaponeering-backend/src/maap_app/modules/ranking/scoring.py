from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RankingComponentScores:
    priority_alignment: int | None
    weaponeering_fit: int | None
    logistics_feasibility: int | None
    readiness: int | None
    resource_balance: int | None
    risk_indicator: int | None


@dataclass(frozen=True)
class RankingWeights:
    priority_weight: int
    weaponeering_weight: int
    logistics_weight: int
    readiness_weight: int
    risk_weight: int
    resource_balance_weight: int


def calculate_ranking_score(
    components: RankingComponentScores,
    weights: RankingWeights,
) -> tuple[int, int, str, dict[str, int | None], list[str]]:
    warnings: list[str] = []
    weighted_parts: list[tuple[str, int, int]] = []

    mapping = [
        ("priority_alignment", components.priority_alignment, weights.priority_weight),
        ("weaponeering_fit", components.weaponeering_fit, weights.weaponeering_weight),
        ("logistics_feasibility", components.logistics_feasibility, weights.logistics_weight),
        ("readiness", components.readiness, weights.readiness_weight),
        ("risk_indicator", components.risk_indicator, weights.risk_weight),
        ("resource_balance", components.resource_balance, weights.resource_balance_weight),
    ]

    breakdown: dict[str, int | None] = {}
    total_weight = 0
    weighted_sum = 0
    present_components = 0

    for name, value, weight in mapping:
        breakdown[name] = value
        if value is None:
            warnings.append(f"Missing {name.replace('_', ' ')} input.")
            continue
        present_components += 1
        total_weight += weight
        weighted_sum += value * weight

    if total_weight == 0 or present_components == 0:
        return 1, 20, "Insufficient ranking inputs.", breakdown, warnings

    total_score = max(1, min(100, weighted_sum // total_weight))
    confidence = max(20, min(100, int(100 * present_components / len(mapping))))
    rationale = (
        f"Weighted aggregate from {present_components} component(s): "
        + "; ".join(f"{k}={v}" for k, v in breakdown.items() if v is not None)
        + "."
    )
    return total_score, confidence, rationale, breakdown, warnings
