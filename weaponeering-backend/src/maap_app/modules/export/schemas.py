from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


EXPORT_TYPES = (
    "scenario_brief",
    "target_list",
    "weaponeering_summary",
    "logistics_summary",
    "ranking_table",
    "scorecard",
    "instructor_notes",
    "audit_summary",
    "full_package",
    "aar_summary",
)

EXPORT_FORMATS = ("markdown", "csv", "json")

RANKING_EXPORT_TYPES = frozenset({"ranking_table", "scorecard", "full_package"})


@dataclass(frozen=True)
class ExportReadinessRequest:
    scenario_id: str
    export_type: str


@dataclass(frozen=True)
class CreateExportRequest:
    scenario_id: str
    export_type: str
    export_format: str
    destination_dir: Path
    ranking_run_id: str | None = None
    created_by: str = "local_user"


@dataclass(frozen=True)
class CompareRankingRequest:
    scenario_id: str
    run_a_id: str
    run_b_id: str


@dataclass(frozen=True)
class ReplayRankingRequest:
    scenario_id: str
    ranking_run_id: str


@dataclass(frozen=True)
class UpdateActionItemRequest:
    action_item_id: str
    status: str
