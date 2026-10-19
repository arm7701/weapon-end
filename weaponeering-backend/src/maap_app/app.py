from __future__ import annotations

from dataclasses import dataclass

from maap_app.config.ai_settings import AiSettings
from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.ai.context import ContextBundleBuilder
from maap_app.modules.ai.repository import AiRepository
from maap_app.modules.ai.service import AiAssistantService
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.logistics.service import LogisticsService
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.ranking.service import RankingService
from maap_app.modules.export.repository import ExportRepository
from maap_app.modules.export.service import ExportService
from maap_app.modules.review.service import HumanReviewService
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.service import TargetService
from maap_app.modules.weaponeering.repository import WeaponeeringRepository
from maap_app.modules.weaponeering.service import WeaponeeringService
from maap_app.modules.wing_data.repository import WingDataRepository
from maap_app.modules.wing_data.service import WingDataService
from maap_app.modules.detection.repository import TargetDetectionRepository
from maap_app.modules.detection.persistence_service import TargetDetectionService
from maap_app.modules.team_marker.repository import TeamMarkerRepository
from maap_app.modules.team_marker.service import TeamMarkerService
from maap_app.modules.ground_transport.repository import GroundTransportRepository
from maap_app.modules.ground_transport.service import GroundTransportService


@dataclass(frozen=True)
class AppContext:
    settings: AppSettings
    database: SQLiteDatabase
    audit_service: AuditService
    guardrail_service: GuardrailService
    scenario_service: ScenarioService
    target_service: TargetService
    logistics_service: LogisticsService
    weaponeering_service: WeaponeeringService
    ranking_service: RankingService
    ai_service: AiAssistantService
    review_service: HumanReviewService
    export_service: ExportService
    wing_data_service: WingDataService
    target_detection_service: TargetDetectionService
    team_marker_service: TeamMarkerService
    ground_transport_service: GroundTransportService


def create_app_context() -> AppContext:
    settings = AppSettings.load()
    database = SQLiteDatabase(settings.database_path)
    database.initialize()

    audit_repository = AuditRepository(database)
    guardrail_repository = GuardrailRepository(database)
    scenario_repository = ScenarioRepository(database)

    audit_service = AuditService(audit_repository)
    guardrail_service = GuardrailService(guardrail_repository, audit_service)
    scenario_service = ScenarioService(
        repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    target_repository = TargetRepository(database)
    logistics_repository = LogisticsRepository(database)
    weaponeering_repository = WeaponeeringRepository(database)
    wing_data_repository = WingDataRepository(database)
    ranking_repository = RankingRepository(database)
    ai_repository = AiRepository(database)
    target_detection_repository = TargetDetectionRepository(database)

    target_service = TargetService(
        repository=target_repository,
        scenario_repository=scenario_repository,
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
        wing_data_repository=wing_data_repository,
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
    ai_settings = AiSettings.load(settings.data_dir)
    context_builder = ContextBundleBuilder(
        scenario_repository=scenario_repository,
        target_repository=target_repository,
        weaponeering_repository=weaponeering_repository,
        logistics_repository=logistics_repository,
        ranking_repository=ranking_repository,
        detection_repository=target_detection_repository,
        wing_data_repository=wing_data_repository,
    )
    ai_service = AiAssistantService(
        repository=ai_repository,
        context_builder=context_builder,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
        ai_settings=ai_settings,
    )
    review_service = HumanReviewService(
        target_repository=target_repository,
        ai_repository=ai_repository,
        weaponeering_repository=weaponeering_repository,
        ranking_repository=ranking_repository,
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

    wing_data_service = WingDataService(
        repository=wing_data_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    target_detection_service = TargetDetectionService(
        repository=target_detection_repository,
        target_repository=target_repository,
        audit_service=audit_service,
    )
    team_marker_repository = TeamMarkerRepository(database)
    team_marker_service = TeamMarkerService(
        repository=team_marker_repository,
        scenario_repository=scenario_repository,
        audit_service=audit_service,
    )
    ground_transport_repository = GroundTransportRepository(database)
    ground_transport_service = GroundTransportService(
        repository=ground_transport_repository,
        wing_data_service=wing_data_service,
        scenario_repository=scenario_repository,
        audit_service=audit_service,
    )

    return AppContext(
        settings=settings,
        database=database,
        audit_service=audit_service,
        guardrail_service=guardrail_service,
        scenario_service=scenario_service,
        target_service=target_service,
        logistics_service=logistics_service,
        weaponeering_service=weaponeering_service,
        ranking_service=ranking_service,
        ai_service=ai_service,
        review_service=review_service,
        export_service=export_service,
        wing_data_service=wing_data_service,
        target_detection_service=target_detection_service,
        team_marker_service=team_marker_service,
        ground_transport_service=ground_transport_service,
    )
