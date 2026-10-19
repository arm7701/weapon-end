from __future__ import annotations

import json
import logging
import pathlib
import subprocess
import sys
from dataclasses import dataclass, field
from uuid import uuid4

from PySide6.QtCore import QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from maap_app.app import AppContext
from maap_app.modules.detection import DetectionRunResult, YoloDetectionService
from maap_app.modules.flight_route.plan_endpoints import resolve_flight_plan_endpoints
from maap_app.modules.flight_route.ai_planner import (
    extract_editable_fly_through_waypoints,
    plan_ai_flight_route,
    split_ai_route_waypoints,
)
from maap_app.modules.flight_route.border_corridor_planner import build_waypoint_connector_paths
from maap_app.modules.flight_route.params import AiRoutePlannerParams, RouteStyle
from maap_app.modules.detection.corridor_flight_route import (
    attach_route_edit_metadata,
    build_waypoint_sketch_route,
)
from maap_app.modules.detection.service import (
    BUILDING_MODEL_FILENAME,
    detection_capture_radius_m,
)
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.weaponeering.mission_defaults import SIM_FLIGHT_DEFAULTS
from maap_app.modules.weaponeering.flight_path import distance_m
from maap_app.modules.weaponeering.schemas import (
    DeploymentAircraftLineRequest,
    DeploymentWaypointRequest,
    UpsertDeploymentPlanRequest,
)
from maap_app.modules.weaponeering.jmem_calculator import (
    JmemWeaponInputs,
    apply_selected_product_rank,
    estimate_mae_building_ft2,
    mission_inputs_from_target_card,
    rank_weapons,
)
from maap_app.modules.target.constants import subtypes_for_target_type
from maap_app.modules.target.profile_fields import TargetProfileFields
from maap_app.modules.target.schemas import (
    CreateTargetCardRequest,
    SaveTargetCoordinatesRequest,
    TargetCoordinateInput,
)
from maap_app.ui.components.app_chrome import AppChrome
from maap_app.ui.components.map_page import MapPageWidget
from maap_app.ui.components.map_workspace import MapWorkspace
from maap_app.ui.components.workspace_stack import WorkspaceStack, build_split_page
from maap_app.ui.map.map_widget import MapWidget
from maap_app.ui.dialogs.target_dialogs import QuickCreateTargetDialog
from maap_app.ui.panels.wing_data_panel import WingDataPanel
from maap_app.ui.panels.export_panel import ExportPanel
from maap_app.ui.panels.target_panel import TargetPanel
from maap_app.ui.panels.review_queue_panel import ReviewQueuePanel
from maap_app.ui.panels.right_maap_panel import RightMaapPanel
from maap_app.config.map_settings import MapSettings
from maap_app.ui.panels.settings_panel import SettingsPanel
from maap_app.modules.target.coordinate_products import resolve_coordinate_product_id
from maap_app.modules.target.map_markers import enrich_target_markers_with_effect_radii
from maap_app.modules.ground_transport.routing import format_distance_m, format_duration_min
from maap_app.modules.team_marker.constants import (
    DEFAULT_RADAR_RADIUS_M,
    MAX_RADAR_RADIUS_M,
    MIN_RADAR_RADIUS_M,
    UNIT_TYPES,
    VALID_UNIT_TYPES,
)
from maap_app.ui.panels.map_detail_sidebar import MapDetailSidebar
from maap_app.ui.panels.weaponeering_panel import WeaponeeringPanel

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
_BUILDING_DETECTOR_MODEL = "Building Detector"

logger = logging.getLogger(__name__)


@dataclass
class _DetectionEditState:
    target_id: str
    coordinate_id: str
    selected_object_id: str | None = None


@dataclass
class _CorridorRouteEditState:
    target_id: str
    coordinate_id: str | None
    rank: int
    wing_id: str
    wing_name: str
    wing_lat: float
    wing_lng: float
    target_lat: float
    target_lng: float
    target_label: str
    border_route: dict
    fly_through_waypoints: list[dict] = field(default_factory=list)
    plan: object | None = None
    selected_waypoint_id: str | None = None
    dirty: bool = False
    show_waypoints: bool = True
    show_waypoint_labels: bool = False
    use_ingress_corridor: bool = False
    ai_route_params: AiRoutePlannerParams | None = None
    ai_ingress_bearing_deg: float | None = None


class _AiRoutePlanWorker(QThread):
    route_ready = Signal(object)
    failed = Signal(str)

    def __init__(self, plan_callable) -> None:
        super().__init__()
        self._plan_callable = plan_callable

    def run(self) -> None:
        try:
            route = self._plan_callable()
            if route is None:
                self.failed.emit("no_route")
                return
            self.route_ready.emit(route)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self._active_scenario_id: str | None = None
        self._link_target_id: str | None = None
        self._last_map_targets: list[dict] = []
        self._selected_map_target_id: str | None = None
        self._corridor_flight_summary: str | None = None
        self._corridor_route_edit_state: _CorridorRouteEditState | None = None
        self._detection_edit_state: _DetectionEditState | None = None
        self._ai_planned_route: dict | None = None
        self._ai_takeoff: tuple[float, float] | None = None
        self._ai_landing: tuple[float, float] | None = None
        self._syncing_ai_adapter_mode = False
        self._ai_route_plan_worker: _AiRoutePlanWorker | None = None
        self._selected_ground_transport_id: str | None = None
        self._pending_detection_request: tuple[dict, str, int, int] | None = None
        self._map_settings = MapSettings.load(context.settings.data_dir)
        self._detection_ready_timer = QTimer(self)
        self._detection_ready_timer.setSingleShot(True)
        self._detection_ready_timer.timeout.connect(self._on_detection_viewport_ready)
        self._map_layers_refresh_timer = QTimer(self)
        self._map_layers_refresh_timer.setSingleShot(True)
        self._map_layers_refresh_timer.setInterval(120)
        self._map_layers_refresh_timer.timeout.connect(self._refresh_map_layers)
        self.detection_service = YoloDetectionService(
            context.settings.data_dir,
            project_root=_PROJECT_ROOT,
        )

        self.setWindowTitle("MAAP Wargame - Local Simulation Workspace")
        self.setMinimumSize(1024, 680)
        screen = QApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            self.resize(int(rect.width() * 0.88), int(rect.height() * 0.88))
        else:
            self.resize(1440, 900)
        self.map_widget = MapWidget()
        self.weaponeering_panel = WeaponeeringPanel(
            context.weaponeering_service,
            context.target_service,
            context.ranking_service,
            context.wing_data_service,
            context.ai_service,
        )
        self.target_panel = TargetPanel(
            context.target_service,
            context.ai_service,
            self.weaponeering_panel,
        )
        self.wing_data_panel = WingDataPanel(
            context.wing_data_service,
            context.ground_transport_service,
            context.team_marker_service,
        )
        self.review_panel = ReviewQueuePanel(context.review_service, context.ai_service)
        self.review_panel.set_ai_mode(context.ai_service.adapter_mode)
        self.settings_panel = SettingsPanel(
            context.ai_service,
            context.settings,
            self._map_settings,
        )
        self.export_panel = ExportPanel(
            context.export_service,
            context.ranking_service.repository,
        )
        self.right_panel = RightMaapPanel(
            context.ranking_service,
            context.ai_service,
            context.review_service,
            context.export_service,
        )
        self.map_detail_sidebar = MapDetailSidebar(
            self.context.target_service,
            self.context.target_detection_service,
            self.context.ground_transport_service,
            self.context.wing_data_service,
        )
        self.map_workspace = MapWorkspace(self.map_widget)
        self.map_page = MapPageWidget(self.map_detail_sidebar, self.map_workspace)
        self.chrome: AppChrome | None = None

        self.menuBar().setVisible(False)
        self._ensure_default_scenario()
        self._build_shell()
        self._wire_signals()
        self.map_widget.map_ready.connect(self._on_map_ready)
        self._activate_default_scenario()
        self._on_workspace_tab_changed("map")

    def _ensure_default_scenario(self) -> None:
        scenarios = self.context.scenario_service.list_scenarios()
        if scenarios:
            return
        self.context.scenario_service.create_scenario(
            CreateScenarioRequest(
                name="Phase 6 - Baseline",
                description="Default training scenario.",
            )
        )

    def _build_shell(self) -> None:
        root = QWidget()
        root.setObjectName("AppRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(4, 4, 4, 2)
        layout.setSpacing(4)

        self.chrome = AppChrome()
        layout.addWidget(self.chrome)

        map_page = self.map_page
        target_page = build_split_page(
            None,
            self.target_panel,
            self.right_panel,
        )
        database_page = build_split_page(None, self.wing_data_panel, None)
        intelligence_page = build_split_page(
            None,
            self.review_panel,
            self.right_panel,
        )
        reports_page = build_split_page(None, self.export_panel, None)
        settings_page = build_split_page(None, self.settings_panel, None)

        self.workspace_stack = WorkspaceStack(
            map_page,
            target_page,
            database_page,
            intelligence_page,
            reports_page,
            settings_page,
        )
        layout.addWidget(self.workspace_stack, stretch=1)

        self.setCentralWidget(root)
        self._build_status_bar()

    def _wire_signals(self) -> None:
        assert self.chrome is not None
        self.chrome.workspace_tab_changed.connect(self._on_workspace_tab_changed)
        self.chrome.llm_mode_changed.connect(self._on_chrome_llm_mode_changed)
        self.chrome.set_llm_mode(self.context.ai_service.adapter_mode)

        self.target_panel.target_selected.connect(self._on_target_selected)
        self.target_panel.target_selected.connect(self.weaponeering_panel.select_target)
        self.target_panel.targets_changed.connect(self._on_targets_changed)
        self.target_panel.map_search_requested.connect(self._on_map_search_requested)
        self.weaponeering_panel.set_target_inputs_provider(
            self.target_panel.get_calculation_snapshot
        )

        self.wing_data_panel.data_changed.connect(self._schedule_map_layers_refresh)
        self.wing_data_panel.data_changed.connect(self._on_wing_data_changed)
        self.wing_data_panel.team_markers_changed.connect(self._refresh_team_markers_only)
        self.wing_data_panel.transport_changed.connect(self._on_ground_transports_changed)
        self.weaponeering_panel.weaponeering_changed.connect(self._schedule_map_layers_refresh)
        self.weaponeering_panel.ranking_completed.connect(self._on_ranking_completed)
        self.review_panel.review_changed.connect(self._on_review_changed)
        self.review_panel.ai_mode_changed.connect(self._on_ai_mode_changed)
        self.settings_panel.ai_settings_changed.connect(self._on_ai_settings_changed)
        self.settings_panel.map_settings_changed.connect(self._on_map_settings_changed)
        self.right_panel.ai_output_changed.connect(self._on_review_changed)
        self.export_panel.readiness_changed.connect(self._on_export_readiness)
        self.export_panel.export_changed.connect(self._on_export_changed)
        self.weaponeering_panel.ranking_completed.connect(self.export_panel.refresh)
        self.map_workspace.detection_run_requested.connect(self._on_detection_run_requested)
        self.map_workspace.open_in_target_stack.connect(self._on_open_target_from_map)
        self.map_workspace.ingress_corridor_view_requested.connect(
            self._on_ingress_corridor_view_requested
        )
        self.map_workspace.flight_route_approve_requested.connect(
            self._on_flight_route_approve_requested
        )
        self.map_workspace.flight_route_delete_waypoint_requested.connect(
            self._on_flight_route_delete_waypoint_requested
        )
        self.map_workspace.flight_route_waypoint_label_changed.connect(
            self._on_flight_route_waypoint_label_changed
        )
        self.map_workspace.flight_route_waypoints_visibility_changed.connect(
            self._on_flight_route_waypoints_visibility_changed
        )
        self.map_workspace.flight_route_waypoint_labels_visibility_changed.connect(
            self._on_flight_route_waypoint_labels_visibility_changed
        )
        self.map_widget.flight_route_waypoint_added.connect(
            self._on_flight_route_waypoint_added
        )
        self.map_widget.flight_route_waypoint_moved.connect(
            self._on_flight_route_waypoint_moved
        )
        self.map_widget.flight_route_waypoint_selected.connect(
            self._on_flight_route_waypoint_selected
        )
        self.map_workspace.detection_editor_requested.connect(
            self._on_detection_editor_requested
        )
        self.map_workspace.detection_delete_requested.connect(
            self._on_detection_delete_requested
        )
        self.map_workspace.detection_object_selected.connect(
            self._on_detection_object_selected
        )
        self.map_workspace.detection_delete_object_requested.connect(
            self._on_detection_delete_object_requested
        )
        self.map_workspace.detection_risk_level_changed.connect(
            self._on_detection_risk_changed
        )
        self.map_workspace.detection_editor_closed.connect(
            self._clear_detection_edit_state
        )
        self.map_workspace.coordinate_product_changed.connect(
            self._on_coordinate_product_changed
        )
        self.map_workspace.flight_route_waypoint_altitude_changed.connect(
            self._on_flight_route_waypoint_altitude_changed
        )
        self.map_workspace.ai_route_plan_requested.connect(self._on_ai_route_plan_requested)
        self.map_workspace.ai_route_apply_requested.connect(self._on_ai_route_apply_requested)
        self.map_workspace.ai_route_clear_requested.connect(self._on_ai_route_clear_requested)
        self.map_workspace.ai_route_use_plan_endpoints_requested.connect(
            self._on_ai_route_use_plan_endpoints_requested
        )
        self.map_workspace.ai_route_takeoff_pick_toggled.connect(
            self._on_ai_route_takeoff_pick_toggled
        )
        self.map_workspace.ai_route_landing_pick_toggled.connect(
            self._on_ai_route_landing_pick_toggled
        )
        self.map_widget.route_point_picked.connect(self._on_route_point_picked)
        self.map_widget.detection_object_added.connect(self._on_detection_object_added)
        self.map_widget.detection_object_selected.connect(
            self._on_detection_object_selected
        )
        self.map_widget.team_marker_place_requested.connect(
            self._on_team_marker_place_requested
        )
        self.map_widget.target_create_at_requested.connect(
            self._on_target_create_at_requested
        )
        self.map_widget.detection_viewport_ready.connect(
            self._on_detection_viewport_ready
        )

        self.map_widget.target_selected.connect(self._on_map_target_selected)
        self.map_detail_sidebar.open_in_target_stack.connect(
            self._on_open_target_from_map
        )
        self.map_detail_sidebar.view_all_targets.connect(
            self._on_view_all_targets_from_map
        )
        self.map_detail_sidebar.target_entry_selected.connect(
            self._on_sidebar_target_entry_selected
        )
        self.map_detail_sidebar.open_wing_in_database.connect(
            self._on_open_wing_from_map
        )
        self.map_detail_sidebar.transport_selected.connect(
            self._on_ground_transport_selected
        )
        self.map_widget.entity_selected.connect(self._on_map_entity_selected)
        self.map_widget.link_map_clicked.connect(self._on_map_link_click)
        self.map_widget.measure_updated.connect(self._on_map_measure_updated)
        self.map_widget.measure_radius_updated.connect(self._on_map_measure_radius_updated)

    def _build_status_bar(self) -> None:
        status_bar = QStatusBar()
        status_bar.showMessage("Hybrid map ready | คลิกแผนที่เพื่อปักเป้าหมาย")

        def pill(text: str, color: str = "#6b7f96") -> QLabel:
            label = QLabel(text)
            label.setStyleSheet(f"color: {color}; font-size: 11px; padding: 0 6px;")
            return label

        self._status_local = pill("● Local Mode", "#4ade80")

        status_bar.addPermanentWidget(self._status_local)
        status_bar.addPermanentWidget(pill("☁ Offline"))
        self.setStatusBar(status_bar)

    def _on_workspace_tab_changed(self, tab_id: str) -> None:
        self.workspace_stack.show_tab(tab_id)

    def _show_workspace_tab(self, tab_id: str) -> None:
        if self.chrome is not None:
            self.chrome.activate_tab(tab_id)
        else:
            self.workspace_stack.show_tab(tab_id)

    def _on_map_target_selected(self, target_id: str) -> None:
        self._selected_map_target_id = target_id
        detail = self.context.target_service.get_target_detail(target_id)
        if detail is None:
            return
        coordinates = self.target_panel.get_detection_coordinates(target_id)
        self.map_workspace.set_detection_coordinates(coordinates)
        marker = self._primary_marker_for_target(target_id)
        self.map_workspace.clear_ingress_corridor_focus()
        self._clear_corridor_route_edit_state()
        self._corridor_flight_summary = None
        self.map_widget.highlight_ingress_corridor(target_id, None, 0, None)
        self.map_widget.highlight_target(target_id)
        self.map_detail_sidebar.show_target(detail, marker)
        self._refresh_target_output_panel(target_id)
        self.statusBar().showMessage(f"Target: {detail.card.label}")
        if self.map_workspace.ai_route_planner.isVisible():
            self._sync_ai_route_from_flight_plan(target_id)

    def _flight_plan_endpoints_for_target(
        self,
        target_id: str,
    ) -> dict[str, object] | None:
        marker = self._primary_marker_for_target(target_id)
        if marker is None:
            return None
        target_lat = float(marker.get("lat") or 0.0)
        target_lng = float(marker.get("lng") or 0.0)
        wing = self._corridor_flight_wing(target_id, target_lat, target_lng)
        if wing is None:
            return None
        plan = self.context.weaponeering_service.get_deployment_plan_for_target(target_id)
        return resolve_flight_plan_endpoints(
            plan=plan,
            wing_lat=float(wing["lat"]),
            wing_lng=float(wing["lng"]),
            wing_name=str(wing["name"]),
        )

    def _sync_ai_route_from_flight_plan(self, target_id: str | None = None) -> None:
        target_id = target_id or self._selected_map_target_id
        planner = self.map_workspace.ai_route_planner
        if not target_id:
            planner.set_takeoff_label("—")
            planner.set_landing_label("—")
            planner.set_status("เลือก Target บนแผนที่")
            return
        endpoints = self._flight_plan_endpoints_for_target(target_id)
        if endpoints is None:
            planner.set_status("ยังไม่มีแผนการบิน · ใช้กองบินใกล้เป้าหมาย")
            return
        self._ai_takeoff = None
        self._ai_landing = None
        planner.set_takeoff_label(str(endpoints["takeoff_label"]))
        planner.set_landing_label(str(endpoints["landing_label"]))
        if endpoints.get("has_plan"):
            planner.set_status(
                f"ใช้พิกัดกองบินจากแผน · บินเข้า-ออกเป้าหมายแล้ว RTB กลับกองบิน"
            )
        else:
            planner.set_status("ใช้กองบินใกล้เป้าหมาย · บันทึกแผนใน Weaponeering เพื่อผูกกองบิน")

    def _resolve_ai_route_endpoints(
        self,
        target_id: str,
    ) -> tuple[tuple[float, float], tuple[float, float]] | None:
        marker = self._primary_marker_for_target(target_id)
        if marker is None:
            return None
        target_lat = float(marker.get("lat") or 0.0)
        target_lng = float(marker.get("lng") or 0.0)
        wing = self._corridor_flight_wing(target_id, target_lat, target_lng)
        if wing is None:
            return None
        wing_point = (float(wing["lat"]), float(wing["lng"]))
        return wing_point, wing_point

    def _upsert_plan_endpoints(
        self,
        target_id: str,
        *,
        takeoff_lat: float,
        takeoff_lng: float,
        landing_lat: float,
        landing_lng: float,
        landing_altitude_ft: int | None = None,
    ) -> None:
        if not self._active_scenario_id:
            return
        plan = self.context.weaponeering_service.get_deployment_plan_for_target(target_id)
        if plan is None:
            return
        fly_through = [
            DeploymentWaypointRequest(
                lat=waypoint.lat,
                lng=waypoint.lng,
                label=waypoint.label or "",
                waypoint_type="fly_through",
                altitude_ft=waypoint.altitude_ft,
            )
            for waypoint in plan.waypoints
            if waypoint.waypoint_type == "fly_through"
        ]
        return_waypoints = [
            DeploymentWaypointRequest(
                lat=waypoint.lat,
                lng=waypoint.lng,
                label=waypoint.label or "",
                waypoint_type="return",
                altitude_ft=waypoint.altitude_ft,
            )
            for waypoint in plan.waypoints
            if waypoint.waypoint_type == "return"
        ]
        landing_point = DeploymentWaypointRequest(
            lat=landing_lat,
            lng=landing_lng,
            label="Landing",
            waypoint_type="return",
            altitude_ft=landing_altitude_ft,
        )
        if return_waypoints:
            return_waypoints[-1] = landing_point
        else:
            return_waypoints = [landing_point]
        request = UpsertDeploymentPlanRequest(
            scenario_id=self._active_scenario_id,
            target_card_id=target_id,
            wing_id=plan.wing_id,
            flying_unit_id=plan.flying_unit_id,
            aircraft_lines=tuple(
                DeploymentAircraftLineRequest(
                    aircraft_id=line.aircraft_id,
                    aircraft_count=line.aircraft_count,
                )
                for line in plan.aircraft_lines
            ),
            takeoff_lat=takeoff_lat,
            takeoff_lng=takeoff_lng,
            ingress_bearing_deg=plan.ingress_bearing_deg,
            ingress_offset_m=plan.ingress_offset_m,
            cruise_altitude_ft=plan.cruise_altitude_ft,
            ingress_altitude_ft=plan.ingress_altitude_ft,
            target_altitude_ft=plan.target_altitude_ft,
            climb_rate_ft_min=plan.climb_rate_ft_min,
            descent_rate_ft_min=plan.descent_rate_ft_min,
            return_enabled=plan.return_enabled,
            cruise_speed_kt=plan.cruise_speed_kt,
            climb_speed_kt=plan.climb_speed_kt,
            descent_speed_kt=plan.descent_speed_kt,
            ingress_speed_kt=plan.ingress_speed_kt,
            bank_angle_deg=plan.bank_angle_deg,
            turn_mode=plan.turn_mode,
            auto_toc_tod=plan.auto_toc_tod,
            waypoints=tuple(fly_through + return_waypoints),
        )
        self.context.weaponeering_service.upsert_deployment_plan(request)
        self.weaponeering_panel.reload_deployment_plan_for_target(target_id)

    def _on_open_target_from_map(self, target_id: str) -> None:
        self._show_workspace_tab("target")
        self.target_panel.select_target(target_id)
        self.weaponeering_panel.select_target(target_id)
        self._on_target_selected(target_id)

    def _on_view_all_targets_from_map(self) -> None:
        self._show_workspace_tab("target")

    def _on_sidebar_target_entry_selected(
        self,
        target_id: str,
        coordinate_id: str,
    ) -> None:
        self._selected_map_target_id = target_id
        detail = self.context.target_service.get_target_detail(target_id)
        if detail is None:
            return
        markers = self._markers_for_target(target_id)
        marker = next(
            (
                item
                for item in markers
                if str(item.get("coordinateId") or "") == coordinate_id
            ),
            markers[0] if markers else None,
        )
        self.map_workspace.clear_ingress_corridor_focus()
        self._clear_corridor_route_edit_state()
        self._corridor_flight_summary = None
        self.map_widget.highlight_ingress_corridor(target_id, None, 0, None)
        self.map_widget.highlight_target(target_id)
        if marker is not None:
            self.map_widget.fit_to_target(float(marker["lat"]), float(marker["lng"]))
        self.map_detail_sidebar.show_target(detail, marker)
        self._refresh_target_output_panel(target_id)
        coordinates = self.target_panel.get_detection_coordinates(target_id)
        self.map_workspace.set_detection_coordinates(coordinates)
        if coordinate_id:
            combo = self.map_workspace.detection_coordinate
            index = combo.findData(coordinate_id)
            if index >= 0:
                combo.setCurrentIndex(index)
        self.statusBar().showMessage(f"Target: {detail.card.label}")

    def _on_map_entity_selected(self, entity_type: str, entity_id: str) -> None:
        if entity_type == "air_wing" and self._active_scenario_id:
            wing_detail = self.context.wing_data_service.get_wing_map_detail(
                entity_id,
                self._active_scenario_id,
            )
            if wing_detail is not None:
                self.map_detail_sidebar.show_wing(wing_detail)
                if (
                    wing_detail.wing.map_lat is not None
                    and wing_detail.wing.map_lng is not None
                ):
                    self.map_widget.fit_to_target(
                        wing_detail.wing.map_lat,
                        wing_detail.wing.map_lng,
                    )
                self.statusBar().showMessage(f"กองบิน: {wing_detail.wing.wing_name}")
            return
        if entity_type == "ground_transport" and self._active_scenario_id:
            self.map_detail_sidebar.set_sidebar_view("transport")
            self._on_ground_transport_selected(entity_id)
            return
        self._show_workspace_tab("database")
        self.wing_data_panel.show_entity_detail(entity_type, entity_id)

    def _on_open_wing_from_map(self, wing_id: str) -> None:
        self._show_workspace_tab("database")
        self.wing_data_panel.show_entity_detail("air_wing", wing_id)

    def _activate_default_scenario(self) -> None:
        scenarios = self.context.scenario_service.list_scenarios()
        if scenarios:
            self._on_scenario_changed(scenarios[0].id)

    def _on_scenario_changed(self, scenario_id: str) -> None:
        self._active_scenario_id = scenario_id
        scenarios = self.context.scenario_service.list_scenarios()
        name = next((s.name for s in scenarios if s.id == scenario_id), scenario_id)
        self.target_panel.set_scenario(scenario_id, name)
        self.wing_data_panel.set_scenario(scenario_id)
        self.weaponeering_panel.set_scenario(scenario_id)
        self.review_panel.set_scenario(scenario_id)
        self.export_panel.set_scenario(scenario_id)
        self.right_panel.set_scenario(scenario_id, name)
        self._check_export_readiness()
        self._update_review_summary()
        self.map_detail_sidebar.set_scenario(scenario_id)
        self.map_detail_sidebar.clear()
        self._selected_ground_transport_id = None
        self.map_workspace.hide_target_detail()
        self.right_panel.clear_target_output()
        self._refresh_map_layers()
        self._load_latest_logistics_score()
        self.statusBar().showMessage(f"Hybrid map ready | Scenario: {name}")

    def _update_review_summary(self) -> None:
        if not self._active_scenario_id:
            return
        pending = len(self.context.review_service.list_queue(self._active_scenario_id))
        self.right_panel.set_review_summary(pending)

    def _refresh_target_output_panel(self, target_id: str | None = None) -> None:
        target_id = target_id or self._selected_map_target_id
        if not target_id or not self._active_scenario_id:
            self.right_panel.clear_target_output()
            self.map_workspace.hide_target_detail()
            return
        detail = self.context.target_service.get_target_detail(target_id)
        if detail is None:
            self.right_panel.clear_target_output()
            self.map_workspace.hide_target_detail()
            return

        payload = {
            "target": {
                "label": detail.card.label,
                "targetType": detail.card.target_type,
                "priorityScore": detail.card.priority_score,
                "complexityScore": detail.card.complexity_score,
            },
            "location": self._target_location_text(detail.map_lat, detail.map_lng),
            "recognition": self._target_recognition_text(detail),
            "warnings": detail.warnings,
            "risk": self._target_risk_payload(target_id),
            "products": self._target_product_ranking_payload(detail),
            "productHint": "จัดอันดับจาก Product ใน Database ด้วยสูตรจำลองเดียวกับ Weaponeering",
            "plan": self._target_plan_payload(target_id),
            "nearestWing": self._nearest_wing_payload(detail.map_lat, detail.map_lng),
        }
        self.right_panel.show_target_output(payload)
        self._refresh_map_target_detail(target_id)

    def _refresh_map_target_detail(self, target_id: str | None = None) -> None:
        target_id = target_id or self._selected_map_target_id
        if not target_id:
            self.map_workspace.hide_target_detail()
            return
        detail = self.context.target_service.get_target_detail(target_id)
        if detail is None:
            self.map_workspace.hide_target_detail()
            return
        markers = self._markers_for_target(target_id)
        weaponeering = self._target_weaponeering_detail_payload(target_id, detail)
        self.map_workspace.show_target_detail(
            detail,
            markers,
            corridor_flight_summary=self._corridor_flight_summary,
            weaponeering=weaponeering,
        )

    def _on_ingress_corridor_view_requested(
        self,
        target_id: str,
        coordinate_id: object,
        rank: int,
    ) -> None:
        coord_key = str(coordinate_id) if coordinate_id else None
        rank_value = int(rank)
        if rank_value <= 0:
            self._clear_corridor_route_edit_state()
            self._corridor_flight_summary = None
            flight_route = None
        else:
            self._corridor_route_edit_state = None
            flight_route, summary = self._build_corridor_flight_route(
                target_id,
                coord_key,
                rank_value,
            )
            self._corridor_flight_summary = summary
            if flight_route is not None:
                flight_route = dict(flight_route)
                flight_route["fitToRoute"] = True
                self._start_corridor_route_edit(
                    target_id=target_id,
                    coordinate_id=coord_key,
                    rank=rank_value,
                    flight_route=flight_route,
                )
        self.map_widget.highlight_ingress_corridor(
            target_id,
            coord_key,
            rank_value,
            flight_route,
        )
        self._refresh_map_target_detail(target_id)

    def _build_corridor_flight_route(
        self,
        target_id: str,
        coordinate_id: str | None,
        rank: int,
        *,
        edit_waypoints: list[dict] | None = None,
        selected_waypoint_id: str | None = None,
        show_waypoints: bool | None = None,
    ) -> tuple[dict | None, str | None]:
        marker = (
            self._marker_for_coordinate(target_id, coordinate_id)
            if coordinate_id
            else None
        ) or self._primary_marker_for_target(target_id)
        if marker is None:
            return None, "ไม่พบพิกัดเป้าหมายสำหรับสร้างเส้นทางบิน"

        risk_direction = marker.get("lowestRiskDirection") or {}
        options = risk_direction.get("recommendedOptions") or []
        option = next(
            (item for item in options if int(item.get("rank") or 0) == rank),
            options[rank - 1] if 0 < rank <= len(options) else None,
        )
        border_route = (option or {}).get("borderRoute") or {}
        if not border_route.get("available"):
            return None, "ยังไม่มีเส้นทางเข้า-ออกชายแดนสำหรับตัวเลือกนี้"

        target_lat = float(marker.get("lat") or 0.0)
        target_lng = float(marker.get("lng") or 0.0)
        wing = self._corridor_flight_wing(target_id, target_lat, target_lng)
        if wing is None:
            return None, "ไม่พบกองบินใกล้เป้าหมาย — เพิ่มกองบินใน Database หรือบันทึกแผน Weaponeering"

        detail = self.context.target_service.get_target_detail(target_id)
        target_label = detail.card.label if detail is not None else str(marker.get("label") or "Target")
        plan = self.context.weaponeering_service.get_deployment_plan_for_target(target_id)
        waypoint_override = edit_waypoints
        if waypoint_override is None and plan is not None:
            waypoint_override = [
                {
                    "id": waypoint.id,
                    "lat": waypoint.lat,
                    "lng": waypoint.lng,
                    "label": waypoint.label or f"WP{index + 1}",
                }
                for index, waypoint in enumerate(plan.waypoints)
                if waypoint.waypoint_type == "fly_through"
            ]
        waypoint_override = waypoint_override or []
        payload = build_waypoint_sketch_route(
            wing_lat=float(wing["lat"]),
            wing_lng=float(wing["lng"]),
            wing_name=str(wing["name"]),
            wing_id=str(wing["id"]),
            target_lat=target_lat,
            target_lng=target_lng,
            target_label=target_label,
            target_card_id=target_id,
            coordinate_id=coordinate_id or str(marker.get("coordinateId") or ""),
            rank=rank,
            fly_through_waypoints=waypoint_override,
        )
        if show_waypoints is None:
            edit_state = self._corridor_route_edit_state
            show_waypoints = edit_state.show_waypoints if edit_state else True
        attach_route_edit_metadata(
            payload,
            editable_waypoints=waypoint_override,
            selected_waypoint_id=selected_waypoint_id,
            show_waypoints=show_waypoints,
        )
        return payload, str(payload.get("summary") or "")

    def _corridor_flight_wing(
        self,
        target_id: str,
        target_lat: float,
        target_lng: float,
    ) -> dict[str, object] | None:
        plan = self.context.weaponeering_service.get_deployment_plan_for_target(target_id)
        if plan is not None:
            wing = self.context.wing_data_service.get_wing(plan.wing_id)
            if wing is not None and wing.map_lat is not None and wing.map_lng is not None:
                return {
                    "id": wing.id,
                    "name": wing.wing_name,
                    "lat": float(wing.map_lat),
                    "lng": float(wing.map_lng),
                }

        if not self._active_scenario_id:
            return None
        nearest = self.context.wing_data_service.find_nearest_wing(
            self._active_scenario_id,
            target_lat,
            target_lng,
        )
        if nearest is None or nearest.map_lat is None or nearest.map_lng is None:
            return None
        return {
            "id": nearest.wing_id,
            "name": nearest.wing_name,
            "lat": float(nearest.map_lat),
            "lng": float(nearest.map_lng),
        }

    def _clear_corridor_route_edit_state(self) -> None:
        self._corridor_route_edit_state = None
        self.map_workspace.hide_flight_route_editor()
        self.map_widget.set_flight_route_edit_mode(False)

    def _clear_detection_edit_state(self) -> None:
        self._detection_edit_state = None
        self.map_widget.set_detection_edit_mode(False)
        self.map_widget.set_detection_add_mode(False)
        self.map_widget.highlight_detection_object(None)

    def _active_detection_coordinate_id(self, target_id: str) -> str | None:
        combo = self.map_workspace.detection_coordinate
        coordinate_id = str(combo.currentData() or "")
        if coordinate_id:
            return coordinate_id
        detail = self.context.target_service.get_target_detail(target_id)
        if detail is None:
            return None
        if detail.coordinates:
            primary = next(
                (coord for coord in detail.coordinates if coord.is_primary),
                detail.coordinates[0],
            )
            return primary.id
        if detail.map_lat is not None and detail.map_lng is not None:
            return f"legacy-{target_id}"
        return None

    def _detection_coordinate_label(self, target_id: str, coordinate_id: str) -> str:
        combo = self.map_workspace.detection_coordinate
        index = combo.findData(coordinate_id)
        if index >= 0:
            return combo.itemText(index)
        return coordinate_id

    def _on_detection_editor_requested(self) -> None:
        target_id = self._selected_map_target_id
        if not target_id or not self._active_scenario_id:
            QMessageBox.information(
                self,
                "จัดการอาคาน",
                "เลือก Target บนแผนที่ก่อน",
            )
            return
        coordinate_id = self._active_detection_coordinate_id(target_id)
        if not coordinate_id:
            QMessageBox.information(
                self,
                "จัดการอาคาน",
                "เป้าหมายนี้ยังไม่มีพิกัด · เพิ่มพิกัดใน Target Form ก่อน",
            )
            return
        detail = self.context.target_service.get_target_detail(target_id)
        if detail is None:
            return
        self._detection_edit_state = _DetectionEditState(
            target_id=target_id,
            coordinate_id=coordinate_id,
        )
        detections_layer = self.map_workspace._layer_actions.get("detections")
        if detections_layer is not None:
            detections_layer.setChecked(True)
            self.map_workspace._emit_layer_visibility()
        self.map_workspace.show_detection_editor(
            target_label=detail.card.label,
            coordinate_label=self._detection_coordinate_label(target_id, coordinate_id),
        )
        self._sync_detection_editor_ui()
        self.statusBar().showMessage(
            "โหมดจัดการอาคาน · คลิกเพิ่ม/ลบแล้วระบบคำนวณทิศทางเข้า-ออกใหม่"
        )

    def _selected_detection_object(self) -> dict | None:
        state = self._detection_edit_state
        if state is None or not state.selected_object_id:
            return None
        objects = self.context.target_detection_service.list_objects_for_coordinate(
            state.target_id,
            state.coordinate_id,
        )
        return next(
            (item for item in objects if item.get("id") == state.selected_object_id),
            None,
        )

    def _sync_detection_editor_ui(self) -> None:
        state = self._detection_edit_state
        if state is None:
            return
        objects = self.context.target_detection_service.list_objects_for_coordinate(
            state.target_id,
            state.coordinate_id,
        )
        selected = self._selected_detection_object()
        self.map_workspace.update_detection_editor(
            object_count=len(objects),
            objects=objects,
            selected_object_id=state.selected_object_id,
            selected_label=str(selected.get("label") or "") if selected else None,
            selected_risk=str(selected.get("risk") or "") if selected else None,
        )
        self.map_widget.highlight_detection_object(state.selected_object_id)

    def _refresh_detection_layers_and_ingress(self) -> None:
        self.map_workspace.clear_ingress_corridor_focus()
        self._corridor_flight_summary = None
        target_id = self._selected_map_target_id
        if target_id:
            self.map_widget.highlight_ingress_corridor(target_id, None, 0, None)
        self._refresh_map_layers()
        if target_id:
            self._refresh_target_output_panel(target_id)
        self._sync_detection_editor_ui()

    def _on_detection_object_added(self, lat: float, lng: float) -> None:
        state = self._detection_edit_state
        if state is None or not self._active_scenario_id:
            return
        selected = self._selected_detection_object()
        risk_level = str(selected.get("risk") or "medium") if selected else "medium"
        try:
            object_id = self.context.target_detection_service.add_manual_detection_object(
                scenario_id=self._active_scenario_id,
                target_card_id=state.target_id,
                target_coordinate_id=state.coordinate_id,
                lat=lat,
                lng=lng,
                risk_level=risk_level,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "เพิ่มอาคารไม่สำเร็จ", str(exc))
            return
        state.selected_object_id = object_id
        self.map_workspace.set_detection_add_mode(False)
        self._refresh_detection_layers_and_ingress()
        self.statusBar().showMessage(
            f"เพิ่มอาคารที่ {lat:.5f}, {lng:.5f} · คำนวณทิศทางเข้า-ออกใหม่แล้ว"
        )

    def _on_detection_object_selected(self, object_id: str) -> None:
        if self._detection_edit_state is None or not object_id:
            return
        self._detection_edit_state.selected_object_id = object_id
        self._sync_detection_editor_ui()

    def _on_detection_delete_requested(self) -> None:
        state = self._detection_edit_state
        if state is None or not state.selected_object_id:
            return
        self._delete_detection_object(state.selected_object_id)

    def _on_detection_delete_object_requested(self, object_id: str) -> None:
        if not object_id:
            return
        self._delete_detection_object(object_id)

    def _delete_detection_object(self, object_id: str) -> None:
        state = self._detection_edit_state
        if state is None or not self._active_scenario_id:
            return
        objects = self.context.target_detection_service.list_objects_for_coordinate(
            state.target_id,
            state.coordinate_id,
        )
        selected = next(
            (item for item in objects if item.get("id") == object_id),
            None,
        )
        label = str((selected or {}).get("label") or "อาคาร")
        answer = QMessageBox.question(
            self,
            "ลบอาคาร",
            f"ลบ {label} และคำนวณทิศทางเข้า-ออกใหม่?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            remaining = self.context.target_detection_service.delete_detection_object(
                scenario_id=self._active_scenario_id,
                target_card_id=state.target_id,
                target_coordinate_id=state.coordinate_id,
                map_object_id=object_id,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "ลบอาคารไม่สำเร็จ", str(exc))
            return
        if state.selected_object_id == object_id:
            state.selected_object_id = None
        self._refresh_detection_layers_and_ingress()
        self.statusBar().showMessage(f"ลบอาคารแล้ว · เหลือ {remaining} รายการ")

    def _on_detection_risk_changed(self, risk_level: str) -> None:
        state = self._detection_edit_state
        if state is None or not state.selected_object_id or not self._active_scenario_id:
            return
        try:
            self.context.target_detection_service.update_detection_object_risk(
                scenario_id=self._active_scenario_id,
                target_card_id=state.target_id,
                target_coordinate_id=state.coordinate_id,
                map_object_id=state.selected_object_id,
                risk_level=risk_level,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "ปรับความเสี่ยงไม่สำเร็จ", str(exc))
            return
        self._refresh_detection_layers_and_ingress()
        self.statusBar().showMessage("ปรับระดับความเสี่ยงอาคาร · คำนวณทิศทางเข้า-ออกใหม่แล้ว")

    def _start_corridor_route_edit(
        self,
        *,
        target_id: str,
        coordinate_id: str | None,
        rank: int,
        flight_route: dict,
        takeoff_lat: float | None = None,
        takeoff_lng: float | None = None,
    ) -> None:
        marker = (
            self._marker_for_coordinate(target_id, coordinate_id)
            if coordinate_id
            else None
        ) or self._primary_marker_for_target(target_id)
        if marker is None:
            return

        risk_direction = marker.get("lowestRiskDirection") or {}
        options = risk_direction.get("recommendedOptions") or []
        option = next(
            (item for item in options if int(item.get("rank") or 0) == rank),
            options[rank - 1] if 0 < rank <= len(options) else None,
        )
        border_route = (option or {}).get("borderRoute") or {}
        target_lat = float(marker.get("lat") or 0.0)
        target_lng = float(marker.get("lng") or 0.0)
        wing = self._corridor_flight_wing(target_id, target_lat, target_lng)
        if wing is None:
            return

        detail = self.context.target_service.get_target_detail(target_id)
        target_label = (
            detail.card.label if detail is not None else str(marker.get("label") or "Target")
        )
        plan = self.context.weaponeering_service.get_deployment_plan_for_target(target_id)
        waypoints = list(flight_route.get("editableWaypoints") or [])
        resolved_takeoff_lat = (
            float(takeoff_lat) if takeoff_lat is not None else float(wing["lat"])
        )
        resolved_takeoff_lng = (
            float(takeoff_lng) if takeoff_lng is not None else float(wing["lng"])
        )
        self._corridor_route_edit_state = _CorridorRouteEditState(
            target_id=target_id,
            coordinate_id=coordinate_id,
            rank=rank,
            wing_id=str(wing["id"]),
            wing_name=str(wing["name"]),
            wing_lat=resolved_takeoff_lat,
            wing_lng=resolved_takeoff_lng,
            target_lat=target_lat,
            target_lng=target_lng,
            target_label=target_label,
            border_route=border_route,
            fly_through_waypoints=waypoints,
            plan=plan,
        )
        self.map_workspace.show_flight_route_editor(
            target_label=target_label,
            wing_name=str(wing["name"]),
            waypoint_count=len(waypoints),
            distance_label=self._sketch_route_distance_label(
                self._corridor_route_edit_state
            )
            if self._corridor_route_edit_state
            else "0 km",
            dirty=False,
        )
        self.map_widget.set_flight_route_edit_mode(True)
        self._update_flight_route_edit_toolbar()

    def _selected_flight_route_waypoint(self) -> dict | None:
        state = self._corridor_route_edit_state
        if state is None or not state.selected_waypoint_id:
            return None
        return next(
            (
                waypoint
                for waypoint in state.fly_through_waypoints
                if str(waypoint.get("id")) == state.selected_waypoint_id
            ),
            None,
        )

    def _sketch_route_distance_label(self, state: _CorridorRouteEditState) -> str:
        if state.use_ingress_corridor and state.ai_route_params is not None:
            outbound, return_wps = split_ai_route_waypoints(state.fly_through_waypoints)
            entry = (state.border_route or {}).get("entry")
            exit_point = (state.border_route or {}).get("exit")
            entry_coords = None
            exit_coords = None
            if isinstance(entry, dict) and entry.get("lat") is not None:
                entry_coords = (float(entry["lat"]), float(entry["lng"]))
            if isinstance(exit_point, dict) and exit_point.get("lat") is not None:
                exit_coords = (float(exit_point["lat"]), float(exit_point["lng"]))
            _, path3d = build_waypoint_connector_paths(
                takeoff=(state.wing_lat, state.wing_lng),
                target=(state.target_lat, state.target_lng),
                landing=(state.wing_lat, state.wing_lng),
                editable_waypoints=[*outbound, *return_wps],
                entry=entry_coords,
                exit_point=exit_coords,
            )
            points = [(lat, lng) for lat, lng, _alt in path3d]
        else:
            points = [(state.wing_lat, state.wing_lng)] + [
                (float(waypoint["lat"]), float(waypoint["lng"]))
                for waypoint in state.fly_through_waypoints
            ]
        if len(points) < 2:
            return "0 km"
        total_m = sum(
            distance_m(
                points[index][0],
                points[index][1],
                points[index + 1][0],
                points[index + 1][1],
            )
            for index in range(len(points) - 1)
        )
        if total_m >= 1000:
            return f"{total_m / 1000:.1f} km"
        return f"{int(round(total_m))} m"

    def _update_flight_route_edit_toolbar(self) -> None:
        state = self._corridor_route_edit_state
        if state is None:
            self.map_workspace.hide_flight_route_editor()
            return
        selected = self._selected_flight_route_waypoint()
        self.map_workspace.update_flight_route_editor(
            waypoint_count=len(state.fly_through_waypoints),
            distance_label=self._sketch_route_distance_label(state),
            dirty=state.dirty,
            selected_label=str(selected.get("label") or "") if selected else None,
            selected_waypoint_id=state.selected_waypoint_id,
            selected_altitude_ft=int(selected.get("altitudeFt") or 0) if selected else None,
            show_waypoints=state.show_waypoints,
            show_waypoint_labels=state.show_waypoint_labels,
        )

    def _on_flight_route_waypoints_visibility_changed(self, visible: bool) -> None:
        state = self._corridor_route_edit_state
        if state is None:
            return
        state.show_waypoints = visible
        self._refresh_corridor_route_display()

    def _on_flight_route_waypoint_labels_visibility_changed(self, visible: bool) -> None:
        state = self._corridor_route_edit_state
        if state is None:
            return
        state.show_waypoint_labels = visible
        self._refresh_corridor_route_display()

    def _refresh_corridor_route_display(self) -> None:
        state = self._corridor_route_edit_state
        if state is None:
            return
        if state.use_ingress_corridor and state.ai_route_params is not None:
            outbound_override, return_override = split_ai_route_waypoints(
                state.fly_through_waypoints
            )
            flight_route = plan_ai_flight_route(
                takeoff_lat=state.wing_lat,
                takeoff_lng=state.wing_lng,
                landing_lat=state.wing_lat,
                landing_lng=state.wing_lng,
                target_lat=state.target_lat,
                target_lng=state.target_lng,
                target_label=state.target_label,
                target_card_id=state.target_id,
                coordinate_id=state.coordinate_id,
                rank=state.rank,
                border_route=state.border_route,
                wing_id=state.wing_id,
                wing_name=state.wing_name,
                params=state.ai_route_params,
                ingress_bearing_deg=state.ai_ingress_bearing_deg,
                fly_through_waypoints_override=outbound_override or None,
                return_fly_through_waypoints_override=return_override or None,
                allow_terrain_network=False,
            )
            if flight_route is None:
                return
            attach_route_edit_metadata(
                flight_route,
                editable_waypoints=state.fly_through_waypoints,
                selected_waypoint_id=state.selected_waypoint_id,
                show_waypoints=state.show_waypoints,
                show_waypoint_labels=state.show_waypoint_labels,
                route_edit_enabled=True,
            )
            flight_route["drawWaypointConnectors"] = True
            flight_route["unifiedRoute"] = True
            flight_route["takeoff"] = [state.wing_lat, state.wing_lng]
            flight_route["destination"] = [state.target_lat, state.target_lng]
            entry = (state.border_route or {}).get("entry")
            exit_point = (state.border_route or {}).get("exit")
            if isinstance(entry, dict) and entry.get("lat") is not None:
                flight_route["borderEntry"] = [float(entry["lat"]), float(entry["lng"])]
            if isinstance(exit_point, dict) and exit_point.get("lat") is not None:
                flight_route["borderExit"] = [float(exit_point["lat"]), float(exit_point["lng"])]
            summary = str(flight_route.get("summary") or "")
        else:
            flight_route, summary = self._build_corridor_flight_route(
                state.target_id,
                state.coordinate_id,
                state.rank,
                edit_waypoints=state.fly_through_waypoints,
                selected_waypoint_id=state.selected_waypoint_id,
            )
            if flight_route is None:
                return
        self._corridor_flight_summary = summary
        self.map_widget.refresh_corridor_flight_route(
            state.target_id,
            state.coordinate_id,
            state.rank,
            flight_route,
        )
        self._update_flight_route_edit_toolbar()

    def _on_flight_route_waypoint_added(self, lat: float, lng: float) -> None:
        state = self._corridor_route_edit_state
        if state is None:
            return
        index = len(state.fly_through_waypoints) + 1
        state.fly_through_waypoints.append(
            {
                "id": str(uuid4()),
                "lat": lat,
                "lng": lng,
                "label": f"WP{index}",
                "altitudeFt": SIM_FLIGHT_DEFAULTS.fly_through_altitude_ft,
            }
        )
        state.selected_waypoint_id = str(state.fly_through_waypoints[-1]["id"])
        state.dirty = True
        self._refresh_corridor_route_display()

    def _on_flight_route_waypoint_moved(
        self,
        waypoint_id: str,
        lat: float,
        lng: float,
    ) -> None:
        state = self._corridor_route_edit_state
        if state is None:
            return
        for waypoint in state.fly_through_waypoints:
            if str(waypoint.get("id")) == waypoint_id:
                waypoint["lat"] = lat
                waypoint["lng"] = lng
                state.selected_waypoint_id = waypoint_id
                state.dirty = True
                break
        self._refresh_corridor_route_display()

    def _on_flight_route_waypoint_selected(self, waypoint_id: str) -> None:
        state = self._corridor_route_edit_state
        if state is None:
            return
        state.selected_waypoint_id = waypoint_id
        self._refresh_corridor_route_display()

    def _on_flight_route_delete_waypoint_requested(self) -> None:
        state = self._corridor_route_edit_state
        if state is None or not state.selected_waypoint_id:
            return
        state.fly_through_waypoints = [
            waypoint
            for waypoint in state.fly_through_waypoints
            if str(waypoint.get("id")) != state.selected_waypoint_id
        ]
        state.selected_waypoint_id = None
        state.dirty = True
        self._refresh_corridor_route_display()

    def _on_flight_route_waypoint_label_changed(self, label: str) -> None:
        state = self._corridor_route_edit_state
        if state is None or not state.selected_waypoint_id:
            return
        for waypoint in state.fly_through_waypoints:
            if str(waypoint.get("id")) == state.selected_waypoint_id:
                waypoint["label"] = label
                state.dirty = True
                break
        self._refresh_corridor_route_display()

    def _on_flight_route_waypoint_altitude_changed(self, altitude_ft: int) -> None:
        state = self._corridor_route_edit_state
        if state is None or not state.selected_waypoint_id:
            return
        for waypoint in state.fly_through_waypoints:
            if str(waypoint.get("id")) == state.selected_waypoint_id:
                waypoint["altitudeFt"] = altitude_ft
                state.dirty = True
                break
        self._refresh_corridor_route_display()

    def _on_ai_route_use_plan_endpoints_requested(self) -> None:
        self._sync_ai_route_from_flight_plan()

    def _on_ai_route_takeoff_pick_toggled(self, checked: bool) -> None:
        self.map_widget.set_route_pick_mode("takeoff" if checked else None)
        if checked:
            self.map_workspace.focus_map_for_interaction()

    def _on_ai_route_landing_pick_toggled(self, checked: bool) -> None:
        self.map_widget.set_route_pick_mode("landing" if checked else None)
        if checked:
            self.map_workspace.focus_map_for_interaction()

    def _on_route_point_picked(self, point_type: str, lat: float, lng: float) -> None:
        planner = self.map_workspace.ai_route_planner
        if point_type in {"takeoff", "landing"}:
            target_id = self._selected_map_target_id
            if target_id:
                self._sync_ai_route_from_flight_plan(target_id)
                planner.set_status(
                    "Takeoff/Landing ใช้พิกัดกองบินจากแผน · RTB กลับกองบินเดิม"
                )
            planner.clear_pick_modes()
            self.map_widget.set_route_pick_mode(None)
            return

    def _on_ai_route_clear_requested(self) -> None:
        self._ai_planned_route = None
        self.map_widget.clear_ai_flight_route()
        state = self._corridor_route_edit_state
        if state is not None and state.use_ingress_corridor:
            target_id = state.target_id
            self._clear_corridor_route_edit_state()
            self.map_widget.highlight_ingress_corridor(target_id, None, 0, None)
        self.map_workspace.ai_route_planner.set_route_ready(False)
        self.map_workspace.ai_route_planner.set_status("ล้างเส้นทาง AI แล้ว")

    def _normalize_fly_through_waypoints(self, waypoints: list[dict]) -> list[dict]:
        normalized: list[dict] = []
        for waypoint in waypoints:
            normalized.append(
                {
                    "id": str(waypoint.get("id") or uuid4()),
                    "lat": float(waypoint["lat"]),
                    "lng": float(waypoint["lng"]),
                    "label": str(waypoint.get("label") or "WP"),
                    "altitudeFt": int(
                        waypoint.get("altitudeFt") or SIM_FLIGHT_DEFAULTS.fly_through_altitude_ft
                    ),
                }
            )
        return normalized

    def _present_ai_route_on_map(
        self,
        *,
        target_id: str,
        coordinate_id: str | None,
        rank: int,
        route: dict,
        fly_through: list[dict],
        takeoff: tuple[float, float],
        landing: tuple[float, float],
        params: AiRoutePlannerParams,
        ingress_bearing_deg: float | None,
    ) -> None:
        route_display = dict(route)
        route_display.update(
            {
                "routeColor": "#38bdf8",
                "editableWaypoints": fly_through,
                "routeEditEnabled": True,
                "unifiedRoute": True,
                "showReturnRoute": False,
                "fitToRoute": True,
            }
        )
        self._start_corridor_route_edit(
            target_id=target_id,
            coordinate_id=coordinate_id,
            rank=rank,
            flight_route=route_display,
            takeoff_lat=takeoff[0],
            takeoff_lng=takeoff[1],
        )
        state = self._corridor_route_edit_state
        if state is None:
            return
        state.use_ingress_corridor = True
        state.ai_route_params = params
        state.ai_ingress_bearing_deg = ingress_bearing_deg
        state.fly_through_waypoints = fly_through
        state.dirty = False
        self.map_widget.clear_ai_flight_route()
        self.map_widget.highlight_ingress_corridor(
            target_id,
            coordinate_id,
            rank,
            None,
        )
        self._refresh_corridor_route_display()
        self._update_flight_route_edit_toolbar()

    def _on_ai_route_plan_requested(self) -> None:
        if self._ai_route_plan_worker is not None and self._ai_route_plan_worker.isRunning():
            return
        target_id = self._selected_map_target_id
        if not target_id:
            QMessageBox.information(self, "AI Route", "เลือก Target บนแผนที่ก่อน")
            return
        detail = self.context.target_service.get_target_detail(target_id)
        if detail is None:
            return
        marker = self._primary_marker_for_target(target_id)
        if marker is None:
            QMessageBox.warning(self, "AI Route", "Target ยังไม่มีพิกัดบนแผนที่")
            return
        target_lat = float(marker.get("lat") or 0.0)
        target_lng = float(marker.get("lng") or 0.0)
        resolved = self._resolve_ai_route_endpoints(target_id)
        if resolved is None:
            QMessageBox.warning(
                self,
                "AI Route",
                "ไม่พบกองบินใกล้เป้าหมาย — เพิ่มกองบินใน Database",
            )
            return
        takeoff, landing = resolved
        wing = self._corridor_flight_wing(target_id, target_lat, target_lng)
        if wing is None:
            QMessageBox.warning(
                self,
                "AI Route",
                "ไม่พบกองบินใกล้เป้าหมาย — เพิ่มกองบินใน Database",
            )
            return
        risk_direction = marker.get("lowestRiskDirection") or {}
        options = risk_direction.get("recommendedOptions") or []
        option = options[0] if options else {}
        border_route = option.get("borderRoute") or {}
        rank = int(option.get("rank") or 1)
        coordinate_id = str(marker.get("coordinateId") or "")
        planner = self.map_workspace.ai_route_planner
        params = AiRoutePlannerParams(
            route_style=planner.selected_route_style(),
            min_agl_m=planner.min_agl.value(),
            pref_agl_m=planner.pref_agl.value(),
            max_agl_m=planner.max_agl.value(),
            cruise_pad_m=planner.cruise_pad.value(),
            grid_m=planner.grid_m.value(),
            cruise_kts=planner.cruise_kts.value(),
            turn_radius_m=planner.turn_radius.value(),
            cruise_altitude_ft=planner.cruise_alt_ft.value(),
        )
        ingress_bearing = float(option.get("bearingDeg") or 0) or None

        def run_plan() -> dict | None:
            return plan_ai_flight_route(
                takeoff_lat=takeoff[0],
                takeoff_lng=takeoff[1],
                landing_lat=landing[0],
                landing_lng=landing[1],
                target_lat=target_lat,
                target_lng=target_lng,
                target_label=detail.card.label,
                target_card_id=target_id,
                coordinate_id=coordinate_id or None,
                rank=rank,
                border_route=border_route,
                wing_id=str(wing["id"]),
                wing_name=str(wing["name"]),
                params=params,
                ingress_bearing_deg=ingress_bearing,
                allow_terrain_network=True,
            )

        planner.set_planning_busy(True, "กำลังวางเส้นทางตามชายแดน…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        worker = _AiRoutePlanWorker(run_plan)
        self._ai_route_plan_worker = worker

        def on_ready(route: object) -> None:
            QApplication.restoreOverrideCursor()
            planner.set_planning_busy(False)
            if not isinstance(route, dict):
                return
            self.map_widget.clear_ai_flight_route()
            raw_waypoints = route.get("editableWaypoints") or extract_editable_fly_through_waypoints(
                route
            )
            fly_through = self._normalize_fly_through_waypoints(raw_waypoints)
            self._ai_planned_route = route
            self._present_ai_route_on_map(
                target_id=target_id,
                coordinate_id=coordinate_id or None,
                rank=rank,
                route=route,
                fly_through=fly_through,
                takeoff=takeoff,
                landing=landing,
                params=params,
                ingress_bearing_deg=ingress_bearing,
            )
            planner.set_route_ready(True)
            planner.set_status(str(route.get("summary") or "วางเส้นทาง AI แล้ว"))
            self.statusBar().showMessage(
                "AI Route Planner · วางเส้นทางแล้ว · แก้ไขจุดได้ · กด Apply เพื่อบันทึก"
            )
            worker.deleteLater()
            if self._ai_route_plan_worker is worker:
                self._ai_route_plan_worker = None

        def on_failed(reason: str) -> None:
            QApplication.restoreOverrideCursor()
            planner.set_planning_busy(False)
            if reason == "no_route":
                QMessageBox.warning(
                    self,
                    "AI Route",
                    "ยังไม่มีเส้นทางเข้า-ออกชายแดน · รัน Detection ก่อน",
                )
            else:
                QMessageBox.warning(self, "AI Route", f"วางเส้นทางไม่สำเร็จ\n\n{reason}")
            worker.deleteLater()
            if self._ai_route_plan_worker is worker:
                self._ai_route_plan_worker = None

        worker.route_ready.connect(on_ready)
        worker.failed.connect(on_failed)
        worker.start()

    def _on_ai_route_apply_requested(self) -> None:
        route = self._ai_planned_route
        target_id = self._selected_map_target_id
        if route is None or not target_id:
            return
        state = self._corridor_route_edit_state
        if state is None or not state.use_ingress_corridor:
            rank = int(route.get("rank") or 1)
            coordinate_id = route.get("coordinateId")
            coord_key = str(coordinate_id) if coordinate_id else None
            fly_through = self._normalize_fly_through_waypoints(
                extract_editable_fly_through_waypoints(route)
            )
            takeoff_coords = route.get("takeoff")
            landing_coords = route.get("landing")
            resolved = self._resolve_ai_route_endpoints(target_id)
            if resolved is not None:
                if not takeoff_coords:
                    takeoff_coords = [resolved[0][0], resolved[0][1]]
                if not landing_coords:
                    landing_coords = [resolved[1][0], resolved[1][1]]
            takeoff_coords = takeoff_coords or [0.0, 0.0]
            landing_coords = landing_coords or takeoff_coords
            planner = self.map_workspace.ai_route_planner
            params = AiRoutePlannerParams(
                route_style=planner.selected_route_style(),
                min_agl_m=planner.min_agl.value(),
                pref_agl_m=planner.pref_agl.value(),
                max_agl_m=planner.max_agl.value(),
                cruise_kts=planner.cruise_kts.value(),
                cruise_altitude_ft=planner.cruise_alt_ft.value(),
            )
            self._present_ai_route_on_map(
                target_id=target_id,
                coordinate_id=coord_key,
                rank=rank,
                route=route,
                fly_through=fly_through,
                takeoff=(float(takeoff_coords[0]), float(takeoff_coords[1])),
                landing=(float(landing_coords[0]), float(landing_coords[1])),
                params=params,
                ingress_bearing_deg=float(route.get("ingressBearingDeg") or 0) or None,
            )
            state = self._corridor_route_edit_state
        if state is not None:
            state.dirty = True
            self._on_flight_route_approve_requested()
        takeoff_coords = route.get("takeoff")
        landing_coords = route.get("landing")
        if takeoff_coords and landing_coords:
            self._upsert_plan_endpoints(
                target_id,
                takeoff_lat=float(takeoff_coords[0]),
                takeoff_lng=float(takeoff_coords[1]),
                landing_lat=float(landing_coords[0]),
                landing_lng=float(landing_coords[1]),
                landing_altitude_ft=0,
            )
        self._sync_ai_route_from_flight_plan(target_id)
        self._ai_planned_route = None
        self.map_workspace.ai_route_planner.set_route_ready(False)
        self.map_workspace.ai_route_planner.set_status("บันทึกเส้นทาง AI ลงแผนแล้ว")

    def _deployment_waypoint_requests_from_edit_state(
        self,
        state: _CorridorRouteEditState,
    ) -> tuple[DeploymentWaypointRequest, ...]:
        requests: list[DeploymentWaypointRequest] = []
        for waypoint in state.fly_through_waypoints:
            requests.append(
                DeploymentWaypointRequest(
                    lat=float(waypoint["lat"]),
                    lng=float(waypoint["lng"]),
                    label=str(waypoint.get("label") or ""),
                    waypoint_type="fly_through",
                    altitude_ft=int(waypoint["altitudeFt"])
                    if waypoint.get("altitudeFt") is not None
                    else None,
                )
            )
        plan = state.plan
        if plan is not None:
            for waypoint in plan.waypoints:
                if waypoint.waypoint_type != "return":
                    continue
                requests.append(
                    DeploymentWaypointRequest(
                        lat=waypoint.lat,
                        lng=waypoint.lng,
                        label=waypoint.label or "",
                        waypoint_type="return",
                        altitude_ft=waypoint.altitude_ft,
                    )
                )
        return tuple(requests)

    def _build_deployment_plan_request_from_edit_state(
        self,
        state: _CorridorRouteEditState,
    ) -> UpsertDeploymentPlanRequest | None:
        if not self._active_scenario_id:
            return None
        waypoint_requests = self._deployment_waypoint_requests_from_edit_state(state)
        plan = state.plan
        if plan is not None:
            aircraft_lines = tuple(
                DeploymentAircraftLineRequest(
                    aircraft_id=line.aircraft_id,
                    aircraft_count=line.aircraft_count,
                )
                for line in plan.aircraft_lines
            )
            return UpsertDeploymentPlanRequest(
                scenario_id=self._active_scenario_id,
                target_card_id=state.target_id,
                wing_id=plan.wing_id,
                flying_unit_id=plan.flying_unit_id,
                aircraft_lines=aircraft_lines,
                takeoff_lat=plan.takeoff_lat,
                takeoff_lng=plan.takeoff_lng,
                ingress_bearing_deg=plan.ingress_bearing_deg,
                ingress_offset_m=plan.ingress_offset_m,
                cruise_altitude_ft=plan.cruise_altitude_ft,
                ingress_altitude_ft=plan.ingress_altitude_ft,
                target_altitude_ft=plan.target_altitude_ft,
                climb_rate_ft_min=plan.climb_rate_ft_min,
                descent_rate_ft_min=plan.descent_rate_ft_min,
                return_enabled=plan.return_enabled,
                cruise_speed_kt=plan.cruise_speed_kt,
                climb_speed_kt=plan.climb_speed_kt,
                descent_speed_kt=plan.descent_speed_kt,
                ingress_speed_kt=plan.ingress_speed_kt,
                bank_angle_deg=plan.bank_angle_deg,
                turn_mode=plan.turn_mode,
                auto_toc_tod=plan.auto_toc_tod,
                waypoints=waypoint_requests,
            )

        units = [
            unit
            for unit in self.context.wing_data_service.list_flying_units(
                self._active_scenario_id
            )
            if unit.wing_id == state.wing_id
        ]
        aircraft_rows = [
            aircraft
            for aircraft in self.context.wing_data_service.list_aircraft(
                self._active_scenario_id
            )
            if aircraft.wing_id == state.wing_id
        ]
        if not units or not aircraft_rows:
            return None
        unit = units[0]
        aircraft = next(
            (row for row in aircraft_rows if row.flying_unit_id == unit.id),
            aircraft_rows[0],
        )
        defaults = SIM_FLIGHT_DEFAULTS
        return UpsertDeploymentPlanRequest(
            scenario_id=self._active_scenario_id,
            target_card_id=state.target_id,
            wing_id=state.wing_id,
            flying_unit_id=unit.id,
            aircraft_lines=(
                DeploymentAircraftLineRequest(
                    aircraft_id=aircraft.id,
                    aircraft_count=1,
                ),
            ),
            ingress_bearing_deg=float(defaults.ingress_heading_deg),
            ingress_offset_m=int(defaults.ingress_distance_m),
            cruise_altitude_ft=defaults.cruise_altitude_ft,
            ingress_altitude_ft=defaults.ingress_altitude_ft,
            target_altitude_ft=defaults.fly_through_altitude_ft,
            climb_rate_ft_min=defaults.climb_rate_ft_min,
            descent_rate_ft_min=defaults.descent_rate_ft_min,
            return_enabled=defaults.rtb_enabled,
            cruise_speed_kt=defaults.cruise_speed_kt,
            climb_speed_kt=defaults.climb_speed_kt,
            descent_speed_kt=defaults.descent_speed_kt,
            ingress_speed_kt=defaults.ingress_speed_kt,
            bank_angle_deg=defaults.ingress_bank_deg,
            turn_mode=defaults.turn_mode,
            auto_toc_tod=defaults.auto_toc_tod,
            waypoints=waypoint_requests,
        )

    def _sync_edit_waypoints_from_plan(self, state: _CorridorRouteEditState) -> None:
        plan = self.context.weaponeering_service.get_deployment_plan_for_target(
            state.target_id
        )
        state.plan = plan
        if plan is None:
            return
        labels_by_position = {
            (round(float(waypoint["lat"]), 5), round(float(waypoint["lng"]), 5)): str(
                waypoint.get("label") or ""
            )
            for waypoint in state.fly_through_waypoints
        }
        state.fly_through_waypoints = [
            {
                "id": waypoint.id,
                "lat": waypoint.lat,
                "lng": waypoint.lng,
                "label": waypoint.label
                or labels_by_position.get(
                    (round(waypoint.lat, 5), round(waypoint.lng, 5)),
                    f"WP{index + 1}",
                ),
            }
            for index, waypoint in enumerate(plan.waypoints)
            if waypoint.waypoint_type == "fly_through"
        ]
        state.selected_waypoint_id = None

    def _on_flight_route_approve_requested(self) -> None:
        state = self._corridor_route_edit_state
        if state is None:
            QMessageBox.information(
                self,
                "บันทึกแผนการบิน",
                "เปิดเส้นทางจาก「ดู」ในทิศทางความเสี่ยงต่ำก่อน",
            )
            return
        if not state.dirty:
            QMessageBox.information(
                self,
                "บันทึกแผนการบิน",
                "เพิ่มหรือแก้ไขจุดบนแผนที่ก่อนกดอนุมัติ",
            )
            return
        request = self._build_deployment_plan_request_from_edit_state(state)
        if request is None:
            QMessageBox.warning(
                self,
                "บันทึกแผนไม่สำเร็จ",
                "ต้องตั้งค่ากองบิน หน่วยบิน และเครื่องบินใน Database ก่อน "
                "หรือบันทึกแผน Weaponeering เบื้องต้นในแท็บ Weaponeering",
            )
            return
        try:
            self.context.weaponeering_service.upsert_deployment_plan(request)
        except ValueError as error:
            QMessageBox.warning(self, "บันทึกแผนไม่สำเร็จ", str(error))
            return

        state.dirty = False
        self._sync_edit_waypoints_from_plan(state)
        self.weaponeering_panel.reload_deployment_plan_for_target(state.target_id)
        self.weaponeering_panel.weaponeering_changed.emit()
        self._refresh_corridor_route_display()
        QMessageBox.information(
            self,
            "บันทึกแผนการบิน",
            f"บันทึกจุดเส้นทาง {len(state.fly_through_waypoints)} จุด "
            "ลงแผน Weaponeering แล้ว",
        )

    @staticmethod
    def _target_location_text(lat: float | None, lng: float | None) -> str:
        if lat is None or lng is None:
            return "Location: ยังไม่ได้เชื่อมพิกัดบนแผนที่"
        return f"Location: {lat:.5f}, {lng:.5f}"

    @staticmethod
    def _target_recognition_text(detail) -> str:
        if detail.recognition is None:
            return "Recognition: ยังไม่มีผล Target Recognition"
        return (
            f"Recognition: {detail.recognition.recognition_confidence_score}/100 · "
            f"{detail.recognition.recognition_summary}"
        )

    def _target_risk_payload(self, target_id: str) -> dict:
        run = self.context.target_detection_service.get_run_for_target(target_id)
        if run is None:
            return {
                "objectCount": 0,
                "highCount": 0,
                "mediumCount": 0,
                "lowCount": 0,
                "modelName": "—",
                "detail": "ยังไม่มีผล Object Detection สำหรับ Target นี้",
                "objects": [],
            }
        high = sum(1 for obj in run.objects if obj.risk_level == "high")
        medium = sum(1 for obj in run.objects if obj.risk_level == "medium")
        low = sum(1 for obj in run.objects if obj.risk_level == "low")
        labels = {}
        for obj in run.objects:
            labels[obj.object_label] = labels.get(obj.object_label, 0) + 1
        label_text = ", ".join(
            f"{label} {count}" for label, count in sorted(labels.items())[:4]
        )
        detail = run.detection_message or "Detection run saved"
        if label_text:
            detail = f"{detail}\nObjects: {label_text}"
        return {
            "objectCount": run.object_count,
            "highCount": high,
            "mediumCount": medium,
            "lowCount": low,
            "modelName": run.model_name,
            "detail": detail,
            "objects": [
                {
                    "label": obj.object_label,
                    "type": obj.object_type,
                    "riskLevel": obj.risk_level,
                    "riskMeaning": self._risk_meaning(obj.risk_level),
                    "confidence": obj.confidence,
                    "lat": obj.center_lat,
                    "lng": obj.center_lng,
                }
                for obj in run.objects
            ],
        }

    @staticmethod
    def _risk_meaning(risk_level: str) -> str:
        if risk_level == "high":
            return "ได้รับผลกระทบสูง"
        if risk_level == "medium":
            return "ได้รับผลกระทบปานกลาง"
        if risk_level == "low":
            return "ได้รับผลกระทบต่ำ"
        return "ไม่ระบุระดับผลกระทบ"

    def _target_product_ranking_payload(
        self,
        detail,
        *,
        coordinate=None,
    ) -> list[dict]:
        products = self.context.wing_data_service.list_products(self._active_scenario_id)
        if not products:
            return []
        mission = mission_inputs_from_target_card(detail.card)
        weapons = [
            JmemWeaponInputs(
                product_id=product.id,
                product_name=product.product_name,
                weight_pounds=product.weight_pounds,
                mae_building_ft2=estimate_mae_building_ft2(
                    product.product_name,
                    product.weight_pounds,
                ),
            )
            for product in products
        ]
        selected_product_id = resolve_coordinate_product_id(coordinate, detail.card)
        return [
            {
                "rank": result.rank,
                "productName": result.product_name,
                "pdBase": result.pd_base,
                "nRequired": result.n_required,
            }
            for result in apply_selected_product_rank(
                rank_weapons(mission, weapons),
                selected_product_id,
            )[:5]
        ]

    def _target_weaponeering_detail_payload(
        self,
        target_id: str,
        detail,
    ) -> dict[str, object]:
        catalog_products = self.context.wing_data_service.list_products(
            self._active_scenario_id
        )
        product_catalog = [
            {"id": product.id, "name": product.product_name}
            for product in catalog_products
        ]
        coordinate_products: list[dict[str, object]] = []
        markers = self._markers_for_target(target_id)
        marker_by_coord = {
            str(marker.get("coordinateId") or ""): marker
            for marker in markers
            if marker.get("coordinateId")
        }
        if detail.coordinates:
            for index, coord in enumerate(detail.coordinates):
                marker = marker_by_coord.get(coord.id)
                coordinate_products.append(
                    {
                        "coordinateId": coord.id,
                        "label": coord.label.strip() or f"P{index + 1}",
                        "isPrimary": coord.is_primary,
                        "selectedProductId": resolve_coordinate_product_id(
                            coord,
                            detail.card,
                        ),
                        "effectProduct": (
                            str(marker.get("effectProduct"))
                            if marker and marker.get("effectProduct")
                            else None
                        ),
                        "products": self._target_product_ranking_payload(
                            detail,
                            coordinate=coord,
                        ),
                    }
                )
        products = self._target_product_ranking_payload(detail)
        plan_summary = self._target_plan_payload(target_id)
        nearest_wing = self._nearest_wing_payload(detail.map_lat, detail.map_lng)
        plan = self.context.weaponeering_service.get_deployment_plan_for_target(target_id)
        plan_fields: dict[str, object] = {}
        if plan is not None:
            takeoff_text = "—"
            if plan.takeoff_lat is not None and plan.takeoff_lng is not None:
                takeoff_text = f"{plan.takeoff_lat:.5f}, {plan.takeoff_lng:.5f}"
            ingress_text = "—"
            if plan.ingress_bearing_deg is not None:
                ingress_text = (
                    f"{plan.ingress_bearing_deg:.0f}° · "
                    f"offset {plan.ingress_offset_m / 1000:.1f} km"
                )
            plan_fields = {
                "takeoff": takeoff_text,
                "ingress": ingress_text,
                "cruiseAltFt": plan.cruise_altitude_ft,
                "ingressAltFt": plan.ingress_altitude_ft,
                "targetAltFt": plan.target_altitude_ft,
                "waypointCount": len(plan.waypoints),
                "returnEnabled": plan.return_enabled,
            }
        return {
            "products": products,
            "productCatalog": product_catalog,
            "coordinateProducts": coordinate_products,
            "plan": plan_summary,
            "planFields": plan_fields,
            "nearestWing": nearest_wing,
            "hasSavedPlan": plan is not None,
        }

    def _target_plan_payload(self, target_id: str) -> dict:
        plan = self.context.weaponeering_service.get_deployment_plan_for_target(target_id)
        if plan is None:
            return {
                "status": "No plan",
                "detail": "ยังไม่ได้บันทึกแผนประจำ Target",
            }
        wing = self.context.wing_data_service.get_wing(plan.wing_id)
        unit = self.context.wing_data_service.get_flying_unit(plan.flying_unit_id)
        aircraft_lines = []
        for line in plan.aircraft_lines:
            aircraft = self.context.wing_data_service.get_aircraft(line.aircraft_id)
            aircraft_type = aircraft.aircraft_type if aircraft else line.aircraft_id[:8]
            aircraft_lines.append(f"{aircraft_type} x{line.aircraft_count}")
        route_parts = []
        if plan.takeoff_lat is not None and plan.takeoff_lng is not None:
            route_parts.append(f"Takeoff {plan.takeoff_lat:.4f}, {plan.takeoff_lng:.4f}")
        if plan.waypoints:
            route_parts.append(f"Waypoints {len(plan.waypoints)}")
        if plan.ingress_bearing_deg is not None:
            route_parts.append(f"Sector {plan.ingress_bearing_deg:.0f}°")
        return {
            "status": "Plan saved",
            "detail": (
                f"{wing.wing_name if wing else plan.wing_id[:8]} · "
                f"{unit.unit_name if unit else plan.flying_unit_id[:8]} · "
                f"Aircraft total {plan.total_aircraft_count}"
            ),
            "aircraft": "Aircraft: " + (", ".join(aircraft_lines) if aircraft_lines else "—"),
            "route": " · ".join(route_parts) if route_parts else "Route: not configured",
        }

    def _nearest_wing_payload(self, lat: float | None, lng: float | None) -> dict:
        if lat is None or lng is None or not self._active_scenario_id:
            return {
                "name": "—",
                "distance": "ต้องมีพิกัด Target และกองบินใน Database",
            }
        nearest = self.context.wing_data_service.find_nearest_wing(
            self._active_scenario_id,
            lat,
            lng,
        )
        if nearest is None:
            return {
                "name": "—",
                "distance": "ไม่พบกองบินที่มีพิกัด",
            }
        aircraft = [
            item
            for item in self.context.wing_data_service.list_aircraft(self._active_scenario_id)
            if item.wing_id == nearest.wing_id
        ]
        ready = sum(1 for item in aircraft if item.mission_ready == "ready")
        readiness = (
            f"Aircraft: {ready}/{len(aircraft)} ready"
            if aircraft
            else "Aircraft: ยังไม่มีข้อมูลเครื่องบินในกองบินนี้"
        )
        return {
            "name": nearest.wing_name,
            "distance": f"{nearest.distance_km:.1f} km ({nearest.distance_nm:.1f} NM)",
            "readiness": readiness,
        }

    def _on_target_selected(self, target_id: str) -> None:
        self._selected_map_target_id = target_id
        detail = self.context.target_service.get_target_detail(target_id)
        coordinates = self.target_panel.get_detection_coordinates(target_id)
        self.map_workspace.set_detection_coordinates(coordinates)
        if detail and detail.map_lat is not None and detail.map_lng is not None:
            self.map_workspace.clear_ingress_corridor_focus()
            self._clear_corridor_route_edit_state()
            self._corridor_flight_summary = None
            self.map_widget.highlight_ingress_corridor(target_id, None, 0, None)
            self.map_widget.highlight_target(target_id)
        self._refresh_target_output_panel(target_id)

    def _on_targets_changed(self) -> None:
        self._refresh_map_layers()
        self.map_detail_sidebar.refresh_targets()
        self.review_panel.refresh()
        if self.weaponeering_panel._selected_target_id:
            self.weaponeering_panel.recalculate()
        if self._selected_map_target_id:
            target_id = self._selected_map_target_id
            coordinates = self.target_panel.get_detection_coordinates(target_id)
            self.map_workspace.set_detection_coordinates(coordinates)

    def _on_target_create_at_requested(self, lat: float, lng: float) -> None:
        if not self._active_scenario_id:
            QMessageBox.information(
                self,
                "สร้างเป้าหมาย",
                "เลือกหรือสร้าง scenario ก่อน",
            )
            return
        existing = len(
            self.context.target_service.list_target_cards(self._active_scenario_id)
        )
        dialog = QuickCreateTargetDialog(
            lat=lat,
            lng=lng,
            default_label=f"TGT-{existing + 1:03d}",
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if not values["label"]:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "กรุณากรอกชื่อเป้าหมาย")
            return
        target_type = values["target_type"]
        try:
            target_id = self.context.target_service.create_target_card(
                CreateTargetCardRequest(
                    scenario_id=self._active_scenario_id,
                    label=values["label"],
                    priority_score=values["priority_score"],
                    complexity_score=3,
                    profile=TargetProfileFields(
                        target_type=target_type,
                        target_subtype=subtypes_for_target_type(target_type)[0],
                    ),
                )
            )
            self.context.target_service.save_target_coordinates(
                SaveTargetCoordinatesRequest(
                    target_card_id=target_id,
                    scenario_id=self._active_scenario_id,
                    coordinates=[
                        TargetCoordinateInput(
                            label="P1",
                            map_lat=lat,
                            map_lng=lng,
                            is_primary=True,
                        )
                    ],
                )
            )
        except ValueError as exc:
            QMessageBox.warning(self, "สร้างเป้าหมายไม่สำเร็จ", str(exc))
            return
        self.target_panel.refresh()
        self._on_targets_changed()
        self._on_open_target_from_map(target_id)
        self.statusBar().showMessage(
            f"สร้างเป้าหมาย {values['label']} ที่ {lat:.5f}, {lng:.5f}"
        )

    def _on_coordinate_product_changed(
        self,
        coordinate_id: str,
        product_id: object,
    ) -> None:
        selected = str(product_id) if product_id else None
        try:
            self.context.target_service.set_coordinate_selected_product(
                coordinate_id,
                selected,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "เลือกสินค้าไม่สำเร็จ", str(exc))
            return
        self.weaponeering_panel.recalculate()
        self._schedule_map_layers_refresh()
        if self._selected_map_target_id:
            self._refresh_map_target_detail(self._selected_map_target_id)
            self._refresh_target_output_panel(self._selected_map_target_id)

    def _on_team_marker_place_requested(
        self,
        side: str,
        unit_type: str,
        lat: float,
        lng: float,
    ) -> None:
        if not self._active_scenario_id:
            QMessageBox.information(
                self,
                "เพิ่มหน่วยบนแผนที่",
                "เลือกหรือสร้าง scenario ก่อน",
            )
            return
        normalized_side = side.strip().lower()
        if normalized_side not in {"blue", "red"}:
            return
        normalized_unit_type = unit_type.strip().lower() or "generic"
        if normalized_unit_type not in VALID_UNIT_TYPES:
            normalized_unit_type = "generic"
        existing = [
            marker
            for marker in self.context.team_marker_service.list_markers(
                self._active_scenario_id
            )
            if marker.side == normalized_side
            and marker.unit_type == normalized_unit_type
        ]
        default_name = self.context.team_marker_service.default_marker_name(
            normalized_side,
            normalized_unit_type,
            len(existing),
        )
        side_label = "ฝ่ายเรา (Blue)" if normalized_side == "blue" else "ฝ่ายตรงข้าม (Red)"
        unit_label = UNIT_TYPES.get(normalized_unit_type, normalized_unit_type)
        name, accepted = QInputDialog.getText(
            self,
            "ตั้งชื่อหน่วย",
            (
                f"ชื่อหน่วย · {unit_label} · {side_label}\n"
                f"พิกัด {lat:.5f}, {lng:.5f}"
            ),
            text=default_name,
        )
        if not accepted:
            return
        radius_m: float | None = None
        if normalized_unit_type == "radar":
            radius_m, radius_ok = QInputDialog.getDouble(
                self,
                "รัศมีเรดาร์",
                (
                    f"รัศมีครอบคลุม (เมตร) · {side_label}\n"
                    f"พิกัด {lat:.5f}, {lng:.5f}"
                ),
                DEFAULT_RADAR_RADIUS_M,
                MIN_RADAR_RADIUS_M,
                MAX_RADAR_RADIUS_M,
                0,
            )
            if not radius_ok:
                return
        try:
            marker_id = self.context.team_marker_service.create_marker(
                scenario_id=self._active_scenario_id,
                side=normalized_side,
                unit_type=normalized_unit_type,
                label=name,
                map_lat=lat,
                map_lng=lng,
                radius_m=radius_m,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "เพิ่มหน่วยไม่สำเร็จ", str(exc))
            return
        self._refresh_team_markers_only()
        teams_layer = self.map_workspace._layer_actions.get("teams")
        if teams_layer is not None:
            teams_layer.setChecked(True)
            self.map_workspace._emit_layer_visibility()
        prefix = "BLUE" if normalized_side == "blue" else "RED"
        radius_note = ""
        if normalized_unit_type == "radar" and radius_m is not None:
            radius_note = f" · รัศมี {radius_m:,.0f} m"
        self.statusBar().showMessage(
            f"เพิ่ม {unit_label} · {prefix} · {name.strip()}{radius_note} "
            f"ที่ {lat:.5f}, {lng:.5f} ({marker_id[:8]})"
        )

    def _on_map_search_requested(self, lat: float, lng: float) -> None:
        self._show_workspace_tab("map")
        self.map_widget.fit_to_target(lat, lng)
        self.statusBar().showMessage(f"ค้นหาพิกัด {lat:.5f}, {lng:.5f} บนแผนที่")

    def _on_link_map_requested(self, target_id: str) -> None:
        self._link_target_id = target_id
        self.map_widget.set_route_add_mode(False)
        self.map_widget.enable_link_mode(True)
        self._show_workspace_tab("map")
        self.map_workspace.focus_map_for_interaction()
        self.statusBar().showMessage("คลิกบนแผนที่เพื่อเชื่อม Target Card กับตำแหน่ง")

    def _on_map_link_click(self, lat: float, lng: float) -> None:
        if not self._link_target_id:
            return
        self.target_panel.complete_map_link(self._link_target_id, lat, lng)
        self.target_panel.refresh()
        self._link_target_id = None
        self.map_widget.enable_link_mode(False)
        self._refresh_map_layers()
        self.statusBar().showMessage("เชื่อม Target Card กับแผนที่แล้ว")

    def _on_map_measure_updated(self, distance_m: float) -> None:
        if distance_m <= 0:
            return
        self.statusBar().showMessage(
            f"วัดระยะบนแผนที่: {self._format_map_distance(distance_m)}"
        )

    def _on_map_measure_radius_updated(self, radius_m: float) -> None:
        if radius_m <= 0:
            return
        self.statusBar().showMessage(
            f"วัดรัศมีบนแผนที่: {self._format_map_distance(radius_m)}"
        )

    @staticmethod
    def _format_map_distance(distance_m: float) -> str:
        if distance_m >= 1000:
            return f"{distance_m / 1000:.2f} km"
        return f"{int(round(distance_m))} m"

    def _schedule_map_layers_refresh(self) -> None:
        self._map_layers_refresh_timer.start()

    def _refresh_team_markers_only(self) -> None:
        if not self._active_scenario_id:
            self.map_widget.set_team_markers([])
            return
        team_markers = self.context.team_marker_service.list_map_markers(
            self._active_scenario_id
        )
        self.map_widget.set_team_markers(team_markers)

    def _refresh_map_layers(self) -> None:
        if not self._active_scenario_id:
            self.map_widget.set_target_markers([])
            self.map_widget.set_asset_layers(
                {
                    "organizations": [],
                    "depots": [],
                    "routes": [],
                    "deploymentLinks": [],
                }
            )
            self.map_widget.set_detection_objects([])
            self.map_widget.set_team_markers([])
            self.map_widget.set_ground_transport_routes([])
            self.right_panel.clear_target_output()
            return
        targets = enrich_target_markers_with_effect_radii(
            self.context.target_service.list_map_markers(self._active_scenario_id),
            self._active_scenario_id,
            self.context.target_service,
            self.context.wing_data_service,
        )
        assets: dict[str, list] = {
            "organizations": [],
            "depots": [],
            "routes": [],
            "deploymentLinks": [],
        }
        wing_layers = self.context.wing_data_service.list_map_layers(self._active_scenario_id)
        for marker in wing_layers["wings"]:
            assets["organizations"].append({
                "entityId": marker["entityId"],
                "entityType": "air_wing",
                "label": marker["label"],
                "lat": marker["lat"],
                "lng": marker["lng"],
                "readiness": "wing",
            })
        for marker in wing_layers["depots"]:
            assets["depots"].append({
                "entityId": marker["entityId"],
                "entityType": "wing_depot",
                "label": marker["label"],
                "lat": marker["lat"],
                "lng": marker["lng"],
                "availability": marker["availability"],
            })
        logistics_layers = self.context.logistics_service.list_map_layers(
            self._active_scenario_id
        )
        assets["routes"] = logistics_layers.get("routes", [])
        detection_objects = (
            self.context.target_detection_service.list_map_objects_for_scenario(
                self._active_scenario_id
            )
        )
        self._last_map_targets = targets
        for marker in targets:
            effect_radii = marker.get("effectRadii") or []
            fallback_radius = max(
                (float(item.get("radiusM", 0)) for item in effect_radii),
                default=120.0,
            )
            marker["lowestRiskDirection"] = (
                self.context.target_detection_service.build_lowest_risk_direction(
                    target_card_id=str(marker["targetCardId"]),
                    target_coordinate_id=marker.get("coordinateId"),
                    lat=float(marker["lat"]),
                    lng=float(marker["lng"]),
                    fallback_radius_m=fallback_radius,
                )
            )
        self.map_widget.set_target_markers(targets)
        self.map_widget.set_asset_layers(assets)
        self.map_widget.set_detection_objects(detection_objects)
        team_markers = self.context.team_marker_service.list_map_markers(
            self._active_scenario_id
        )
        self.map_widget.set_team_markers(team_markers)
        self._refresh_ground_transport_routes()
        if self._selected_map_target_id:
            self._refresh_target_output_panel(self._selected_map_target_id)

    def _refresh_ground_transport_routes(self) -> None:
        if not self._active_scenario_id or not self._selected_ground_transport_id:
            self.map_widget.set_ground_transport_routes([])
            return
        routes = self.context.ground_transport_service.list_map_routes(
            self._active_scenario_id,
            selected_id=self._selected_ground_transport_id,
        )
        selected = [
            route
            for route in routes
            if route["id"] == self._selected_ground_transport_id
        ]
        self.map_widget.set_ground_transport_routes(selected)

    def _on_ground_transport_selected(self, transport_id: str) -> None:
        if not transport_id:
            self._selected_ground_transport_id = None
            self.map_detail_sidebar.select_transport(None)
            self._refresh_ground_transport_routes()
            self.statusBar().showMessage("ยกเลิกการแสดงเส้นทางขนส่ง")
            return
        self._selected_ground_transport_id = transport_id
        self.map_detail_sidebar.select_transport(transport_id)
        self._refresh_ground_transport_routes()
        routes = self.context.ground_transport_service.list_map_routes(
            self._active_scenario_id or "",
            selected_id=transport_id,
        )
        route = next((item for item in routes if item["id"] == transport_id), None)
        if route is None:
            return
        origin = route.get("origin") or []
        destination = route.get("destination") or []
        if len(origin) >= 2 and len(destination) >= 2:
            mid_lat = (float(origin[0]) + float(destination[0])) / 2
            mid_lng = (float(origin[1]) + float(destination[1])) / 2
            focus_radius = max(float(route.get("distanceM") or 0) / 2, 5000)
            self.map_widget.fit_to_target(mid_lat, mid_lng, focus_radius)
        self.statusBar().showMessage(
            "ขนส่งทางบก · "
            f"{route.get('originWingName', '')} → {route.get('destinationWingName', '')} · "
            f"{format_distance_m(float(route.get('distanceM') or 0))} · "
            f"{format_duration_min(float(route.get('durationMin') or 0))}"
        )

    def _on_ground_transports_changed(self) -> None:
        self.map_detail_sidebar.refresh_transports()
        if self._selected_ground_transport_id:
            exists = any(
                item.id == self._selected_ground_transport_id
                for item in self.context.ground_transport_service.list_transports(
                    self._active_scenario_id or ""
                )
            )
            if not exists:
                self._selected_ground_transport_id = None
                self.map_detail_sidebar.select_transport(None)
        self._refresh_ground_transport_routes()

    def _load_latest_logistics_score(self) -> None:
        if not self._active_scenario_id:
            return
        score = self.context.logistics_service.get_latest_plan_score(self._active_scenario_id)
        if score:
            self.right_panel.set_logistics_result(
                score.logistics_feasibility,
                score.rationale,
                [],
            )

    def _check_export_readiness(self) -> None:
        if not self._active_scenario_id:
            return
        from maap_app.modules.export.schemas import ExportReadinessRequest

        result = self.context.export_service.check_readiness(
            ExportReadinessRequest(
                scenario_id=self._active_scenario_id,
                export_type="full_package",
            )
        )
        text = "Ready" if result.ready else "; ".join(result.blockers[:2])
        self.right_panel.set_export_readiness(result.ready, text)

    def _on_export_readiness(self, ready: bool, text: str) -> None:
        self.right_panel.set_export_readiness(ready, text)

    def _on_export_changed(self) -> None:
        self._check_export_readiness()
        self.export_panel.refresh()

    def _on_chrome_llm_mode_changed(self, mode: str) -> None:
        self._apply_ai_adapter_mode(mode, source="chrome")

    def _on_ai_mode_changed(self, mode: str) -> None:
        self._apply_ai_adapter_mode(mode, source="review")

    def _apply_ai_adapter_mode(self, mode: str, *, source: str = "settings") -> None:
        if self._syncing_ai_adapter_mode:
            return
        self._syncing_ai_adapter_mode = True
        try:
            self.context.ai_service.set_adapter_mode(mode, self.context.settings.data_dir)
            self.settings_panel.sync_adapter_mode(mode)
            if source != "chrome" and self.chrome is not None:
                self.chrome.set_llm_mode(mode)
            if source != "review":
                self.review_panel.set_ai_mode(mode)
            if source == "chrome":
                self._notify_cloud_llm_setup_if_needed(mode)
            self.right_panel._update_ai_status()
        finally:
            self._syncing_ai_adapter_mode = False

    def _notify_cloud_llm_setup_if_needed(self, mode: str) -> None:
        settings = self.context.ai_service.ai_settings
        if mode == "openai" and (
            not settings.openai_api_key.strip() or not settings.openai_model.strip()
        ):
            QMessageBox.information(
                self,
                "ตั้งค่า OpenAI",
                "เลือกโหมด OpenAI แล้ว — ไปที่ Settings → AI "
                "แล้วกรอก API Key และ Model ก่อนใช้งาน",
            )
        elif mode == "gemini" and (
            not settings.gemini_api_key.strip() or not settings.gemini_model.strip()
        ):
            QMessageBox.information(
                self,
                "ตั้งค่า Gemini",
                "เลือกโหมด Gemini แล้ว — ไปที่ Settings → AI "
                "แล้วกรอก API Key และ Model ก่อนใช้งาน",
            )

    def _on_ai_settings_changed(self, mode: str) -> None:
        self._apply_ai_adapter_mode(mode, source="settings")

    def _on_ai_summary_ready(self, interaction_id: str, text: str) -> None:
        interaction = self.context.ai_service.get_interaction(interaction_id)
        status = interaction.review_status if interaction else "requires_review"
        self.right_panel.set_ai_output(text, interaction_id, status)
        self.review_panel.refresh()

    def _on_review_changed(self) -> None:
        self.review_panel.refresh()
        self.target_panel.refresh()
        self.right_panel.refresh_ranking()
        self._update_review_summary()

    def _on_wing_data_changed(self) -> None:
        panel = self.weaponeering_panel
        if panel._selected_target_id:
            panel.recalculate()
        elif self._active_scenario_id:
            panel.set_scenario(self._active_scenario_id)

    def _on_detection_run_requested(
        self,
        radius_m: int,
        zoom_level: int,
        coordinate_id: str,
    ) -> None:
        model_name = _BUILDING_DETECTOR_MODEL
        target_id = (
            self.weaponeering_panel._selected_target_id or self._selected_map_target_id
        )
        if not target_id:
            self.statusBar().showMessage(
                "เลือก Target บนแผนที่หรือ Target Stack ก่อน Run Detection"
            )
            return
        if coordinate_id.startswith("draft-"):
            QMessageBox.warning(
                self,
                "YOLO Detection",
                "บันทึกพิกัดใน Target Stack ก่อน Run Detection ต่อพิกัดนี้",
            )
            return
        target = self._marker_for_coordinate(target_id, coordinate_id)
        if target is None:
            coordinates = self.target_panel.get_detection_coordinates(target_id)
            coord = next(
                (item for item in coordinates if str(item.get("id")) == coordinate_id),
                None,
            )
            if coord is None:
                self.statusBar().showMessage("ไม่พบพิกัดที่เลือกสำหรับ Run Detection")
                return
            target = self._build_detection_target_payload(target_id, coord)
        capture_radius_m = detection_capture_radius_m(radius_m, zoom_level)
        self._pending_detection_request = (
            target,
            model_name,
            radius_m,
            capture_radius_m,
        )
        self._show_workspace_tab("map")
        self.map_widget.fit_to_detection_area(
            float(target["lat"]),
            float(target["lng"]),
            capture_radius_m,
        )
        self.statusBar().showMessage(
            f"Preparing map crop around {target.get('label', 'Target')} "
            f"within {radius_m} m · zoom {zoom_level} "
            f"(view {capture_radius_m} m)..."
        )
        self.map_widget.set_detection_capture_mode(True)
        self._detection_ready_timer.start(3200 + zoom_level * 350)

    def _on_detection_viewport_ready(self) -> None:
        self._detection_ready_timer.stop()
        if self._pending_detection_request is None:
            return
        target, model_name, radius_m, capture_radius_m = self._pending_detection_request
        self._pending_detection_request = None
        QTimer.singleShot(
            250,
            lambda: self._run_detection_after_viewport_capture(
                target,
                model_name,
                radius_m,
                capture_radius_m,
            ),
        )

    def _run_detection_after_viewport_capture(
        self,
        target: dict,
        model_name: str,
        radius_m: int,
        capture_radius_m: int,
    ) -> None:
        try:
            self._run_detection_after_viewport_capture_impl(
                target, model_name, radius_m, capture_radius_m
            )
        except Exception:
            logger.exception("Run Detection failed")
            self.map_widget.set_detection_capture_mode(False)
            self.map_widget.restore_map_layers_after_detection()
            self.statusBar().showMessage("Run Detection failed - see logs for details")
            QMessageBox.critical(
                self,
                "YOLO Detection",
                "Run Detection encountered an unexpected error and was aborted.\n"
                "See the application logs for details.",
            )

    def _run_detection_after_viewport_capture_impl(
        self,
        target: dict,
        model_name: str,
        radius_m: int,
        capture_radius_m: int,
    ) -> None:
        try:
            source_path = self._capture_detection_source(target)
        finally:
            self.map_widget.set_detection_capture_mode(False)
        if source_path is None:
            self.map_widget.restore_map_layers_after_detection()
            QMessageBox.warning(
                self,
                "YOLO Detection",
                "Cannot capture the current map viewport for detection.",
            )
            return
        result = self._run_detection_subprocess(
            target=target,
            model_name=model_name,
            radius_m=radius_m,
            capture_radius_m=capture_radius_m,
        )
        target_id = str(target.get("targetCardId") or "")
        coordinate_id = str(target.get("coordinateId") or "")
        if result.ok and target_id and coordinate_id and self._active_scenario_id:
            try:
                self.context.target_detection_service.save_detection_run(
                    scenario_id=self._active_scenario_id,
                    target_card_id=target_id,
                    target_coordinate_id=coordinate_id,
                    model_name=model_name,
                    model_file_name=(
                        result.model_path.name if result.model_path else None
                    ),
                    radius_m=radius_m,
                    capture_radius_m=capture_radius_m,
                    source_image_name=(
                        result.source_path.name if result.source_path else None
                    ),
                    detection_message=result.message,
                    objects=result.objects,
                )
            except ValueError as exc:
                self.map_widget.restore_map_layers_after_detection()
                QMessageBox.warning(self, "YOLO Detection", str(exc))
                return
        self._refresh_map_layers()
        self.map_detail_sidebar.refresh_targets()
        self.map_widget.restore_map_layers_after_detection()
        if self._detection_edit_state is not None:
            self._sync_detection_editor_ui()
        if target_id:
            self.map_workspace.clear_ingress_corridor_focus()
            self._clear_corridor_route_edit_state()
            self._corridor_flight_summary = None
            self.map_widget.highlight_ingress_corridor(target_id, None, 0, None)
            self.map_widget.highlight_target(target_id)
            if target_id == self._selected_map_target_id:
                detail = self.context.target_service.get_target_detail(target_id)
                marker = self._primary_marker_for_target(target_id)
                if detail is not None:
                    self.map_detail_sidebar.show_target(detail, marker)
                    self._refresh_target_output_panel(target_id)
                    coordinates = self.target_panel.get_detection_coordinates(target_id)
                    self.map_workspace.set_detection_coordinates(coordinates)
        saved_note = ""
        if result.ok and target_id and self._active_scenario_id:
            count = len(result.objects)
            saved_note = f" · บันทึก {count} อาคารลงฐานข้อมูลแล้ว"
        self.statusBar().showMessage(result.message + saved_note)
        if not result.ok:
            QMessageBox.information(
                self,
                "YOLO Detection",
                result.message
                + "\n\n"
                + "Required setup:\n"
                + '1. Install: pip install -e ".[detection]"\n'
                + "2. Put your trained model at:\n"
                + f"   {_PROJECT_ROOT / 'building-seg.pt'}\n"
                + "3. Source image is auto-captured from the current map viewport.\n\n"
                + self.detection_service.describe_setup(model_name),
            )
            return
        if not result.objects:
            QMessageBox.information(
                self,
                "YOLO Detection",
                result.message
                + "\n\n"
                + "Tips:\n"
                + "- Increase the radius selector (recommended 120-250 m)\n"
                + "- Ensure the Target is linked to the map with satellite tiles loaded\n"
                + "- Wait for the map to finish zooming before the next Run Detection\n"
                + f"- Fine-tune {BUILDING_MODEL_FILENAME} for satellite imagery using scripts/train_yolo_model.py",
            )

    def _run_detection_subprocess(
        self,
        *,
        target: dict,
        model_name: str,
        radius_m: int,
        capture_radius_m: int,
    ) -> DetectionRunResult:
        request = {
            "data_dir": str(self.context.settings.data_dir),
            "project_root": str(_PROJECT_ROOT),
            "target": target,
            "model_name": model_name,
            "radius_m": radius_m,
            "capture_radius_m": capture_radius_m,
        }
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "maap_app.modules.detection.worker"],
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=300,
            )
        except (OSError, subprocess.TimeoutExpired):
            logger.exception("Failed to run detection worker process")
            return DetectionRunResult(
                message="Failed to launch the detection worker process."
            )
        if proc.returncode != 0 or not proc.stdout.strip():
            logger.error(
                "Detection worker exited with code %s: %s",
                proc.returncode,
                proc.stderr.strip(),
            )
            return DetectionRunResult(
                message="Detection worker process failed unexpectedly."
                + (f"\n{proc.stderr.strip()}" if proc.stderr.strip() else "")
            )
        payload = json.loads(proc.stdout)
        return DetectionRunResult(
            objects=payload["objects"],
            message=payload["message"],
            model_path=pathlib.Path(payload["model_path"]) if payload["model_path"] else None,
            source_path=pathlib.Path(payload["source_path"]) if payload["source_path"] else None,
            ok=payload["ok"],
        )

    def _capture_detection_source(self, target: dict) -> pathlib.Path | None:
        pixmap = self.map_widget.grab()
        if pixmap.isNull():
            return None
        width = pixmap.width()
        height = pixmap.height()
        side = min(width, height)
        if side <= 0:
            return None
        left = max((width - side) // 2, 0)
        top = max((height - side) // 2, 0)
        crop = pixmap.copy(left, top, side, side)
        source_dir = self.context.settings.data_dir / "detection_sources"
        source_dir.mkdir(parents=True, exist_ok=True)
        target_id = str(target.get("targetCardId") or "default")
        destination = source_dir / f"{target_id}.png"
        if not crop.save(str(destination), "PNG"):
            return None
        return destination

    def _markers_for_target(self, target_id: str) -> list[dict]:
        return [
            item
            for item in self._last_map_targets
            if item.get("targetCardId") == target_id
        ]

    def _primary_marker_for_target(self, target_id: str) -> dict | None:
        markers = self._markers_for_target(target_id)
        if not markers:
            return None
        return next(
            (item for item in markers if item.get("isPrimary")),
            markers[0],
        )

    def _marker_for_coordinate(
        self,
        target_id: str,
        coordinate_id: str,
    ) -> dict | None:
        for marker in self._markers_for_target(target_id):
            if marker.get("coordinateId") == coordinate_id:
                return marker
        return None

    @staticmethod
    def _build_detection_target_payload(
        target_id: str,
        coord: dict[str, object],
    ) -> dict:
        label = str(coord.get("label") or "P1")
        return {
            "targetCardId": target_id,
            "coordinateId": str(coord.get("id") or ""),
            "label": label,
            "lat": float(coord.get("lat") or 0.0),
            "lng": float(coord.get("lng") or 0.0),
            "isPrimary": bool(coord.get("isPrimary")),
        }

    def _on_ranking_completed(self) -> None:
        self.right_panel.refresh_ranking()
        self._check_export_readiness()
        self.statusBar().showMessage("Priority ranking run completed.")

    def _on_logistics_calculated(self) -> None:
        if not self._active_scenario_id:
            return
        score = self.context.logistics_service.get_latest_plan_score(self._active_scenario_id)
        if score:
            self.right_panel.set_logistics_result(
                score.logistics_feasibility,
                score.rationale,
                [],
            )

    def _on_map_ready(self) -> None:
        self.map_workspace.apply_map_settings(
            stadia_api_key=self._map_settings.stadia_api_key,
            prefer_stadia=bool(self._map_settings.stadia_api_key.strip()),
        )
        self.map_workspace.set_terrain_enabled(self._map_settings.terrain_enabled)
        self.map_widget.fit_to_scenario()
        self._refresh_map_layers()

    def _on_map_settings_changed(self, map_settings: MapSettings) -> None:
        self._map_settings = map_settings
        current = self.map_workspace.current_basemap_id()
        self.map_workspace.apply_map_settings(
            stadia_api_key=map_settings.stadia_api_key,
            prefer_stadia=False,
        )
        if map_settings.stadia_api_key.strip() and current in {
            "stadia_satellite",
            "stadia_smooth_dark",
        }:
            self.map_widget.set_basemap(current)
