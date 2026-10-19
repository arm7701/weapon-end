from __future__ import annotations

from uuid import uuid4

from maap_app.modules.audit.service import AuditService
from maap_app.modules.geo_utils import haversine_distance_km, km_to_nm
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.weaponeering.product_catalog import catalog_description
from maap_app.modules.wing_data.models import (
    WingDistanceResult,
    WingMapDetail,
    WingTableSummary,
)
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
    UpdateAircraftRequest,
    UpdateAirWingRequest,
    UpdateFlyingUnitRequest,
    UpdateLogisticsVehicleRequest,
    UpdatePilotRequest,
    UpdateWingDepotRequest,
    UpdateWingProductRequest,
    UpsertDepotInventoryRequest,
)


class WingDataService:
    def __init__(
        self,
        repository: WingDataRepository,
        guardrail_service: GuardrailService,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.guardrail_service = guardrail_service
        self.audit_service = audit_service

    def _validate(self, text: str, entity_type: str, entity_id: str) -> None:
        if not self.guardrail_service.validate_training_text(
            text=text, entity_type=entity_type, entity_id=entity_id
        ):
            raise ValueError(f"{entity_type} text was blocked by guardrail validation.")

    # --- Wing ---
    def create_wing(self, request: CreateAirWingRequest) -> str:
        wing_id = str(uuid4())
        self._validate(request.wing_name, "air_wing", wing_id)
        self.repository.insert_wing(
            wing_id, request.scenario_id, request.wing_name,
            request.map_lat, request.map_lng,
        )
        self.audit_service.record_event(
            "local_user", "air_wing_created", "air_wing", wing_id,
            {"wing_name": request.wing_name},
        )
        return wing_id

    def update_wing(self, request: UpdateAirWingRequest) -> None:
        self._validate(request.wing_name, "air_wing", request.wing_id)
        self.repository.update_wing(
            request.wing_id, request.wing_name, request.map_lat, request.map_lng,
        )
        self.audit_service.record_event(
            "local_user", "air_wing_updated", "air_wing", request.wing_id,
            {"wing_name": request.wing_name},
        )

    def delete_wing(self, wing_id: str) -> None:
        self.repository.archive_wing(wing_id)
        self.audit_service.record_event(
            "local_user", "air_wing_archived", "air_wing", wing_id, {},
        )

    def list_wings(self, scenario_id: str):
        return self.repository.list_wings(scenario_id)

    def list_wing_table_summaries(
        self,
        scenario_id: str,
    ) -> dict[str, WingTableSummary]:
        summaries: dict[str, dict[str, int | dict[str, int]]] = {
            wing.id: {
                "units": 0,
                "aircraft": 0,
                "pilots": 0,
                "depots": 0,
                "products": {},
            }
            for wing in self.repository.list_wings(scenario_id)
        }
        for unit in self.repository.list_flying_units(scenario_id):
            if unit.wing_id in summaries:
                summaries[unit.wing_id]["units"] += 1
        for aircraft in self.repository.list_aircraft(scenario_id):
            if aircraft.wing_id in summaries:
                summaries[aircraft.wing_id]["aircraft"] += 1
        for pilot in self.repository.list_pilots(scenario_id):
            if pilot.wing_id and pilot.wing_id in summaries:
                summaries[pilot.wing_id]["pilots"] += 1
        depots = self.repository.list_depots(scenario_id)
        depot_to_wing = {}
        for depot in depots:
            depot_to_wing[depot.id] = depot.wing_id
            if depot.wing_id in summaries:
                summaries[depot.wing_id]["depots"] += 1
        for row in self.repository.list_inventory(scenario_id):
            wing_id = depot_to_wing.get(row.depot_id)
            if wing_id not in summaries:
                continue
            products = summaries[wing_id]["products"]
            products[row.product_name] = products.get(row.product_name, 0) + row.quantity
        return {
            wing_id: WingTableSummary(
                flying_unit_count=int(values["units"]),
                aircraft_count=int(values["aircraft"]),
                pilot_count=int(values["pilots"]),
                depot_count=int(values["depots"]),
                product_stock=tuple(
                    sorted(values["products"].items(), key=lambda item: item[0].lower())
                ),
            )
            for wing_id, values in summaries.items()
        }

    def get_wing(self, wing_id: str):
        return self.repository.get_wing(wing_id)

    def _validate_flying_unit_for_wing(
        self,
        flying_unit_id: str | None,
        wing_id: str | None,
        scenario_id: str,
    ) -> None:
        if not flying_unit_id:
            return
        unit = self.repository.get_flying_unit(flying_unit_id)
        if unit is None or unit.scenario_id != scenario_id:
            raise ValueError("ไม่พบหน่วยบินที่เลือก")
        if wing_id and unit.wing_id != wing_id:
            raise ValueError("หน่วยบินต้องอยู่ภายใต้กองบินเดียวกัน")

    # --- Flying unit ---
    def create_flying_unit(self, request: CreateFlyingUnitRequest) -> str:
        flying_unit_id = str(uuid4())
        self._validate(request.unit_name, "wing_flying_unit", flying_unit_id)
        self.repository.insert_flying_unit(
            flying_unit_id,
            request.scenario_id,
            request.wing_id,
            request.unit_name,
            request.map_lat,
            request.map_lng,
        )
        self.audit_service.record_event(
            "local_user",
            "wing_flying_unit_created",
            "wing_flying_unit",
            flying_unit_id,
            {"unit_name": request.unit_name},
        )
        return flying_unit_id

    def update_flying_unit(self, request: UpdateFlyingUnitRequest) -> None:
        self._validate(request.unit_name, "wing_flying_unit", request.flying_unit_id)
        self.repository.update_flying_unit(
            request.flying_unit_id,
            request.wing_id,
            request.unit_name,
            request.map_lat,
            request.map_lng,
        )
        self.audit_service.record_event(
            "local_user",
            "wing_flying_unit_updated",
            "wing_flying_unit",
            request.flying_unit_id,
            {"unit_name": request.unit_name},
        )

    def delete_flying_unit(self, flying_unit_id: str) -> None:
        self.repository.archive_flying_unit(flying_unit_id)
        self.audit_service.record_event(
            "local_user",
            "wing_flying_unit_archived",
            "wing_flying_unit",
            flying_unit_id,
            {},
        )

    def list_flying_units(self, scenario_id: str):
        return self.repository.list_flying_units(scenario_id)

    def get_flying_unit(self, flying_unit_id: str):
        return self.repository.get_flying_unit(flying_unit_id)

    def get_wing_map_detail(self, wing_id: str, scenario_id: str) -> WingMapDetail | None:
        wing = self.repository.get_wing(wing_id)
        if wing is None or wing.scenario_id != scenario_id:
            return None
        depot_ids = {
            depot.id
            for depot in self.repository.list_depots(scenario_id)
            if depot.wing_id == wing_id
        }
        flying_units = tuple(
            row
            for row in self.repository.list_flying_units(scenario_id)
            if row.wing_id == wing_id
        )
        aircraft = tuple(
            row
            for row in self.repository.list_aircraft(scenario_id)
            if row.wing_id == wing_id
        )
        pilots = tuple(
            row
            for row in self.repository.list_pilots(scenario_id)
            if row.wing_id == wing_id
        )
        inventory = tuple(
            row
            for row in self.repository.list_inventory(scenario_id)
            if row.depot_id in depot_ids and row.quantity > 0
        )
        return WingMapDetail(
            wing=wing,
            flying_units=flying_units,
            aircraft=aircraft,
            pilots=pilots,
            inventory=inventory,
        )

    def find_wings_by_distance(
        self,
        scenario_id: str,
        target_lat: float,
        target_lng: float,
    ) -> list[WingDistanceResult]:
        ranked: list[WingDistanceResult] = []
        for wing in self.repository.list_wings(scenario_id):
            if wing.map_lat is None or wing.map_lng is None:
                continue
            distance_km = haversine_distance_km(
                target_lat,
                target_lng,
                wing.map_lat,
                wing.map_lng,
            )
            ranked.append(
                WingDistanceResult(
                    wing_id=wing.id,
                    wing_name=wing.wing_name,
                    map_lat=wing.map_lat,
                    map_lng=wing.map_lng,
                    distance_km=distance_km,
                    distance_nm=km_to_nm(distance_km),
                )
            )
        ranked.sort(key=lambda row: row.distance_km)
        return [
            WingDistanceResult(
                wing_id=row.wing_id,
                wing_name=row.wing_name,
                map_lat=row.map_lat,
                map_lng=row.map_lng,
                distance_km=row.distance_km,
                distance_nm=row.distance_nm,
                rank=index,
            )
            for index, row in enumerate(ranked, start=1)
        ]

    def find_nearest_wing(
        self,
        scenario_id: str,
        target_lat: float,
        target_lng: float,
    ) -> WingDistanceResult | None:
        ranked = self.find_wings_by_distance(scenario_id, target_lat, target_lng)
        return ranked[0] if ranked else None

    # --- Aircraft ---
    def create_aircraft(self, request: CreateAircraftRequest) -> str:
        aircraft_id = str(uuid4())
        self._validate(request.aircraft_type, "wing_aircraft", aircraft_id)
        self._validate_flying_unit_for_wing(
            request.flying_unit_id,
            request.wing_id,
            request.scenario_id,
        )
        self.repository.insert_aircraft(
            aircraft_id,
            request.scenario_id,
            request.wing_id,
            request.aircraft_type,
            request.flying_unit_id,
            request.mission_ready,
        )
        self.audit_service.record_event(
            "local_user", "wing_aircraft_created", "wing_aircraft", aircraft_id,
            {"aircraft_type": request.aircraft_type},
        )
        return aircraft_id

    def update_aircraft(self, request: UpdateAircraftRequest) -> None:
        existing = self.repository.get_aircraft(request.aircraft_id)
        if existing is None:
            raise ValueError("ไม่พบเครื่องบิน")
        self._validate(request.aircraft_type, "wing_aircraft", request.aircraft_id)
        self._validate_flying_unit_for_wing(
            request.flying_unit_id,
            request.wing_id,
            existing.scenario_id,
        )
        self.repository.update_aircraft(
            request.aircraft_id,
            request.wing_id,
            request.aircraft_type,
            request.flying_unit_id,
            request.mission_ready,
        )
        self.audit_service.record_event(
            "local_user", "wing_aircraft_updated", "wing_aircraft", request.aircraft_id, {},
        )

    def delete_aircraft(self, aircraft_id: str) -> None:
        self.repository.archive_aircraft(aircraft_id)
        self.audit_service.record_event(
            "local_user", "wing_aircraft_archived", "wing_aircraft", aircraft_id, {},
        )

    def list_aircraft(self, scenario_id: str):
        return self.repository.list_aircraft(scenario_id)

    def get_aircraft(self, aircraft_id: str):
        return self.repository.get_aircraft(aircraft_id)

    # --- Pilot ---
    def create_pilot(self, request: CreatePilotRequest) -> str:
        pilot_id = str(uuid4())
        self._validate(f"{request.pilot_name} {request.callsign}", "wing_pilot", pilot_id)
        self._validate_flying_unit_for_wing(
            request.flying_unit_id,
            request.wing_id,
            request.scenario_id,
        )
        self.repository.insert_pilot(
            pilot_id,
            request.scenario_id,
            request.wing_id,
            request.flying_unit_id,
            request.pilot_name,
            request.callsign,
            request.cep_value,
        )
        self.audit_service.record_event(
            "local_user", "wing_pilot_created", "wing_pilot", pilot_id,
            {"pilot_name": request.pilot_name},
        )
        return pilot_id

    def update_pilot(self, request: UpdatePilotRequest) -> None:
        existing = self.repository.get_pilot(request.pilot_id)
        if existing is None:
            raise ValueError("ไม่พบนักบิน")
        self._validate(f"{request.pilot_name} {request.callsign}", "wing_pilot", request.pilot_id)
        self._validate_flying_unit_for_wing(
            request.flying_unit_id,
            request.wing_id,
            existing.scenario_id,
        )
        self.repository.update_pilot(
            request.pilot_id,
            request.wing_id,
            request.flying_unit_id,
            request.pilot_name,
            request.callsign,
            request.cep_value,
        )
        self.audit_service.record_event(
            "local_user", "wing_pilot_updated", "wing_pilot", request.pilot_id, {},
        )

    def delete_pilot(self, pilot_id: str) -> None:
        self.repository.archive_pilot(pilot_id)
        self.audit_service.record_event(
            "local_user", "wing_pilot_archived", "wing_pilot", pilot_id, {},
        )

    def list_pilots(self, scenario_id: str):
        return self.repository.list_pilots(scenario_id)

    def get_pilot(self, pilot_id: str):
        return self.repository.get_pilot(pilot_id)

    # --- Depot ---
    def create_depot(self, request: CreateWingDepotRequest) -> str:
        depot_id = str(uuid4())
        self._validate(request.depot_name, "wing_depot", depot_id)
        self.repository.insert_depot(
            depot_id, request.scenario_id, request.wing_id, request.depot_name,
            request.map_lat, request.map_lng,
        )
        self.audit_service.record_event(
            "local_user", "wing_depot_created", "wing_depot", depot_id,
            {"depot_name": request.depot_name},
        )
        return depot_id

    def update_depot(self, request: UpdateWingDepotRequest) -> None:
        self._validate(request.depot_name, "wing_depot", request.depot_id)
        self.repository.update_depot(
            request.depot_id, request.wing_id, request.depot_name,
            request.map_lat, request.map_lng,
        )
        self.audit_service.record_event(
            "local_user", "wing_depot_updated", "wing_depot", request.depot_id, {},
        )

    def delete_depot(self, depot_id: str) -> None:
        self.repository.archive_depot(depot_id)
        self.audit_service.record_event(
            "local_user", "wing_depot_archived", "wing_depot", depot_id, {},
        )

    def list_depots(self, scenario_id: str):
        return self.repository.list_depots(scenario_id)

    def get_depot(self, depot_id: str):
        return self.repository.get_depot(depot_id)

    # --- Logistics vehicle ---
    def create_vehicle(self, request: CreateLogisticsVehicleRequest) -> str:
        vehicle_id = str(uuid4())
        self._validate(request.vehicle_name, "wing_logistics_vehicle", vehicle_id)
        self.repository.insert_vehicle(
            vehicle_id, request.scenario_id, request.wing_id,
            request.vehicle_name, request.fuel_consumption_rate, request.mission_ready,
        )
        self.audit_service.record_event(
            "local_user", "wing_logistics_vehicle_created", "wing_logistics_vehicle", vehicle_id,
            {"vehicle_name": request.vehicle_name},
        )
        return vehicle_id

    def update_vehicle(self, request: UpdateLogisticsVehicleRequest) -> None:
        self._validate(request.vehicle_name, "wing_logistics_vehicle", request.vehicle_id)
        self.repository.update_vehicle(
            request.vehicle_id, request.wing_id, request.vehicle_name,
            request.fuel_consumption_rate, request.mission_ready,
        )
        self.audit_service.record_event(
            "local_user", "wing_logistics_vehicle_updated", "wing_logistics_vehicle",
            request.vehicle_id, {},
        )

    def delete_vehicle(self, vehicle_id: str) -> None:
        self.repository.archive_vehicle(vehicle_id)
        self.audit_service.record_event(
            "local_user", "wing_logistics_vehicle_archived", "wing_logistics_vehicle",
            vehicle_id, {},
        )

    def list_vehicles(self, scenario_id: str):
        return self.repository.list_vehicles(scenario_id)

    def get_vehicle(self, vehicle_id: str):
        return self.repository.get_vehicle(vehicle_id)

    # --- Product ---
    def create_product(self, request: CreateWingProductRequest) -> str:
        product_id = str(uuid4())
        self._validate(request.product_name, "wing_product", product_id)
        description = request.description.strip() or catalog_description(request.product_name)
        self.repository.insert_product(
            product_id,
            request.scenario_id,
            request.product_name,
            request.weight_pounds,
            request.unit_cost,
            description,
        )
        self.audit_service.record_event(
            "local_user", "wing_product_created", "wing_product", product_id,
            {"product_name": request.product_name},
        )
        return product_id

    def update_product(self, request: UpdateWingProductRequest) -> None:
        self._validate(request.product_name, "wing_product", request.product_id)
        self.repository.update_product(
            request.product_id,
            request.product_name,
            request.weight_pounds,
            request.unit_cost,
            request.description,
        )
        self.audit_service.record_event(
            "local_user", "wing_product_updated", "wing_product", request.product_id, {},
        )

    def delete_product(self, product_id: str) -> None:
        self.repository.archive_product(product_id)
        self.audit_service.record_event(
            "local_user", "wing_product_archived", "wing_product", product_id, {},
        )

    def list_products(self, scenario_id: str):
        return self.repository.list_products(scenario_id)

    def get_product(self, product_id: str):
        return self.repository.get_product(product_id)

    # --- Depot inventory ---
    def upsert_inventory(self, request: UpsertDepotInventoryRequest) -> str:
        if request.quantity < 0:
            raise ValueError("จำนวนสินค้าต้องไม่ต่ำกว่า 0")
        existing = self.repository.get_inventory_row(request.depot_id, request.product_id)
        inventory_id = existing.id if existing else str(uuid4())
        self.repository.upsert_inventory(
            inventory_id, request.scenario_id,
            request.depot_id, request.product_id, request.quantity,
        )
        self.audit_service.record_event(
            "local_user", "wing_depot_inventory_upserted", "wing_depot_inventory",
            inventory_id,
            {
                "depot_id": request.depot_id,
                "product_id": request.product_id,
                "quantity": request.quantity,
            },
        )
        return inventory_id

    def list_inventory(self, scenario_id: str):
        return self.repository.list_inventory(scenario_id)

    def list_transfers(self, scenario_id: str):
        return self.repository.list_transfers(scenario_id)

    def delete_inventory(self, inventory_id: str) -> None:
        self.repository.archive_inventory(inventory_id)
        self.audit_service.record_event(
            "local_user", "wing_depot_inventory_archived", "wing_depot_inventory",
            inventory_id, {},
        )

    def transfer_inventory(self, request: TransferDepotInventoryRequest) -> None:
        if request.from_depot_id == request.to_depot_id:
            raise ValueError("คลังต้นทางและปลายทางต้องไม่ใช่คลังเดียวกัน")
        if request.quantity <= 0:
            raise ValueError("จำนวนที่ย้ายต้องมากกว่า 0")
        source = self.repository.get_inventory_row(request.from_depot_id, request.product_id)
        if not source or source.quantity < request.quantity:
            raise ValueError("จำนวนสินค้าในคลังต้นทางไม่เพียงพอ")
        dest = self.repository.get_inventory_row(request.to_depot_id, request.product_id)
        dest_qty = dest.quantity if dest else 0
        self.repository.adjust_inventory_quantity(
            request.from_depot_id, request.product_id, -request.quantity,
        )
        self.repository.upsert_inventory(
            dest.id if dest else str(uuid4()),
            request.scenario_id,
            request.to_depot_id,
            request.product_id,
            dest_qty + request.quantity,
        )
        transfer_id = str(uuid4())
        self.repository.insert_transfer(
            transfer_id, request.scenario_id, request.product_id,
            request.from_depot_id, request.to_depot_id, request.quantity,
        )
        self.audit_service.record_event(
            "local_user", "wing_depot_inventory_transferred", "wing_depot_transfer",
            transfer_id,
            {
                "from_depot_id": request.from_depot_id,
                "to_depot_id": request.to_depot_id,
                "product_id": request.product_id,
                "quantity": request.quantity,
            },
        )

    def list_map_layers(self, scenario_id: str) -> dict:
        wings = []
        depots = []
        for wing in self.repository.list_wings(scenario_id):
            if wing.map_lat is None or wing.map_lng is None:
                continue
            wings.append({
                "entityId": wing.id,
                "entityType": "air_wing",
                "label": wing.wing_name,
                "lat": wing.map_lat,
                "lng": wing.map_lng,
            })
        for depot in self.repository.list_depots(scenario_id):
            if depot.map_lat is None or depot.map_lng is None:
                continue
            depots.append({
                "entityId": depot.id,
                "entityType": "wing_depot",
                "label": depot.depot_name,
                "lat": depot.map_lat,
                "lng": depot.map_lng,
                "availability": "active",
            })
        return {"wings": wings, "depots": depots}

    def list_map_markers(self, scenario_id: str) -> list[dict]:
        return self.list_map_layers(scenario_id)["wings"]

    def wing_name_map(self, scenario_id: str) -> dict[str, str]:
        return {w.id: w.wing_name for w in self.repository.list_wings(scenario_id)}
