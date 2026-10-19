from __future__ import annotations

import json
from uuid import uuid4

from maap_app.modules.audit.service import AuditService
from maap_app.modules.ground_transport.constants import OSRM_MIN_PATH_POINTS
from maap_app.modules.ground_transport.models import GroundRouteResult
from maap_app.modules.ground_transport.repository import GroundTransportRepository
from maap_app.modules.ground_transport.road_routing import resolve_ground_route
from maap_app.modules.ground_transport.schemas import CreateGroundTransportRequest
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.wing_data.service import WingDataService


def encode_route_geometry(path: tuple[tuple[float, float], ...]) -> str:
    return json.dumps([[lat, lng] for lat, lng in path])


def decode_route_geometry(route_geometry_json: str | None) -> list[list[float]]:
    if not route_geometry_json:
        return []
    try:
        raw = json.loads(route_geometry_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    path: list[list[float]] = []
    for point in raw:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        lat = float(point[0])
        lng = float(point[1])
        path.append([lat, lng])
    return path


def route_mode_label(route_mode: str) -> str:
    if route_mode == "road":
        return "เส้นทางถนน (เหมือน Google Maps)"
    return "เส้นตรง (ไม่มีข้อมูลถนน)"


class GroundTransportService:
    def __init__(
        self,
        repository: GroundTransportRepository,
        wing_data_service: WingDataService,
        scenario_repository: ScenarioRepository,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.wing_data_service = wing_data_service
        self.scenario_repository = scenario_repository
        self.audit_service = audit_service

    def create_transport(self, request: CreateGroundTransportRequest) -> str:
        origin, destination = self._validate_wings(request)
        self._validate_optional_refs(request)

        route = resolve_ground_route(
            origin.map_lat,
            origin.map_lng,
            destination.map_lat,
            destination.map_lng,
        )
        label = request.label.strip()
        if not label:
            label = self._default_label(
                origin.wing_name,
                destination.wing_name,
                request.product_id,
            )

        transport_id = str(uuid4())
        self.repository.insert_transport(
            transport_id=transport_id,
            scenario_id=request.scenario_id,
            origin_wing_id=request.origin_wing_id,
            destination_wing_id=request.destination_wing_id,
            product_id=request.product_id,
            vehicle_id=request.vehicle_id,
            quantity=request.quantity,
            distance_m=route.distance_m,
            duration_min=route.duration_min,
            route_mode=route.route_mode,
            route_geometry_json=encode_route_geometry(route.path),
            label=label,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="ground_transport_created",
            entity_type="ground_transport",
            entity_id=transport_id,
            details={
                "scenario_id": request.scenario_id,
                "origin_wing_id": request.origin_wing_id,
                "destination_wing_id": request.destination_wing_id,
                "distance_m": route.distance_m,
                "duration_min": route.duration_min,
                "route_mode": route.route_mode,
            },
        )
        return transport_id

    def list_transports(self, scenario_id: str):
        return self.repository.list_transports(scenario_id)

    def get_transport(self, transport_id: str):
        return self.repository.get_transport(transport_id)

    def preview_route(
        self,
        *,
        origin_wing_id: str,
        destination_wing_id: str,
    ) -> GroundRouteResult | None:
        if not origin_wing_id or not destination_wing_id:
            return None
        if origin_wing_id == destination_wing_id:
            return None
        origin = self.wing_data_service.get_wing(origin_wing_id)
        destination = self.wing_data_service.get_wing(destination_wing_id)
        if (
            origin is None
            or destination is None
            or origin.map_lat is None
            or origin.map_lng is None
            or destination.map_lat is None
            or destination.map_lng is None
        ):
            return None
        return resolve_ground_route(
            origin.map_lat,
            origin.map_lng,
            destination.map_lat,
            destination.map_lng,
        )

    def list_map_routes(
        self,
        scenario_id: str,
        *,
        selected_id: str | None = None,
        resolve_missing_geometry: bool = False,
    ) -> list[dict[str, object]]:
        wings = {
            wing.id: wing
            for wing in self.wing_data_service.list_wings(scenario_id)
        }
        products = {
            product.id: product
            for product in self.wing_data_service.list_products(scenario_id)
        }
        vehicles = {
            vehicle.id: vehicle
            for vehicle in self.wing_data_service.list_vehicles(scenario_id)
        }
        routes: list[dict[str, object]] = []
        for transport in self.repository.list_transports(scenario_id):
            origin = wings.get(transport.origin_wing_id)
            destination = wings.get(transport.destination_wing_id)
            if (
                origin is None
                or destination is None
                or origin.map_lat is None
                or origin.map_lng is None
                or destination.map_lat is None
                or destination.map_lng is None
            ):
                continue
            product = products.get(transport.product_id or "")
            vehicle = vehicles.get(transport.vehicle_id or "")
            path = decode_route_geometry(transport.route_geometry_json)
            distance_m = transport.distance_m
            duration_min = transport.duration_min
            route_mode = transport.route_mode
            if resolve_missing_geometry and len(path) < OSRM_MIN_PATH_POINTS:
                refreshed = resolve_ground_route(
                    origin.map_lat,
                    origin.map_lng,
                    destination.map_lat,
                    destination.map_lng,
                )
                path = [[lat, lng] for lat, lng in refreshed.path]
                distance_m = refreshed.distance_m
                duration_min = refreshed.duration_min
                route_mode = refreshed.route_mode
                if route_mode == "road" and len(path) >= OSRM_MIN_PATH_POINTS:
                    self.repository.update_route_geometry(
                        transport.id,
                        distance_m,
                        duration_min,
                        route_mode,
                        encode_route_geometry(refreshed.path),
                    )
            if len(path) < 2:
                path = [
                    [origin.map_lat, origin.map_lng],
                    [destination.map_lat, destination.map_lng],
                ]
            routes.append(
                {
                    "id": transport.id,
                    "label": transport.label,
                    "originWingName": origin.wing_name,
                    "destinationWingName": destination.wing_name,
                    "origin": [origin.map_lat, origin.map_lng],
                    "destination": [destination.map_lat, destination.map_lng],
                    "path": path,
                    "distanceM": distance_m,
                    "durationMin": duration_min,
                    "routeMode": route_mode,
                    "routeModeLabel": route_mode_label(route_mode),
                    "productName": product.product_name if product else "",
                    "vehicleName": vehicle.vehicle_name if vehicle else "",
                    "quantity": transport.quantity,
                    "selected": transport.id == selected_id,
                }
            )
        return routes

    def delete_transport(self, transport_id: str) -> None:
        if not self.repository.delete_transport(transport_id):
            raise ValueError("ไม่พบเส้นทางขนส่ง")
        self.audit_service.record_event(
            actor="local_user",
            event_type="ground_transport_deleted",
            entity_type="ground_transport",
            entity_id=transport_id,
            details={},
        )

    def _validate_wings(self, request: CreateGroundTransportRequest):
        if self.scenario_repository.get_scenario(request.scenario_id) is None:
            raise ValueError("ไม่พบ scenario นี้")
        if request.origin_wing_id == request.destination_wing_id:
            raise ValueError("กองบินต้นทางและปลายทางต้องไม่เหมือนกัน")
        if request.quantity < 1:
            raise ValueError("จำนวนสินค้าต้องมากกว่า 0")

        origin = self.wing_data_service.get_wing(request.origin_wing_id)
        destination = self.wing_data_service.get_wing(request.destination_wing_id)
        if origin is None or destination is None:
            raise ValueError("ไม่พบกองบินที่เลือก")
        if origin.scenario_id != request.scenario_id or destination.scenario_id != request.scenario_id:
            raise ValueError("กองบินไม่อยู่ใน scenario นี้")
        if origin.map_lat is None or origin.map_lng is None:
            raise ValueError("กองบินต้นทางยังไม่มีพิกัดบนแผนที่")
        if destination.map_lat is None or destination.map_lng is None:
            raise ValueError("กองบินปลายทางยังไม่มีพิกัดบนแผนที่")
        return origin, destination

    def _validate_optional_refs(self, request: CreateGroundTransportRequest) -> None:
        if request.product_id:
            product = self.wing_data_service.get_product(request.product_id)
            if product is None or product.scenario_id != request.scenario_id:
                raise ValueError("ไม่พบสินค้าที่เลือก")
        if request.vehicle_id:
            vehicle = self.wing_data_service.get_vehicle(request.vehicle_id)
            if vehicle is None or vehicle.scenario_id != request.scenario_id:
                raise ValueError("ไม่พบรถขนส่งที่เลือก")

    def _default_label(
        self,
        origin_name: str,
        destination_name: str,
        product_id: str | None,
    ) -> str:
        if product_id:
            product = self.wing_data_service.get_product(product_id)
            if product is not None:
                return f"{product.product_name}: {origin_name} → {destination_name}"
        return f"{origin_name} → {destination_name}"
