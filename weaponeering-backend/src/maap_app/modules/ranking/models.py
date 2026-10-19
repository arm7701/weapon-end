from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoringProfile:
    id: str
    scenario_id: str
    name: str
    ruleset_version: str
    priority_weight: int
    weaponeering_weight: int
    logistics_weight: int
    readiness_weight: int
    risk_weight: int
    resource_balance_weight: int
    is_active: int


@dataclass(frozen=True)
class RankingRun:
    id: str
    scenario_id: str
    ruleset_version: str
    scoring_profile_id: str | None
    generated_by: str
    run_status: str
    summary: str
    created_at: str | None = None


@dataclass(frozen=True)
class RankingItem:
    id: str
    ranking_run_id: str
    entity_type: str
    entity_id: str
    rank_order: int
    total_score: int
    confidence_score: int
    rationale: str
    breakdown_json: str
    review_status: str
    override_rank_order: int | None = None
    override_notes: str = ""
    entity_label: str | None = None


@dataclass
class RankingRunResult:
    run: RankingRun
    items: list[RankingItem] = field(default_factory=list)
