from __future__ import annotations

from pathlib import Path

from maap_app.config.ai_settings import AiSettings
from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.ai.context import ContextBundleBuilder
from maap_app.modules.ai.repository import AiRepository
from maap_app.modules.ai.service import AiAssistantService
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.export.repository import ExportRepository
from maap_app.modules.export.schemas import (
    CompareRankingRequest,
    CreateExportRequest,
    ExportReadinessRequest,
    ReplayRankingRequest,
)
from maap_app.modules.export.service import ExportService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.ranking.schemas import RunRankingRequest
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


def build_export_service(tmp_path: Path) -> tuple[str, ExportService, RankingService]:
    settings = AppSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.sqlite3",
    )
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    audit_repository = AuditRepository(database)
    audit_service = AuditService(audit_repository)
    guardrail_repository = GuardrailRepository(database)
    guardrail_service = GuardrailService(guardrail_repository, audit_service)
    scenario_repository = ScenarioRepository(database)
    scenario_service = ScenarioService(
        repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    target_repository = TargetRepository(database)
    logistics_repository = LogisticsRepository(database)
    weaponeering_repository = WeaponeeringRepository(database)
    ranking_repository = RankingRepository(database)
    ai_repository = AiRepository(database)

    target_service = TargetService(
        repository=target_repository,
        scenario_repository=scenario_repository,
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
    export_service = ExportService(
        repository=ExportRepository(database),
        scenario_repository=scenario_repository,
        target_repository=target_repository,
        weaponeering_repository=weaponeering_repository,
        logistics_repository=logistics_repository,
        ranking_repository=ranking_repository,
        ranking_service=ranking_service,
        ai_repository=ai_repository,
        audit_repository=audit_repository,
        guardrail_repository=guardrail_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )

    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Phase 6 Export Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(
            scenario_id=scenario_id,
            label="TGT-EXPORT-01",
            priority_score=80,
            complexity_score=30,
        )
    )
    option_id = weaponeering_service.create_abstract_option(
        CreateAbstractOptionRequest(
            scenario_id=scenario_id,
            option_label="OPT-EXPORT",
        )
    )
    assessment_id = weaponeering_service.create_assessment(
        CreateAssessmentRequest(
            target_card_id=target_id,
            abstract_weaponeering_option_id=option_id,
            suitability_score=70,
            feasibility_score=65,
            risk_score=35,
        )
    )
    weaponeering_service.approve_assessment(assessment_id)
    ranking_service.run_ranking(RunRankingRequest(scenario_id=scenario_id))
    return scenario_id, export_service, ranking_service


def test_export_readiness_blocks_ranking_without_run(tmp_path: Path) -> None:
    settings = AppSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "empty.sqlite3",
    )
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    audit_service = AuditService(AuditRepository(database))
    guardrail_service = GuardrailService(GuardrailRepository(database), audit_service)
    scenario_repository = ScenarioRepository(database)
    scenario_service = ScenarioService(
        repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Empty Scenario")
    )
    target_repository = TargetRepository(database)
    ranking_repository = RankingRepository(database)
    ranking_service = RankingService(
        repository=ranking_repository,
        target_repository=target_repository,
        weaponeering_repository=WeaponeeringRepository(database),
        logistics_repository=LogisticsRepository(database),
        audit_service=audit_service,
    )
    export_service = ExportService(
        repository=ExportRepository(database),
        scenario_repository=scenario_repository,
        target_repository=target_repository,
        weaponeering_repository=WeaponeeringRepository(database),
        logistics_repository=LogisticsRepository(database),
        ranking_repository=ranking_repository,
        ranking_service=ranking_service,
        ai_repository=AiRepository(database),
        audit_repository=AuditRepository(database),
        guardrail_repository=GuardrailRepository(database),
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    result = export_service.check_readiness(
        ExportReadinessRequest(scenario_id=scenario_id, export_type="ranking_table")
    )
    assert not result.ready
    assert any("ranking run" in b.lower() for b in result.blockers)


def test_scenario_brief_export_writes_file(tmp_path: Path) -> None:
    scenario_id, export_service, _ = build_export_service(tmp_path)
    out_dir = tmp_path / "exports"
    package = export_service.create_export(
        CreateExportRequest(
            scenario_id=scenario_id,
            export_type="scenario_brief",
            export_format="markdown",
            destination_dir=out_dir,
        )
    )
    assert package.export_status == "exported"
    assert Path(package.destination_path).exists()
    content = Path(package.destination_path).read_text(encoding="utf-8")
    assert "SIMULATION-ONLY" in content
    assert "Phase 6 Export Scenario" in content


def test_ranking_compare_and_replay(tmp_path: Path) -> None:
    scenario_id, export_service, ranking_service = build_export_service(tmp_path)
    first_run = ranking_service.run_ranking(RunRankingRequest(scenario_id=scenario_id))
    second_run = ranking_service.run_ranking(RunRankingRequest(scenario_id=scenario_id))

    comparison = export_service.compare_ranking_runs(
        CompareRankingRequest(
            scenario_id=scenario_id,
            run_a_id=first_run.run.id,
            run_b_id=second_run.run.id,
        )
    )
    assert comparison.rows
    assert comparison.summary

    replay = export_service.replay_ranking(
        ReplayRankingRequest(
            scenario_id=scenario_id,
            ranking_run_id=first_run.run.id,
        )
    )
    assert replay.replay_run_id
    assert replay.summary


def test_aar_generation_creates_action_items(tmp_path: Path) -> None:
    scenario_id, export_service, _ = build_export_service(tmp_path)
    text, items = export_service.generate_aar(scenario_id)
    assert "After-Action Review" in text
    assert "SIMULATION-ONLY" in text
    stored = export_service.list_action_items(scenario_id)
    assert len(stored) >= len(items)
