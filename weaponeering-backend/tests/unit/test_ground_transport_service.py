from __future__ import annotations

from pathlib import Path

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.ground_transport.models import GroundRouteResult
from maap_app.modules.ground_transport.repository import GroundTransportRepository
from maap_app.modules.ground_transport.schemas import CreateGroundTransportRequest
from maap_app.modules.ground_transport.service import GroundTransportService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.wing_data.repository import WingDataRepository
from maap_app.modules.wing_data.schemas import CreateAirWingRequest
from maap_app.modules.wing_data.service import WingDataService
import pytest
from unittest.mock import patch


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
    wing_data_service = WingDataService(
        repository=WingDataRepository(database),
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    ground_transport_service = GroundTransportService(
        repository=GroundTransportRepository(database),
        wing_data_service=wing_data_service,
        scenario_repository=scenario_repository,
        audit_service=audit_service,
    )
    return scenario_service, wing_data_service, ground_transport_service


def test_create_ground_transport_between_wings(tmp_path: Path) -> None:
    scenario_service, wing_data_service, ground_transport_service = _build_services(
        tmp_path
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Ground Transport Scenario")
    )
    origin_id = wing_data_service.create_wing(
        CreateAirWingRequest(
            scenario_id=scenario_id,
            wing_name="Wing Alpha",
            map_lat=13.75,
            map_lng=100.50,
        )
    )
    destination_id = wing_data_service.create_wing(
        CreateAirWingRequest(
            scenario_id=scenario_id,
            wing_name="Wing Bravo",
            map_lat=14.10,
            map_lng=100.80,
        )
    )

    transport_id = ground_transport_service.create_transport(
        CreateGroundTransportRequest(
            scenario_id=scenario_id,
            origin_wing_id=origin_id,
            destination_wing_id=destination_id,
            quantity=2,
        )
    )

    transports = ground_transport_service.list_transports(scenario_id)
    assert len(transports) == 1
    assert transports[0].id == transport_id
    assert transports[0].distance_m > 0
    assert transports[0].duration_min > 0
    assert transports[0].route_mode in {"road", "direct"}

    routes = ground_transport_service.list_map_routes(
        scenario_id,
        selected_id=transport_id,
    )
    assert len(routes) == 1
    assert routes[0]["selected"] is True
    assert routes[0]["originWingName"] == "Wing Alpha"
    assert routes[0]["destinationWingName"] == "Wing Bravo"
    assert len(routes[0]["path"]) >= 2


@patch(
    "maap_app.modules.ground_transport.service.resolve_ground_route",
    return_value=GroundRouteResult(
        distance_m=15000.0,
        duration_min=20.0,
        path=((13.75, 100.5), (13.9, 100.65), (14.1, 100.8)),
        route_mode="road",
    ),
)
def test_create_transport_stores_road_geometry(_mock_route, tmp_path: Path) -> None:
    scenario_service, wing_data_service, ground_transport_service = _build_services(
        tmp_path
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Road Geometry Scenario")
    )
    origin_id = wing_data_service.create_wing(
        CreateAirWingRequest(
            scenario_id=scenario_id,
            wing_name="Wing Alpha",
            map_lat=13.75,
            map_lng=100.50,
        )
    )
    destination_id = wing_data_service.create_wing(
        CreateAirWingRequest(
            scenario_id=scenario_id,
            wing_name="Wing Bravo",
            map_lat=14.10,
            map_lng=100.80,
        )
    )

    transport_id = ground_transport_service.create_transport(
        CreateGroundTransportRequest(
            scenario_id=scenario_id,
            origin_wing_id=origin_id,
            destination_wing_id=destination_id,
        )
    )

    transport = ground_transport_service.list_transports(scenario_id)[0]
    assert transport.id == transport_id
    assert transport.route_mode == "road"
    routes = ground_transport_service.list_map_routes(scenario_id)
    assert len(routes[0]["path"]) == 3


def test_ground_transport_rejects_same_wing(tmp_path: Path) -> None:
    scenario_service, wing_data_service, ground_transport_service = _build_services(
        tmp_path
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Same Wing Scenario")
    )
    wing_id = wing_data_service.create_wing(
        CreateAirWingRequest(
            scenario_id=scenario_id,
            wing_name="Wing Alpha",
            map_lat=13.75,
            map_lng=100.50,
        )
    )
    with pytest.raises(ValueError, match="ต้นทางและปลายทาง"):
        ground_transport_service.create_transport(
            CreateGroundTransportRequest(
                scenario_id=scenario_id,
                origin_wing_id=wing_id,
                destination_wing_id=wing_id,
            )
        )
