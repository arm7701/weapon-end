from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl, Signal
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

logger = logging.getLogger(__name__)

from maap_app.ui.map.map_event_bridge import MapEventBridge

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_WING_ICON_PATH = _PROJECT_ROOT / "assets" / "icons" / "airport.png"
if not _WING_ICON_PATH.is_file():
    _WING_ICON_PATH = _ASSETS_DIR / "icons" / "airport.png"
_MAP_HTML = "cesium_map.html"


class MapWidget(QWebEngineView):
    """Qt WebEngine map host using CesiumJS (3D globe) with the same JS bridge API."""
    map_ready = Signal()
    target_selected = Signal(str)
    entity_selected = Signal(str, str)
    link_map_clicked = Signal(float, float)
    coordinate_picked = Signal(float, float)
    flight_route_waypoint_added = Signal(float, float)
    flight_route_waypoint_moved = Signal(str, float, float)
    flight_route_waypoint_selected = Signal(str)
    detection_object_added = Signal(float, float)
    detection_object_selected = Signal(str)
    team_marker_place_requested = Signal(str, str, float, float)
    target_create_at_requested = Signal(float, float)
    detection_viewport_ready = Signal()
    measure_updated = Signal(float)
    measure_radius_updated = Signal(float)
    route_point_picked = Signal(str, float, float)

    def __init__(self) -> None:
        super().__init__()
        self._ready = False
        self._pending_fit = False
        self._pending_target_markers: list[dict[str, Any]] | None = None
        self._pending_asset_layers: dict[str, Any] | None = None
        self._pending_detection_objects: list[dict[str, Any]] | None = None
        self._pending_team_markers: list[dict[str, Any]] | None = None
        self._pending_ground_transport_routes: list[dict[str, Any]] | None = None
        self._pending_basemap: str | None = None
        self._stadia_api_key = ""
        self._pending_link_mode: bool | None = None
        self._pending_route_add_mode: bool | None = None
        self._pending_pick_coord_mode: bool | None = None
        self._pending_flight_route_edit_mode: bool | None = None
        self._pending_detection_edit_mode: bool | None = None
        self._pending_detection_add_mode: bool | None = None
        self._pending_terrain_enabled: bool | None = None
        self._pending_ai_flight_route: dict[str, Any] | None = None
        self._pending_route_pick_mode: str | None = None

        settings = self.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,
            True,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True,
        )

        self.loadFinished.connect(self._on_load_finished)
        self.page().titleChanged.connect(self._on_title_changed)
        self.page().renderProcessTerminated.connect(self._on_render_process_terminated)

        self._bridge = MapEventBridge()
        self._bridge.link_map_clicked.connect(self.link_map_clicked)
        self._bridge.coordinate_picked.connect(self.coordinate_picked)
        self._bridge.flight_route_waypoint_added.connect(
            self.flight_route_waypoint_added
        )
        self._bridge.flight_route_waypoint_moved.connect(
            self.flight_route_waypoint_moved
        )
        self._bridge.flight_route_waypoint_selected.connect(
            self.flight_route_waypoint_selected
        )
        self._bridge.detection_object_added.connect(self.detection_object_added)
        self._bridge.detection_object_selected.connect(self.detection_object_selected)
        self._bridge.team_marker_place_requested.connect(
            self.team_marker_place_requested
        )
        self._bridge.target_create_at_requested.connect(
            self.target_create_at_requested
        )
        self._bridge.target_selected.connect(self.target_selected)
        self._bridge.entity_selected.connect(self.entity_selected)
        self._bridge.detection_ready.connect(self.detection_viewport_ready)
        self._bridge.measure_updated.connect(self.measure_updated)
        self._bridge.measure_radius_updated.connect(self.measure_radius_updated)
        self._bridge.route_point_picked.connect(self.route_point_picked)
        channel = QWebChannel(self)
        channel.registerObject("bridge", self._bridge)
        self.page().setWebChannel(channel)

        html_path = _ASSETS_DIR / _MAP_HTML
        self.load(QUrl.fromLocalFile(str(html_path)))

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            return
        self._ready = True
        wing_icon_url = QUrl.fromLocalFile(str(_WING_ICON_PATH)).toString()
        self._run_js(
            f"window.maapMap.setWingIconUrl({json.dumps(wing_icon_url)});"
        )
        self.set_stadia_api_key(self._stadia_api_key)
        if self._pending_fit:
            self.fit_to_scenario()
            self._pending_fit = False
        if self._pending_target_markers is not None:
            self.set_target_markers(self._pending_target_markers)
            self._pending_target_markers = None
        if self._pending_asset_layers is not None:
            self.set_asset_layers(self._pending_asset_layers)
            self._pending_asset_layers = None
        if self._pending_detection_objects is not None:
            self.set_detection_objects(self._pending_detection_objects)
            self._pending_detection_objects = None
        if self._pending_team_markers is not None:
            self.set_team_markers(self._pending_team_markers)
            self._pending_team_markers = None
        if self._pending_ground_transport_routes is not None:
            self.set_ground_transport_routes(self._pending_ground_transport_routes)
            self._pending_ground_transport_routes = None
        if self._pending_basemap is not None:
            self.set_basemap(self._pending_basemap)
            self._pending_basemap = None
        self._flush_pending_map_modes()
        self.map_ready.emit()

    def _flush_pending_map_modes(self) -> None:
        if self._pending_link_mode is not None:
            enabled = self._pending_link_mode
            self._pending_link_mode = None
            self.enable_link_mode(enabled)
        if self._pending_pick_coord_mode is not None:
            enabled = self._pending_pick_coord_mode
            self._pending_pick_coord_mode = None
            self.set_pick_coord_mode(enabled)
        if self._pending_route_add_mode is not None:
            enabled = self._pending_route_add_mode
            self._pending_route_add_mode = None
            self.set_route_add_mode(enabled)
        if self._pending_flight_route_edit_mode is not None:
            enabled = self._pending_flight_route_edit_mode
            self._pending_flight_route_edit_mode = None
            self.set_flight_route_edit_mode(enabled)
        if self._pending_detection_edit_mode is not None:
            enabled = self._pending_detection_edit_mode
            self._pending_detection_edit_mode = None
            self.set_detection_edit_mode(enabled)
        if self._pending_detection_add_mode is not None:
            enabled = self._pending_detection_add_mode
            self._pending_detection_add_mode = None
            self.set_detection_add_mode(enabled)
        if self._pending_terrain_enabled is not None:
            enabled = self._pending_terrain_enabled
            self._pending_terrain_enabled = None
            self.set_terrain_enabled(enabled)
        if self._pending_ai_flight_route is not None:
            route = self._pending_ai_flight_route
            self._pending_ai_flight_route = None
            self.set_ai_flight_route(route)
        if self._pending_route_pick_mode is not None:
            mode = self._pending_route_pick_mode
            self._pending_route_pick_mode = None
            self.set_route_pick_mode(mode)

    def _on_render_process_terminated(
        self,
        status: QWebEnginePage.RenderProcessTerminationStatus,
        exit_code: int,
    ) -> None:
        logger.error(
            "Map render process terminated (status=%s, exit_code=%s); reloading map",
            status,
            exit_code,
        )
        self._ready = False
        self.reload()

    def _on_title_changed(self, title: str) -> None:
        if not title.startswith("MAAP_SYNC|"):
            return
        parts = title.split("|")
        if len(parts) < 3:
            return
        event = parts[1]
        if event == "select_target":
            self.target_selected.emit(parts[2])
        elif event == "select_entity" and len(parts) >= 4:
            self.entity_selected.emit(parts[2], parts[3])
        elif event == "link_map" and len(parts) >= 4:
            self.link_map_clicked.emit(float(parts[2]), float(parts[3]))
        elif event == "pick_coord" and len(parts) >= 4:
            self.coordinate_picked.emit(float(parts[2]), float(parts[3]))
        elif event == "flight_route_add" and len(parts) >= 4:
            self.flight_route_waypoint_added.emit(float(parts[2]), float(parts[3]))
        elif event == "flight_route_move" and len(parts) >= 5:
            self.flight_route_waypoint_moved.emit(
                parts[2],
                float(parts[3]),
                float(parts[4]),
            )
        elif event == "flight_route_select" and len(parts) >= 3:
            self.flight_route_waypoint_selected.emit(parts[2])
        elif event == "detection_add" and len(parts) >= 4:
            self.detection_object_added.emit(float(parts[2]), float(parts[3]))
        elif event == "detection_select" and len(parts) >= 3:
            self.detection_object_selected.emit(parts[2])
        elif event == "team_marker_place" and len(parts) >= 6:
            self.team_marker_place_requested.emit(
                parts[2],
                parts[3],
                float(parts[4]),
                float(parts[5]),
            )
        elif event == "team_marker_place" and len(parts) >= 5:
            self.team_marker_place_requested.emit(
                parts[2],
                "generic",
                float(parts[3]),
                float(parts[4]),
            )
        elif event == "target_create_at" and len(parts) >= 4:
            self.target_create_at_requested.emit(float(parts[2]), float(parts[3]))
        elif event == "route_point_pick" and len(parts) >= 5:
            self.route_point_picked.emit(parts[2], float(parts[3]), float(parts[4]))
        elif event == "detection_ready":
            self.detection_viewport_ready.emit()
        elif event == "measure_update" and len(parts) >= 3:
            try:
                self.measure_updated.emit(float(parts[2]))
            except ValueError:
                self.measure_updated.emit(0.0)
            if len(parts) >= 4:
                try:
                    self.measure_radius_updated.emit(float(parts[3]))
                except ValueError:
                    self.measure_radius_updated.emit(0.0)

    def _run_js(self, script: str) -> None:
        if not self._ready:
            return
        self.page().runJavaScript(script)

    def fit_to_scenario(self) -> None:
        if not self._ready:
            self._pending_fit = True
            return
        self._run_js("window.maapMap.fitToScenario();")

    def set_target_markers(self, markers: list[dict[str, Any]]) -> None:
        if not self._ready:
            self._pending_target_markers = markers
            return
        payload = json.dumps(markers)
        self._run_js(f"window.maapMap.setTargetMarkers({payload});")

    def set_asset_layers(self, layers: dict[str, Any]) -> None:
        if not self._ready:
            self._pending_asset_layers = layers
            return
        payload = json.dumps(layers)
        self._run_js(f"window.maapMap.setAssetLayers({payload});")

    def set_detection_objects(self, objects: list[dict[str, Any]]) -> None:
        if not self._ready:
            self._pending_detection_objects = objects
            return
        payload = json.dumps(objects)
        self._run_js(f"window.maapMap.setDetectedObjects({payload});")

    def set_team_markers(self, markers: list[dict[str, Any]]) -> None:
        if not self._ready:
            self._pending_team_markers = markers
            return
        payload = json.dumps(markers)
        self._run_js(f"window.maapMap.setTeamMarkers({payload});")

    def set_ground_transport_routes(self, routes: list[dict[str, Any]]) -> None:
        if not self._ready:
            self._pending_ground_transport_routes = routes
            return
        payload = json.dumps(routes)
        self._run_js(f"window.maapMap.setGroundTransportRoutes({payload});")

    def set_layer_visibility(self, layers: dict[str, bool]) -> None:
        payload = json.dumps(layers)
        self._run_js(f"window.maapMap.setLayerVisibility({payload});")

    def set_basemap(self, basemap_id: str) -> None:
        if not self._ready:
            self._pending_basemap = basemap_id
            return
        self._run_js(f"window.maapMap.setBasemap({json.dumps(basemap_id)});")

    def set_stadia_api_key(self, api_key: str) -> None:
        self._stadia_api_key = api_key.strip()
        if not self._ready:
            return
        self._run_js(
            f"window.maapMap.setStadiaApiKey({json.dumps(self._stadia_api_key)});"
        )

    def set_detection_capture_mode(self, enabled: bool) -> None:
        self._run_js(
            f"window.maapMap.setDetectionCaptureMode({json.dumps(enabled)});"
        )

    def restore_map_layers_after_detection(self) -> None:
        self._run_js("window.maapMap.restoreMapLayersAfterDetection();")

    def enable_link_mode(self, enabled: bool = True) -> None:
        if not self._ready:
            self._pending_link_mode = enabled
            return
        self._run_js(f"window.maapMap.setLinkMode({json.dumps(enabled)});")

    def fit_to_target(
        self,
        lat: float,
        lng: float,
        focus_radius_m: float = 0,
    ) -> None:
        self._run_js(
            f"window.maapMap.fitToTarget({lat}, {lng}, {focus_radius_m});"
        )

    def fit_to_detection_area(
        self,
        lat: float,
        lng: float,
        radius_m: float,
    ) -> None:
        self._run_js(
            f"window.maapMap.fitToDetectionArea({lat}, {lng}, {radius_m});"
        )

    def fit_to_target_card(self, target_card_id: str) -> None:
        self._run_js(
            f"window.maapMap.fitToTargetCard({json.dumps(target_card_id)});"
        )

    def highlight_target(self, target_card_id: str) -> None:
        self._run_js(
            f"window.maapMap.highlightTarget({json.dumps(target_card_id)});"
        )

    def highlight_ingress_corridor(
        self,
        target_card_id: str,
        coordinate_id: str | None,
        rank: int,
        flight_route: dict | None = None,
    ) -> None:
        flight_payload = json.dumps(flight_route) if flight_route is not None else "null"
        self._run_js(
            "window.maapMap.highlightIngressCorridor("
            f"{json.dumps(target_card_id)}, "
            f"{json.dumps(coordinate_id)}, "
            f"{int(rank)}, "
            f"{flight_payload});"
        )

    def set_measure_mode(self, enabled: bool) -> None:
        self._run_js(f"window.maapMap.setMeasureMode({json.dumps(enabled)});")

    def set_measure_type(self, tool_type: str) -> None:
        measure_type = "radius" if tool_type == "radius" else "distance"
        self._run_js(
            f"window.maapMap.setMeasureType({json.dumps(measure_type)});"
        )

    def clear_measurements(self) -> None:
        self._run_js("window.maapMap.clearMeasure();")

    def set_pick_coord_mode(self, enabled: bool) -> None:
        if not self._ready:
            self._pending_pick_coord_mode = enabled
            return
        self._run_js(f"window.maapMap.setPickCoordMode({json.dumps(enabled)});")

    def clear_picked_coordinate(self) -> None:
        self._run_js("window.maapMap.clearPickedCoordinate();")

    def set_route_add_mode(self, enabled: bool) -> None:
        if not self._ready:
            self._pending_route_add_mode = enabled
            return
        self._run_js(f"window.maapMap.setRouteAddMode({json.dumps(enabled)});")

    def set_flight_route_edit_mode(self, enabled: bool) -> None:
        if not self._ready:
            self._pending_flight_route_edit_mode = enabled
            return
        self._run_js(f"window.maapMap.setFlightRouteEditMode({json.dumps(enabled)});")

    def set_detection_edit_mode(self, enabled: bool) -> None:
        if not self._ready:
            self._pending_detection_edit_mode = enabled
            return
        self._run_js(f"window.maapMap.setDetectionEditMode({json.dumps(enabled)});")

    def set_detection_add_mode(self, enabled: bool) -> None:
        if not self._ready:
            self._pending_detection_add_mode = enabled
            return
        self._run_js(f"window.maapMap.setDetectionAddMode({json.dumps(enabled)});")

    def highlight_detection_object(self, object_id: str | None) -> None:
        payload = json.dumps(object_id or "")
        self._run_js(f"window.maapMap.highlightDetectionObject({payload});")

    def refresh_corridor_flight_route(
        self,
        target_card_id: str,
        coordinate_id: str | None,
        rank: int,
        flight_route: dict | None,
    ) -> None:
        flight_payload = json.dumps(flight_route) if flight_route is not None else "null"
        self._run_js(f"window.maapMap.updateCorridorFlightRoute({flight_payload});")

    def set_terrain_enabled(self, enabled: bool) -> None:
        if not self._ready:
            self._pending_terrain_enabled = enabled
            return
        self._run_js(f"window.maapMap.setTerrainEnabled({json.dumps(enabled)});")

    def set_ai_flight_route(self, route: dict[str, Any] | None) -> None:
        """Render through the corridor/waypoint layer (same as manual route editing)."""
        if not self._ready:
            self._pending_ai_flight_route = route
            return
        self._run_js("window.maapMap.clearAiFlightRoute();")
        if route is None:
            return
        normalized = dict(route)
        normalized.setdefault("routeColor", "#38bdf8")
        normalized["routeEditEnabled"] = True
        if normalized.get("editableWaypoints"):
            normalized["drawWaypointConnectors"] = True
        if normalized.get("unifiedRoute"):
            normalized["showReturnRoute"] = False
        elif len(normalized.get("returnRoute") or []) >= 2:
            normalized["showReturnRoute"] = True
        target_id = str(normalized.get("targetCardId") or "")
        coordinate_id = normalized.get("coordinateId")
        rank = int(normalized.get("rank") or 1)
        if target_id:
            self.highlight_ingress_corridor(
                target_id,
                str(coordinate_id) if coordinate_id else None,
                rank,
                normalized,
            )

    def clear_ai_flight_route(self) -> None:
        self.set_ai_flight_route(None)

    def set_route_pick_mode(self, mode: str | None) -> None:
        if not self._ready:
            self._pending_route_pick_mode = mode
            return
        payload = json.dumps(mode or "")
        self._run_js(f"window.maapMap.setRoutePickMode({payload});")
