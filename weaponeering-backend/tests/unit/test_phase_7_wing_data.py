from __future__ import annotations

from pathlib import Path

import pytest

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.wing_data.repository import WingDataRepository
from maap_app.modules.wing_data.schemas import (
    CreateAircraftRequest,
    CreateAirWingRequest,
    CreateFlyingUnitRequest,
    CreateLogisticsVehicleRequest,
    CreatePilotRequest,
    CreateWingDepotRequest,
    CreateWingProductRequest,
    TransferDepotInventoryRequest,
    UpdateAirWingRequest,
    UpsertDepotInventoryRequest,
)
from maap_app.modules.wing_data.service import WingDataService


def build_wing_data_service(tmp_path: Path) -> tuple[str, WingDataService]:
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
    wing_data_service = WingDataService(
        repository=WingDataRepository(database),
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Phase 7 Wing Data Scenario")
    )
    return scenario_id, wing_data_service


def test_wing_data_crud_inventory_and_transfer(tmp_path: Path) -> None:
    scenario_id, service = build_wing_data_service(tmp_path)

    wing_id = service.create_wing(
        CreateAirWingRequest(
            scenario_id=scenario_id,
            wing_name="กองบิน 1",
            map_lat=16.81230,
            map_lng=100.26000,
        )
    )
    depot_a = service.create_depot(
        CreateWingDepotRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            depot_name="คลัง A",
            map_lat=16.82000,
            map_lng=100.27000,
        )
    )
    depot_b = service.create_depot(
        CreateWingDepotRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            depot_name="คลัง B",
            map_lat=16.83000,
            map_lng=100.28000,
        )
    )
    product_id = service.create_product(
        CreateWingProductRequest(
            scenario_id=scenario_id,
            product_name="MK-82",
            weight_pounds=500,
            unit_cost=125_000.0,
        )
    )

    service.upsert_inventory(
        UpsertDepotInventoryRequest(
            scenario_id=scenario_id,
            depot_id=depot_a,
            product_id=product_id,
            quantity=20,
        )
    )
    inventory = service.list_inventory(scenario_id)
    assert len(inventory) == 1
    assert inventory[0].quantity == 20
    assert inventory[0].depot_name == "คลัง A"

    service.transfer_inventory(
        TransferDepotInventoryRequest(
            scenario_id=scenario_id,
            from_depot_id=depot_a,
            to_depot_id=depot_b,
            product_id=product_id,
            quantity=8,
        )
    )
    inventory = service.list_inventory(scenario_id)
    by_depot = {row.depot_name: row.quantity for row in inventory}
    assert by_depot["คลัง A"] == 12
    assert by_depot["คลัง B"] == 8

    layers = service.list_map_layers(scenario_id)
    assert len(layers["wings"]) == 1
    assert len(layers["depots"]) == 2

    flying_unit_id = service.create_flying_unit(
        CreateFlyingUnitRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            unit_name="ฝูง 1",
        )
    )
    aircraft_id = service.create_aircraft(
        CreateAircraftRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            aircraft_type="F-16",
            flying_unit_id=flying_unit_id,
            mission_ready="ready",
        )
    )
    pilot_id = service.create_pilot(
        CreatePilotRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            flying_unit_id=flying_unit_id,
            pilot_name="น.อ. ทดสอบ",
            callsign="VIPER-1",
            cep_value=120.0,
        )
    )
    wing_detail = service.get_wing_map_detail(wing_id, scenario_id)
    assert wing_detail is not None
    assert wing_detail.aircraft_ready_count == 1
    assert len(wing_detail.aircraft) == 1
    assert wing_detail.aircraft[0].id == aircraft_id
    assert len(wing_detail.flying_units) == 1
    assert len(wing_detail.pilots) == 1
    assert wing_detail.pilots[0].id == pilot_id
    counts = service.list_wing_table_summaries(scenario_id)
    summary = counts[wing_id]
    assert summary.flying_unit_count == 1
    assert summary.aircraft_count == 1
    assert summary.pilot_count == 1
    assert summary.depot_count == 2
    assert summary.product_stock == (("MK-82", 20),)
    assert len(wing_detail.inventory) == 2
    assert {row.depot_name for row in wing_detail.inventory} == {"คลัง A", "คลัง B"}

    service.update_wing(
        UpdateAirWingRequest(
            wing_id=wing_id,
            wing_name="กองบิน 1 (แก้ไข)",
            map_lat=16.81230,
            map_lng=100.26000,
        )
    )

    aircraft_id = service.create_aircraft(
        CreateAircraftRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            aircraft_type="F-16",
            flying_unit_id=flying_unit_id,
            mission_ready="ready",
        )
    )
    pilot_id = service.create_pilot(
        CreatePilotRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            flying_unit_id=flying_unit_id,
            pilot_name="น.อ. สมชาย",
            callsign="VIPER-1",
            cep_value=12.5,
        )
    )
    vehicle_id = service.create_vehicle(
        CreateLogisticsVehicleRequest(
            scenario_id=scenario_id,
            wing_id=wing_id,
            vehicle_name="รถบรรทุกน้ำมัน 1",
            fuel_consumption_rate=12.5,
            mission_ready="not_ready",
        )
    )

    assert service.get_depot(depot_a) is not None
    assert service.get_product(product_id) is not None
    assert service.get_aircraft(aircraft_id) is not None
    assert service.get_pilot(pilot_id) is not None
    assert service.get_vehicle(vehicle_id) is not None
    counts = service.list_wing_table_summaries(scenario_id)
    summary = counts[wing_id]
    assert summary.flying_unit_count == 1
    assert summary.aircraft_count == 2
    assert summary.pilot_count == 2
    assert summary.depot_count == 2
    assert summary.product_stock == (("MK-82", 20),)

    with pytest.raises(ValueError):
        service.transfer_inventory(
            TransferDepotInventoryRequest(
                scenario_id=scenario_id,
                from_depot_id=depot_b,
                to_depot_id=depot_a,
                product_id=product_id,
                quantity=999,
            )
        )
