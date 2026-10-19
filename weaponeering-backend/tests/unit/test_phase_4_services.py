from __future__ import annotations

import json
from pathlib import Path

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.logistics.schemas import CalculateLogisticsRequest
from maap_app.modules.logistics.service import LogisticsService
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.ranking.schemas import OverrideRankingRequest, RunRankingRequest
from maap_app.modules.ranking.service import RankingService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.schemas import CreateTargetCardRequest
from maap_app.modules.target.service import TargetService
from maap_app.modules.weaponeering.repository import WeaponeeringRepository
from maap_app.modules.weaponeering.schemas import (
    CreateAbstractOptionRequest,
    CreateAssessmentRequest,
)
from maap_app.modules.weaponeering.service import WeaponeeringService
from maap_app.modules.wing_data.repository import WingDataRepository


def build_phase_4_services(
    tmp_path: Path,
) -> tuple[str, str, WeaponeeringService, RankingService, TargetService]:
    settings = AppSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.sqlite3",
    )
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    audit_service = AuditService(AuditRepository(database))
    guardrail_service = GuardrailService(GuardrailRepository(database), audit_service)
    scenario_service = ScenarioService(
        repository=ScenarioRepository(database),
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    target_repository = TargetRepository(database)
    logistics_repository = LogisticsRepository(database)
    weaponeering_repository = WeaponeeringRepository(database)
    ranking_repository = RankingRepository(database)

    target_service = TargetService(
        repository=target_repository,
        scenario_repository=ScenarioRepository(database),
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    logistics_service = LogisticsService(
        repository=logistics_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    weaponeering_service = WeaponeeringService(
        repository=weaponeering_repository,
        target_repository=target_repository,
        wing_data_repository=WingDataRepository(database),
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    ranking_service = RankingService(
        repository=ranking_repository,
        target_repository=target_repository,
        weaponeering_repository=weaponeering_repository,
        logistics_repository=logistics_repository,
        audit_service=audit_service,
    )

    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Phase 4 Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(
            scenario_id=scenario_id,
            label="TGT-RANK-01",
            priority_score=75,
            complexity_score=40,
        )
    )
    logistics_service.calculate_logistics_feasibility(
        CalculateLogisticsRequest(scenario_id=scenario_id)
    )
    return scenario_id, target_id, weaponeering_service, ranking_service, target_service


def test_weaponeering_assessment_and_ranking_run(tmp_path: Path) -> None:
    scenario_id, target_id, weaponeering_service, ranking_service, _ = (
        build_phase_4_services(tmp_path)
    )

    option_id = weaponeering_service.create_abstract_option(
        CreateAbstractOptionRequest(
            scenario_id=scenario_id,
            option_label="OPT-DISRUPT-A",
            effect_category="abstract_disrupt",
            estimated_effect_score=70,
            risk_score=30,
        )
    )
    assessment_id = weaponeering_service.create_assessment(
        CreateAssessmentRequest(
            target_card_id=target_id,
            abstract_weaponeering_option_id=option_id,
            suitability_score=80,
            feasibility_score=75,
            risk_score=25,
            rationale="Synthetic abstract fit for training scenario.",
        )
    )
    weaponeering_service.approve_assessment(assessment_id)

    result = ranking_service.run_ranking(RunRankingRequest(scenario_id=scenario_id))
    assert result.run.scenario_id == scenario_id
    assert len(result.items) == 1
    assert result.items[0].entity_id == target_id
    assert 1 <= result.items[0].total_score <= 100
    assert result.items[0].confidence_score >= 20


def test_import_rejects_guardrail_blocked_row(tmp_path: Path) -> None:
    scenario_id, target_id, weaponeering_service, _, _ = build_phase_4_services(
        tmp_path
    )
    import_path = tmp_path / "unsafe_import.json"
    import_path.write_text(
        json.dumps(
            [
                {
                    "target_card_id": target_id,
                    "abstract_option_label": "OPT-BLOCKED",
                    "rationale": "Uses real weapon GBU-31 with PK=0.9",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = weaponeering_service.import_from_file(scenario_id, import_path)
    assert result.imported_count == 0
    assert result.rejected_count == 1
    assert weaponeering_service.list_abstract_options(scenario_id) == []


def test_ranking_override_and_plan_draft(tmp_path: Path) -> None:
    scenario_id, target_id, weaponeering_service, ranking_service, _ = (
        build_phase_4_services(tmp_path)
    )
    option_id = weaponeering_service.create_abstract_option(
        CreateAbstractOptionRequest(
            scenario_id=scenario_id,
            option_label="OPT-SUPPORT",
            effect_category="abstract_support",
        )
    )
    assessment_id = weaponeering_service.create_assessment(
        CreateAssessmentRequest(
            target_card_id=target_id,
            abstract_weaponeering_option_id=option_id,
            suitability_score=60,
            feasibility_score=60,
            risk_score=40,
        )
    )
    weaponeering_service.approve_assessment(assessment_id)

    result = ranking_service.run_ranking(RunRankingRequest(scenario_id=scenario_id))
    item = result.items[0]
    ranking_service.override_ranking_item(
        OverrideRankingRequest(
            ranking_item_id=item.id,
            new_rank_order=3,
            notes="Instructor moved target lower for training discussion.",
        )
    )
    updated = ranking_service.get_ranking_item(item.id)
    assert updated is not None
    assert updated.override_rank_order == 3

    plan_id = ranking_service.create_plan_draft_from_item(item.id)
    assert plan_id
