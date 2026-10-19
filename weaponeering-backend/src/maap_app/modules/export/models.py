from __future__ import annotations

from dataclasses import dataclass, field


SIMULATION_LABEL = "SIMULATION-ONLY TRAINING OUTPUT — NOT FOR OPERATIONAL USE"


@dataclass(frozen=True)
class ExportPackage:
    id: str
    scenario_id: str
    export_type: str
    export_status: str
    destination_path: str
    blocked_reason: str
    created_by: str
    created_at: str | None = None


@dataclass
class ExportReadinessResult:
    ready: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class RankingComparisonRow:
    entity_id: str
    entity_label: str
    run_a_rank: int | None
    run_b_rank: int | None
    run_a_score: int | None
    run_b_score: int | None
    score_delta: int | None
    rank_delta: int | None


@dataclass
class RankingComparisonResult:
    run_a_id: str
    run_b_id: str
    rows: list[RankingComparisonRow] = field(default_factory=list)
    summary: str = ""


@dataclass
class ReplayDifference:
    entity_id: str
    entity_label: str
    original_rank: int
    replay_rank: int
    original_score: int
    replay_score: int
    explanation: str


@dataclass
class ReplayResult:
    original_run_id: str
    replay_run_id: str
    differences: list[ReplayDifference] = field(default_factory=list)
    summary: str = ""


@dataclass(frozen=True)
class AarActionItem:
    id: str
    scenario_id: str
    source_type: str
    source_reference: str
    description: str
    status: str
    created_at: str | None = None
