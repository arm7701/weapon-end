from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateScoringProfileRequest:
    scenario_id: str
    name: str
    priority_weight: int = 20
    weaponeering_weight: int = 20
    logistics_weight: int = 20
    readiness_weight: int = 15
    risk_weight: int = 15
    resource_balance_weight: int = 10


@dataclass(frozen=True)
class RunRankingRequest:
    scenario_id: str
    scoring_profile_id: str | None = None
    ruleset_version: str = "phase-1-baseline"


@dataclass(frozen=True)
class OverrideRankingRequest:
    ranking_item_id: str
    new_rank_order: int
    reviewer: str = "local_user"
    notes: str = ""
