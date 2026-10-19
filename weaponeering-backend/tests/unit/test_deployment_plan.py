from __future__ import annotations

from pathlib import Path

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.schemas import (
    CreateTargetCardRequest,
    LinkTargetMapNodeRequest,
)
from maap_app.modules.target.service import TargetService
from maap_app.modules.weaponeering.repository import WeaponeeringRepository
from maap_app.modules.weaponeering.schemas import (
    DeploymentAircraftLineRequest,
    DeploymentWaypointRequest,
    UpsertDeploymentPlanRequest,
)
from maap_app.modules.weaponeering.service import WeaponeeringService
from maap_app.modules.wing_data.repository import WingDataRepository
from maap_app.modules.wing_data.schemas import (
    CreateAircraftRequest,
    CreateAirWingRequest,
    CreateFlyingUnitRequest,
)
from maap_app.modules.wing_data.service import WingDataService


def _build_services(tmp_path: Path):
    settings = AppSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.sqlite3",
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
    target_repository = TargetRepository(database)
    target_service = TargetService(
        repository=target_repository,
        scenario_repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    wing_data_repository = WingDataRepository(database)
    wing_data_service = WingDataService(
        repository=wing_data_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    weaponeering_service = WeaponeeringService(
        repository=WeaponeeringRepository(database),
        target_repository=target_repository,
        wing_data_repository=wing_data_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    return scenario_service, target_service, wing_data_service, weaponeering_service


def test_deployment_plan_upsert_and_reload(tmp_path: Path) -> None:
    scenario_service, target_service, wing_data_service, weaponeering_service = (
        _build_services(tmp_path)
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Deployment Plan Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-PLAN")
    )
    wing_id = wing_data_service.create_wing(
        CreateAirWingRequest(
            scenario_id=scenario_id,
            wing_name="กองบิน 1",
            map_lat=16.81,
            map_lng=100.12,
        )
    )
    unit_id = wing_data_service.create_flying_unit(
        CreateFlyingUnitRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            unit_name="ฝูง 1",
        )
    )
    aircraft_id = wing_data_service.create_aircraft(
        CreateAircraftRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            aircraft_type="F-16",
            flying_unit_id=unit_id,
            mission_ready="ready",
        )
    )

    plan_id = weaponeering_service.upsert_deployment_plan(
        UpsertDeploymentPlanRequest(
            scenario_id=scenario_id,
            target_card_id=target_id,
            wing_id=wing_id,
            flying_unit_id=unit_id,
            aircraft_lines=(
                DeploymentAircraftLineRequest(
                    aircraft_id=aircraft_id,
                    aircraft_count=4,
                ),
            ),
        )
    )
    loaded = weaponeering_service.get_deployment_plan_for_target(target_id)
    assert loaded is not None
    assert loaded.id == plan_id
    assert loaded.total_aircraft_count == 4
    assert loaded.wing_id == wing_id
    assert loaded.flying_unit_id == unit_id
    assert len(loaded.aircraft_lines) == 1
    assert loaded.aircraft_lines[0].aircraft_id == aircraft_id
    assert loaded.aircraft_lines[0].aircraft_count == 4

    weaponeering_service.upsert_deployment_plan(
        UpsertDeploymentPlanRequest(
            scenario_id=scenario_id,
            target_card_id=target_id,
            wing_id=wing_id,
            flying_unit_id=unit_id,
            aircraft_lines=(
                DeploymentAircraftLineRequest(
                    aircraft_id=aircraft_id,
                    aircraft_count=2,
                ),
            ),
        )
    )
    updated = weaponeering_service.get_deployment_plan_for_target(target_id)
    assert updated is not None
    assert updated.id == plan_id
    assert updated.total_aircraft_count == 2
    assert updated.aircraft_lines[0].aircraft_count == 2


def test_deployment_plan_multiple_aircraft_lines(tmp_path: Path) -> None:
    scenario_service, target_service, wing_data_service, weaponeering_service = (
        _build_services(tmp_path)
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Multi Aircraft Plan")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-MULTI")
    )
    wing_id = wing_data_service.create_wing(
        CreateAirWingRequest(
            scenario_id=scenario_id,
            wing_name="กองบิน 2",
            map_lat=16.82,
            map_lng=100.13,
        )
    )
    unit_id = wing_data_service.create_flying_unit(
        CreateFlyingUnitRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            unit_name="ฝูง 2",
        )
    )
    f16_id = wing_data_service.create_aircraft(
        CreateAircraftRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            aircraft_type="F-16",
            flying_unit_id=unit_id,
            mission_ready="ready",
        )
    )
    f35_id = wing_data_service.create_aircraft(
        CreateAircraftRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            aircraft_type="F-35",
            flying_unit_id=unit_id,
            mission_ready="ready",
        )
    )

    weaponeering_service.upsert_deployment_plan(
        UpsertDeploymentPlanRequest(
            scenario_id=scenario_id,
            target_card_id=target_id,
            wing_id=wing_id,
            flying_unit_id=unit_id,
            aircraft_lines=(
                DeploymentAircraftLineRequest(aircraft_id=f16_id, aircraft_count=2),
                DeploymentAircraftLineRequest(aircraft_id=f35_id, aircraft_count=3),
            ),
        )
    )
    loaded = weaponeering_service.get_deployment_plan_for_target(target_id)
    assert loaded is not None
    assert loaded.total_aircraft_count == 5
    assert len(loaded.aircraft_lines) == 2
    assert loaded.aircraft_lines[0].aircraft_id == f16_id
    assert loaded.aircraft_lines[0].aircraft_count == 2
    assert loaded.aircraft_lines[1].aircraft_id == f35_id
    assert loaded.aircraft_lines[1].aircraft_count == 3


def test_deployment_plan_map_links_require_coordinates(tmp_path: Path) -> None:
    scenario_service, target_service, wing_data_service, weaponeering_service = (
        _build_services(tmp_path)
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Map Link Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-LINK")
    )
    wing_id = wing_data_service.create_wing(
        CreateAirWingRequest(
            scenario_id=scenario_id,
            wing_name="กองบิน 3",
            map_lat=16.80,
            map_lng=100.10,
        )
    )
    unit_id = wing_data_service.create_flying_unit(
        CreateFlyingUnitRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            unit_name="ฝูง 3",
        )
    )
    aircraft_id = wing_data_service.create_aircraft(
        CreateAircraftRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            aircraft_type="F-16",
            flying_unit_id=unit_id,
            mission_ready="ready",
        )
    )

    assert weaponeering_service.list_map_deployment_links(scenario_id) == []

    weaponeering_service.upsert_deployment_plan(
        UpsertDeploymentPlanRequest(
            scenario_id=scenario_id,
            target_card_id=target_id,
            wing_id=wing_id,
            flying_unit_id=unit_id,
            aircraft_lines=(
                DeploymentAircraftLineRequest(aircraft_id=aircraft_id, aircraft_count=2),
            ),
        )
    )
    assert weaponeering_service.list_map_deployment_links(scenario_id) == []

    target_service.link_target_to_map(
        LinkTargetMapNodeRequest(
            target_card_id=target_id,
            scenario_id=scenario_id,
            map_lat=16.85,
            map_lng=100.15,
        )
    )
    links = weaponeering_service.list_map_deployment_links(scenario_id)
    assert len(links) == 1
    assert links[0]["targetCardId"] == target_id
    assert links[0]["wingId"] == wing_id
    assert links[0]["origin"] == [16.80, 100.10]
    assert links[0]["destination"] == [16.85, 100.15]
    assert links[0]["aircraftCount"] == 2
    assert "กองบิน 3" in links[0]["label"]
    assert "TGT-LINK" in links[0]["label"]


def test_deployment_plan_flight_path_persists_and_renders_on_map(tmp_path: Path) -> None:
    scenario_service, target_service, wing_data_service, weaponeering_service = (
        _build_services(tmp_path)
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Flight Path Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-FLIGHT")
    )
    target_service.link_target_to_map(
        LinkTargetMapNodeRequest(
            target_card_id=target_id,
            scenario_id=scenario_id,
            map_lat=16.85,
            map_lng=100.15,
        )
    )
    wing_id = wing_data_service.create_wing(
        CreateAirWingRequest(
            scenario_id=scenario_id,
            wing_name="กองบิน 4",
            map_lat=16.80,
            map_lng=100.10,
        )
    )
    unit_id = wing_data_service.create_flying_unit(
        CreateFlyingUnitRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            unit_name="ฝูง 4",
        )
    )
    aircraft_id = wing_data_service.create_aircraft(
        CreateAircraftRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            aircraft_type="F-16",
            flying_unit_id=unit_id,
            mission_ready="ready",
        )
    )

    weaponeering_service.upsert_deployment_plan(
        UpsertDeploymentPlanRequest(
            scenario_id=scenario_id,
            target_card_id=target_id,
            wing_id=wing_id,
            flying_unit_id=unit_id,
            aircraft_lines=(
                DeploymentAircraftLineRequest(aircraft_id=aircraft_id, aircraft_count=1),
            ),
            ingress_bearing_deg=90.0,
            ingress_offset_m=8000,
            cruise_altitude_ft=25000,
            ingress_altitude_ft=5000,
            target_altitude_ft=1500,
            waypoints=(
                DeploymentWaypointRequest(
                    lat=16.82,
                    lng=100.12,
                    label="Corridor",
                    altitude_ft=24000,
                ),
            ),
        )
    )

    loaded = weaponeering_service.get_deployment_plan_for_target(target_id)
    assert loaded is not None
    assert loaded.ingress_bearing_deg == 90.0
    assert loaded.cruise_altitude_ft == 25000
    assert loaded.return_enabled is True
    assert len(loaded.waypoints) == 1
    assert loaded.waypoints[0].altitude_ft == 24000

    links = weaponeering_service.list_map_deployment_links(scenario_id)
    assert len(links) == 1
    assert len(links[0]["outboundRoute"]) >= 2
    assert len(links[0]["returnRoute"]) >= 2
    assert links[0]["routeMarkers"]
    assert any(marker["routeCode"] == "DEP" for marker in links[0]["routeMarkers"])
    assert any(marker["routeCode"] == "TGT" for marker in links[0]["routeMarkers"])
    assert links[0]["cruiseAltitudeFt"] == 25000
    assert links[0]["totalDurationMin"] > 0
    assert links[0]["profileSegments"]
