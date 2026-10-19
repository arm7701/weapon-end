from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot


class MapEventBridge(QObject):
    """Qt WebChannel bridge for Cesium map events (replaces title-sync only)."""

    link_map_clicked = Signal(float, float)
    coordinate_picked = Signal(float, float)
    flight_route_waypoint_added = Signal(float, float)
    flight_route_waypoint_moved = Signal(str, float, float)
    flight_route_waypoint_selected = Signal(str)
    detection_object_added = Signal(float, float)
    detection_object_selected = Signal(str)
    team_marker_place_requested = Signal(str, str, float, float)
    target_create_at_requested = Signal(float, float)
    target_selected = Signal(str)
    entity_selected = Signal(str, str)
    detection_ready = Signal()
    measure_updated = Signal(float)
    measure_radius_updated = Signal(float)
    route_point_picked = Signal(str, float, float)

    @Slot(float, float)
    def linkMapClick(self, lat: float, lng: float) -> None:
        self.link_map_clicked.emit(lat, lng)

    @Slot(float, float)
    def pickCoord(self, lat: float, lng: float) -> None:
        self.coordinate_picked.emit(lat, lng)

    @Slot(float, float)
    def flightRouteAdd(self, lat: float, lng: float) -> None:
        self.flight_route_waypoint_added.emit(lat, lng)

    @Slot(str, float, float)
    def flightRouteMove(self, waypoint_id: str, lat: float, lng: float) -> None:
        self.flight_route_waypoint_moved.emit(waypoint_id, lat, lng)

    @Slot(str)
    def flightRouteSelect(self, waypoint_id: str) -> None:
        self.flight_route_waypoint_selected.emit(waypoint_id)

    @Slot(float, float)
    def detectionAdd(self, lat: float, lng: float) -> None:
        self.detection_object_added.emit(lat, lng)

    @Slot(str)
    def detectionSelect(self, object_id: str) -> None:
        self.detection_object_selected.emit(object_id)

    @Slot(str, str, float, float)
    def teamMarkerPlace(
        self, side: str, unit_type: str, lat: float, lng: float
    ) -> None:
        self.team_marker_place_requested.emit(side, unit_type, lat, lng)

    @Slot(float, float)
    def targetCreateAt(self, lat: float, lng: float) -> None:
        self.target_create_at_requested.emit(lat, lng)

    @Slot(str)
    def selectTarget(self, target_id: str) -> None:
        self.target_selected.emit(target_id)

    @Slot(str, str)
    def selectEntity(self, entity_type: str, entity_id: str) -> None:
        self.entity_selected.emit(entity_type, entity_id)

    @Slot()
    def detectionReady(self) -> None:
        self.detection_ready.emit()

    @Slot(float, float)
    def measureUpdate(self, distance_m: float, radius_m: float) -> None:
        self.measure_updated.emit(distance_m)
        self.measure_radius_updated.emit(radius_m)

    @Slot(str, float, float)
    def routePointPick(self, point_type: str, lat: float, lng: float) -> None:
        self.route_point_picked.emit(point_type, lat, lng)
