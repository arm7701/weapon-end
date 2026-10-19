from __future__ import annotations

from pathlib import Path

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.logistics.schemas import (
    CalculateLogisticsRequest,
    CreateDepotRequest,
    CreateOrganizationRequest,
    CreateRouteSegmentRequest,
    CreateSimulatedPlatformRequest,
    CreateTransportAssetRequest,
    UpdatePlatformReadinessRequest,
)
from maap_app.modules.logistics.service import LogisticsService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService


def build_logistics_service(tmp_path: Path) -> tuple[str, LogisticsService]:
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
    logistics_service = LogisticsService(
        repository=LogisticsRepository(database),
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Phase 3 Scenario")
    )
    return scenario_id, logistics_service


def test_organization_depot_route_and_logistics_score(tmp_path: Path) -> None:
    scenario_id, service = build_logistics_service(tmp_path)

    org_id = service.create_organization(
        CreateOrganizationRequest(
            scenario_id=scenario_id,
            name="ORG-ALPHA",
            map_lat=16.81,
            map_lng=100.12,
        )
    )
    platform_id = service.create_simulated_platform(
        CreateSimulatedPlatformRequest(
            scenario_id=scenario_id,
            label="PLAT-01",
            organization_id=org_id,
        )
    )
    service.update_platform_readiness(
        UpdatePlatformReadinessRequest(
            platform_id=platform_id,
            readiness_status="ready",
            readiness_score=85,
            reason="Synthetic training readiness inject",
        )
    )
    depot_id = service.create_depot(
        CreateDepotRequest(
            scenario_id=scenario_id,
            name="DEPOT-NORTH",
            map_lat=16.82,
            map_lng=100.13,
        )
    )
    service.create_transport_asset(
        CreateTransportAssetRequest(
            scenario_id=scenario_id,
            label="TRUCK-01",
            organization_id=org_id,
            readiness_status="ready",
        )
    )
    route_id = service.create_route_segment(
        CreateRouteSegmentRequest(
            scenario_id=scenario_id,
            origin_entity_type="organization",
            origin_entity_id=org_id,
            destination_entity_type="depot",
            destination_entity_id=depot_id,
            origin_lat=16.81,
            origin_lng=100.12,
            destination_lat=16.82,
            destination_lng=100.13,
            route_friction_score=35,
            fuel_stop_score=70,
        )
    )

    result = service.calculate_logistics_feasibility(
        CalculateLogisticsRequest(scenario_id=scenario_id, route_segment_id=route_id)
    )
    layers = service.list_map_layers(scenario_id)

    assert result.score >= 1
    assert result.plan_score_id is not None
    assert len(layers["organizations"]) == 1
    assert len(layers["depots"]) == 1
    assert len(layers["routes"]) == 1


def test_logistics_guardrail_blocks_operational_language(tmp_path: Path) -> None:
    scenario_id, service = build_logistics_service(tmp_path)
    blocked = False
    try:
        service.create_organization(
            CreateOrganizationRequest(
                scenario_id=scenario_id,
                name="real unit location at grid 12345",
            )
        )
    except ValueError:
        blocked = True
    assert blocked
