from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QGuiApplication, QResizeEvent, QShowEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.target.models import TargetCardDetail
from maap_app.ui.components.map_ai_route_planner_panel import MapAiRoutePlannerPanel
from maap_app.ui.components.map_target_detail_overlay import MapTargetDetailOverlay
from maap_app.ui.map.map_widget import MapWidget


class _MapContainer(QWidget):
    """Hosts the map with floating toolbar and target detail overlays."""

    def __init__(
        self,
        map_widget: MapWidget,
        toolbar: QWidget,
        detail_overlay: MapTargetDetailOverlay,
        ai_planner: MapAiRoutePlannerPanel,
    ) -> None:
        super().__init__()
        self.setObjectName("MapContainer")
        self._map_widget = map_widget
        self._toolbar = toolbar
        self._detail_overlay = detail_overlay
        self._ai_planner = ai_planner

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(map_widget)

        toolbar.setParent(self)
        detail_overlay.setParent(self)
        ai_planner.setParent(self)
        toolbar.raise_()
        detail_overlay.raise_()
        ai_planner.raise_()

    def _position_overlays(self) -> None:
        if self._ai_planner.isVisible():
            self._ai_planner.position_in_container(self.width(), self.height())
            self._ai_planner.raise_()
        if self._detail_overlay.isVisible():
            self._detail_overlay.position_in_container(self.width(), self.height())
            self._detail_overlay.raise_()

    def resizeEvent(self, event: QResizeEvent) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._toolbar.adjustSize()
        x = max(12, (self.width() - self._toolbar.width()) // 2)
        self._toolbar.move(x, 10)
        self._toolbar.raise_()
        self._position_overlays()


class MapWorkspace(QWidget):
    layer_visibility_changed = Signal(dict)
    detail_visibility_changed = Signal(bool)
    detection_run_requested = Signal(int, int, str)
    open_in_target_stack = Signal(str)
    ingress_corridor_view_requested = Signal(str, object, int)
    flight_route_approve_requested = Signal()
    flight_route_delete_waypoint_requested = Signal()
    flight_route_waypoint_label_changed = Signal(str)
    flight_route_waypoint_altitude_changed = Signal(int)
    flight_route_waypoints_visibility_changed = Signal(bool)
    flight_route_waypoint_labels_visibility_changed = Signal(bool)
    detection_editor_requested = Signal()
    detection_add_mode_toggled = Signal(bool)
    detection_delete_requested = Signal()
    detection_object_selected = Signal(str)
    detection_delete_object_requested = Signal(str)
    detection_risk_level_changed = Signal(str)
    detection_editor_closed = Signal()
    coordinate_product_changed = Signal(str, object)
    ai_route_plan_requested = Signal()
    ai_route_apply_requested = Signal()
    ai_route_clear_requested = Signal()
    ai_route_use_plan_endpoints_requested = Signal()
    ai_route_takeoff_pick_toggled = Signal(bool)
    ai_route_landing_pick_toggled = Signal(bool)
    terrain_enabled_changed = Signal(bool)

    def __init__(self, map_widget: MapWidget) -> None:
        super().__init__()
        self.setObjectName("MapWorkspace")
        self.map_widget = map_widget
        self._detail_syncing = False
        self._detail_visible = True
        self._has_target_detail = False
        self._last_distance_m = 0.0
        self._last_radius_m = 0.0
        self._last_picked_lat: float | None = None
        self._last_picked_lng: float | None = None
        self._stadia_api_key = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("MapWorkspaceHeader")
        header.setFixedHeight(36)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        title = QLabel("Cesium Map")
        title.setObjectName("MapWorkspaceTitle")
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        layout.addWidget(header)

        self._floating_toolbar = self._build_floating_toolbar()
        self._target_detail_overlay = MapTargetDetailOverlay()
        self._ai_route_planner = MapAiRoutePlannerPanel()
        self._target_detail_overlay.closed.connect(self._on_target_detail_closed)
        self._target_detail_overlay.open_in_target_stack.connect(
            self.open_in_target_stack.emit
        )
        self._target_detail_overlay.ingress_corridor_view_requested.connect(
            self.ingress_corridor_view_requested.emit
        )
        self._target_detail_overlay.flight_route_approve_requested.connect(
            self.flight_route_approve_requested.emit
        )
        self._target_detail_overlay.flight_route_delete_waypoint_requested.connect(
            self.flight_route_delete_waypoint_requested.emit
        )
        self._target_detail_overlay.flight_route_waypoint_label_changed.connect(
            self.flight_route_waypoint_label_changed.emit
        )
        self._target_detail_overlay.flight_route_waypoint_altitude_changed.connect(
            self.flight_route_waypoint_altitude_changed.emit
        )
        self._target_detail_overlay.flight_route_add_mode_toggled.connect(
            self._on_route_add_mode_toggled
        )
        self._target_detail_overlay.flight_route_waypoints_visibility_changed.connect(
            self.flight_route_waypoints_visibility_changed.emit
        )
        self._target_detail_overlay.flight_route_waypoint_labels_visibility_changed.connect(
            self.flight_route_waypoint_labels_visibility_changed.emit
        )
        self._target_detail_overlay.flight_route_editor_closed.connect(
            self.hide_flight_route_editor
        )
        self._target_detail_overlay.detection_editor_requested.connect(
            self.detection_editor_requested.emit
        )
        self._target_detail_overlay.detection_add_mode_toggled.connect(
            self._on_detection_add_mode_toggled
        )
        self._target_detail_overlay.detection_delete_requested.connect(
            self.detection_delete_requested.emit
        )
        self._target_detail_overlay.detection_object_selected.connect(
            self.detection_object_selected.emit
        )
        self._target_detail_overlay.detection_delete_object_requested.connect(
            self.detection_delete_object_requested.emit
        )
        self._target_detail_overlay.detection_risk_level_changed.connect(
            self.detection_risk_level_changed.emit
        )
        self._target_detail_overlay.detection_editor_closed.connect(
            self.hide_detection_editor
        )
        self._target_detail_overlay.coordinate_product_changed.connect(
            self.coordinate_product_changed.emit
        )
        self._ai_route_planner.closed.connect(self.hide_ai_route_planner)
        self._ai_route_planner.plan_requested.connect(self.ai_route_plan_requested.emit)
        self._ai_route_planner.apply_requested.connect(self.ai_route_apply_requested.emit)
        self._ai_route_planner.clear_requested.connect(self.ai_route_clear_requested.emit)
        self._ai_route_planner.use_plan_endpoints_requested.connect(
            self.ai_route_use_plan_endpoints_requested.emit
        )
        self._ai_route_planner.takeoff_pick_toggled.connect(
            self.ai_route_takeoff_pick_toggled.emit
        )
        self._ai_route_planner.landing_pick_toggled.connect(
            self.ai_route_landing_pick_toggled.emit
        )
        self._map_container = _MapContainer(
            map_widget,
            self._floating_toolbar,
            self._target_detail_overlay,
            self._ai_route_planner,
        )
        layout.addWidget(self._map_container, stretch=1)

        self.map_widget.measure_updated.connect(self._on_measure_updated)
        self.map_widget.measure_radius_updated.connect(self._on_measure_radius_updated)
        self.map_widget.coordinate_picked.connect(self._on_coordinate_picked)

    def _build_floating_toolbar(self) -> QWidget:
        toolbar = QWidget()
        toolbar.setObjectName("MapFloatingToolbar")

        row = QHBoxLayout(toolbar)
        row.setContentsMargins(10, 6, 10, 6)
        row.setSpacing(8)

        row.addWidget(self._build_layers_button())
        row.addWidget(self._make_divider())
        row.addWidget(self._build_labeled_control("Basemap", self._build_basemap_combo()))
        row.addWidget(self._make_divider())
        row.addWidget(self._build_labeled_control("Point", self._build_point_combo()))
        row.addWidget(self._make_divider())
        row.addWidget(self._build_labeled_control("Radius", self._build_radius_spin()))
        row.addWidget(self._make_divider())
        row.addWidget(self._build_labeled_control("Zoom", self._build_zoom_spin()))
        row.addWidget(self._make_divider())
        row.addWidget(self._build_run_detection_button())
        row.addWidget(self._make_divider())
        row.addWidget(self._build_ai_route_button())
        row.addWidget(self._make_divider())
        row.addWidget(self._build_measure_button())
        row.addWidget(self._make_divider())
        row.addWidget(self._build_pick_coord_button())
        row.addWidget(self._make_divider())
        row.addWidget(self._build_clear_button())

        return toolbar

    def _build_layers_button(self) -> QToolButton:
        button = QToolButton()
        button.setObjectName("MapToolbarButton")
        button.setText("Layers")
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        menu = QMenu(button)
        menu.setObjectName("MapToolbarMenu")
        self._layer_actions: dict[str, QAction] = {}
        layer_items = (
            ("organizations", "Org", True, "หน่วย/กองบินบนแผนที่"),
            ("depots", "Depot", True, "คลังเสบียว"),
            ("routes", "Logistics", True, "เส้นเสบียว/โลจิสติกส์"),
            ("ground_transport", "ขนส่ง", True, "เส้นทางขนสินค้าระหว่างกองบิน"),
            ("detections", "Detection", True, "ผลตรวจจับ YOLO"),
            ("teams", "Blue/Red", True, "หน่วยฝ่ายเราและฝ่ายตรงข้าม"),
            ("borders", "Borders", True, "เส้นแบ่งเขตประเทศไทย"),
        )
        for key, label, checked, tooltip in layer_items:
            action = QAction(label, menu)
            action.setCheckable(True)
            action.setChecked(checked)
            action.setToolTip(tooltip)
            action.toggled.connect(self._emit_layer_visibility)
            menu.addAction(action)
            self._layer_actions[key] = action

        menu.addSeparator()
        self._terrain_action = QAction("Terrain 3D", menu)
        self._terrain_action.setCheckable(True)
        self._terrain_action.setChecked(True)
        self._terrain_action.setToolTip("เปิด/ปิด Terrain ความสูงภูมิประเทศ 3D")
        self._terrain_action.toggled.connect(self._on_terrain_toggled)
        menu.addAction(self._terrain_action)

        self._detail_action = QAction("Detail", menu)
        self._detail_action.setCheckable(True)
        self._detail_action.setChecked(True)
        self._detail_action.setToolTip("แสดง/ซ่อนการ์ดรายละเอียด Target ด้านขวาบนแผนที่")
        self._detail_action.toggled.connect(self._on_detail_action_toggled)
        menu.addAction(self._detail_action)

        button.setMenu(menu)
        return button

    def _build_basemap_combo(self) -> QComboBox:
        self.basemap_combo = QComboBox()
        self.basemap_combo.setObjectName("MapToolbarCombo")
        self.basemap_combo.setMinimumWidth(168)
        self.basemap_combo.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )
        self.basemap_combo.setToolTip("เลือกชั้นภาพพื้นหลังแผนที่")
        basemap_items = (
            ("stadia_satellite", "Stadia Satellite"),
            ("stadia_smooth_dark", "Stadia Smooth Dark"),
            ("open_topo_map", "OpenTopoMap"),
            ("esri_world_imagery", "Esri World Imagery"),
            ("cesium", "Cesium / ดาวเทียม"),
            ("rtaf_50k", "RTAF 1:50K"),
            ("rtaf_250k", "RTAF 1:250K"),
            ("rtaf_500k", "RTAF 1:500K"),
        )
        for basemap_id, label in basemap_items:
            self.basemap_combo.addItem(label, basemap_id)
        self.basemap_combo.currentIndexChanged.connect(self._on_basemap_changed)
        return self.basemap_combo

    def _on_basemap_changed(self, index: int) -> None:
        if index < 0:
            return
        basemap_id = self.basemap_combo.itemData(index)
        if not basemap_id:
            return
        basemap_id = str(basemap_id)
        if basemap_id in {"stadia_satellite", "stadia_smooth_dark"} and not self._stadia_api_key:
            QMessageBox.information(
                self,
                "Stadia Maps API Key",
                "Stadia Maps ต้องใช้ API Key ฟรีจาก stadiamaps.com\n\n"
                "ไปที่ Settings → แท็บ Map แล้วใส่ Stadia API Key ก่อนใช้งาน",
            )
            self.set_basemap_selection("cesium")
            self.map_widget.set_basemap("cesium")
            return
        self.map_widget.set_basemap(basemap_id)

    def set_stadia_api_key(self, api_key: str) -> None:
        self._stadia_api_key = api_key.strip()
        self.map_widget.set_stadia_api_key(self._stadia_api_key)

    def set_basemap_selection(self, basemap_id: str) -> None:
        self.basemap_combo.blockSignals(True)
        index = self.basemap_combo.findData(basemap_id)
        if index >= 0:
            self.basemap_combo.setCurrentIndex(index)
        self.basemap_combo.blockSignals(False)

    def current_basemap_id(self) -> str:
        index = self.basemap_combo.currentIndex()
        if index < 0:
            return "cesium"
        value = self.basemap_combo.itemData(index)
        return str(value) if value else "cesium"

    def apply_map_settings(self, *, stadia_api_key: str, prefer_stadia: bool = True) -> None:
        self.set_stadia_api_key(stadia_api_key)
        if stadia_api_key.strip() and prefer_stadia:
            target = "stadia_satellite"
        elif self.current_basemap_id() in {"stadia_satellite", "stadia_smooth_dark"}:
            target = "cesium"
        else:
            target = self.current_basemap_id()
        self.set_basemap_selection(target)
        self.map_widget.set_basemap(target)

    def set_terrain_enabled(self, enabled: bool) -> None:
        self._terrain_action.blockSignals(True)
        self._terrain_action.setChecked(enabled)
        self._terrain_action.blockSignals(False)
        self.map_widget.set_terrain_enabled(enabled)

    @property
    def ai_route_planner(self) -> MapAiRoutePlannerPanel:
        return self._ai_route_planner

    def show_ai_route_planner(self) -> None:
        self._ai_route_planner.setVisible(True)
        self._map_container._position_overlays()
        self.ai_route_use_plan_endpoints_requested.emit()

    def hide_ai_route_planner(self) -> None:
        self._ai_route_planner.setVisible(False)
        self._ai_route_planner.clear_pick_modes()
        self.map_widget.set_route_pick_mode(None)
        self._map_container._position_overlays()

    def _build_point_combo(self) -> QComboBox:
        self.detection_coordinate = QComboBox()
        self.detection_coordinate.setObjectName("MapToolbarCombo")
        self.detection_coordinate.setMinimumWidth(108)
        self.detection_coordinate.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )
        self.detection_coordinate.setToolTip("เลือกพิกัดเป้าหมายสำหรับ Run Detection")
        return self.detection_coordinate

    def _build_radius_spin(self) -> QSpinBox:
        self.detection_radius = QSpinBox()
        self.detection_radius.setObjectName("MapToolbarSpin")
        self.detection_radius.setRange(20, 300)
        self.detection_radius.setSingleStep(10)
        self.detection_radius.setValue(120)
        self.detection_radius.setSuffix(" m")
        self.detection_radius.setToolTip("รัศมีกรองวัตถุรอบพิกัดเป้าหมาย")
        return self.detection_radius

    def _build_zoom_spin(self) -> QSpinBox:
        self.detection_zoom = QSpinBox()
        self.detection_zoom.setObjectName("MapToolbarSpin")
        self.detection_zoom.setRange(1, 4)
        self.detection_zoom.setValue(4)
        self.detection_zoom.setToolTip(
            "ซูมภาพตรวจจับ — ค่าสูง = ใกล้ขึ้น (รัศมีเป้าหมายคงเดิม)"
        )
        return self.detection_zoom

    def _build_run_detection_button(self) -> QPushButton:
        button = QPushButton("Run Detection")
        button.setObjectName("MapToolbarAccentButton")
        button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        button.clicked.connect(self._emit_detection_run)
        return button

    def _build_ai_route_button(self) -> QPushButton:
        button = QPushButton("AI Route")
        button.setObjectName("MapToolbarButton")
        button.setToolTip("เปิด AI Route Planner · วางเส้นทาง Takeoff → Target → Landing")
        button.clicked.connect(self.show_ai_route_planner)
        return button

    def _on_terrain_toggled(self, checked: bool) -> None:
        self.map_widget.set_terrain_enabled(checked)
        self.terrain_enabled_changed.emit(checked)

    def _build_measure_button(self) -> QWidget:
        host = QWidget()
        host_layout = QHBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(6)

        self.measure_btn = QToolButton()
        self.measure_btn.setObjectName("MapToolbarButton")
        self.measure_btn.setText("Measure")
        self.measure_btn.setCheckable(True)
        self.measure_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.measure_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon))
        self.measure_btn.setToolTip("วัดระยะ/รัศมีบนแผนที่ — เลือกโหมดแล้วคลิกบนแผนที่")
        self.measure_btn.toggled.connect(self._on_measure_toggled)
        host_layout.addWidget(self.measure_btn)

        self.measure_type = QComboBox()
        self.measure_type.setObjectName("MapToolbarCombo")
        self.measure_type.addItem("ระยะทาง", "distance")
        self.measure_type.addItem("รัศมี", "radius")
        self.measure_type.setToolTip("ระยะทาง = วัดหลายจุด · รัศมี = วงจากจุดศูนย์กลาง")
        self.measure_type.currentIndexChanged.connect(self._on_measure_type_changed)
        host_layout.addWidget(self.measure_type)
        return host

    def _build_pick_coord_button(self) -> QWidget:
        host = QWidget()
        host_layout = QHBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(6)

        self.pick_coord_btn = QToolButton()
        self.pick_coord_btn.setObjectName("MapToolbarButton")
        self.pick_coord_btn.setText("พิกัด")
        self.pick_coord_btn.setCheckable(True)
        self.pick_coord_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.pick_coord_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        )
        self.pick_coord_btn.setToolTip("คลิกบนแผนที่เพื่อรับพิกัด Lat, Lng")
        self.pick_coord_btn.toggled.connect(self._on_pick_coord_toggled)
        host_layout.addWidget(self.pick_coord_btn)

        self.pick_coord_label = QLabel("Lat —, Lng —")
        self.pick_coord_label.setObjectName("MapToolbarLabel")
        self.pick_coord_label.setToolTip("พิกัดล่าสุดจากการคลิกบนแผนที่")
        host_layout.addWidget(self.pick_coord_label)

        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("MapToolbarButton")
        copy_btn.setToolTip("คัดลอกพิกัดล่าสุด")
        copy_btn.clicked.connect(self._copy_picked_coordinate)
        host_layout.addWidget(copy_btn)
        return host

    def show_flight_route_editor(
        self,
        *,
        target_label: str,
        wing_name: str,
        waypoint_count: int,
        distance_label: str,
        dirty: bool,
    ) -> None:
        if self._has_target_detail:
            self._target_detail_overlay.setVisible(True)
        self._target_detail_overlay.show_flight_route_editor(
            target_label=target_label,
            wing_name=wing_name,
        )
        self._target_detail_overlay.update_flight_route_editor(
            waypoint_count=waypoint_count,
            distance_label=distance_label,
            dirty=dirty,
        )
        self._map_container.resizeEvent(
            QResizeEvent(self._map_container.size(), self._map_container.size())
        )

    def hide_flight_route_editor(self) -> None:
        self._target_detail_overlay.hide_flight_route_editor()
        self._on_route_add_mode_toggled(False)
        self._map_container.resizeEvent(
            QResizeEvent(self._map_container.size(), self._map_container.size())
        )

    def update_flight_route_editor(
        self,
        *,
        waypoint_count: int,
        distance_label: str,
        dirty: bool,
        selected_label: str | None = None,
        selected_waypoint_id: str | None = None,
        selected_altitude_ft: int | None = None,
        show_waypoints: bool = True,
        show_waypoint_labels: bool = False,
    ) -> None:
        self._target_detail_overlay.update_flight_route_editor(
            waypoint_count=waypoint_count,
            distance_label=distance_label,
            dirty=dirty,
            selected_label=selected_label,
            selected_waypoint_id=selected_waypoint_id,
            selected_altitude_ft=selected_altitude_ft,
            show_waypoints=show_waypoints,
            show_waypoint_labels=show_waypoint_labels,
        )

    def hide_detection_editor(self) -> None:
        self._target_detail_overlay.hide_detection_editor()
        self._on_detection_add_mode_toggled(False)
        self.map_widget.set_detection_edit_mode(False)
        self._map_container.resizeEvent(
            QResizeEvent(self._map_container.size(), self._map_container.size())
        )

    def show_detection_editor(
        self,
        *,
        target_label: str,
        coordinate_label: str,
    ) -> None:
        self._target_detail_overlay.show_detection_editor(
            target_label=target_label,
            coordinate_label=coordinate_label,
        )
        self.map_widget.set_detection_edit_mode(True)
        self._map_container.resizeEvent(
            QResizeEvent(self._map_container.size(), self._map_container.size())
        )

    def update_detection_editor(
        self,
        *,
        object_count: int,
        objects: list[dict[str, Any]] | None = None,
        selected_label: str | None = None,
        selected_risk: str | None = None,
        selected_object_id: str | None = None,
    ) -> None:
        self._target_detail_overlay.update_detection_editor(
            object_count=object_count,
            objects=objects,
            selected_label=selected_label,
            selected_risk=selected_risk,
            selected_object_id=selected_object_id,
        )

    def _on_detection_add_mode_toggled(self, checked: bool) -> None:
        if checked:
            self.measure_btn.setChecked(False)
            self.pick_coord_btn.setChecked(False)
            self.map_widget.enable_link_mode(False)
            self.map_widget.set_pick_coord_mode(False)
            self.map_widget.set_detection_edit_mode(True)
        self.map_widget.set_detection_add_mode(checked)
        if checked:
            self.focus_map_for_interaction()

    def set_detection_add_mode(self, checked: bool) -> None:
        editor = self._target_detail_overlay.detection_editor
        editor.add_btn.blockSignals(True)
        editor.add_btn.setChecked(checked)
        editor.add_btn.blockSignals(False)
        self._on_detection_add_mode_toggled(checked)

    def focus_map_for_interaction(self) -> None:
        """Give the map keyboard focus without covering the floating overlay controls."""
        self._map_container._map_widget.setFocus()
        self._map_container._toolbar.raise_()
        self._map_container._position_overlays()

    def _on_route_add_mode_toggled(self, checked: bool) -> None:
        if checked:
            self.measure_btn.setChecked(False)
            self.pick_coord_btn.setChecked(False)
            self.map_widget.enable_link_mode(False)
            self.map_widget.set_pick_coord_mode(False)
            self.map_widget.set_flight_route_edit_mode(True)
        self.map_widget.set_route_add_mode(checked)
        if checked:
            self.focus_map_for_interaction()

    def _build_clear_button(self) -> QToolButton:
        button = QToolButton()
        button.setObjectName("MapToolbarButton")
        button.setText("Clear")
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        button.setToolTip("ล้างเส้นวัดระยะและจุดพิกัดบนแผนที่")
        button.clicked.connect(self._clear_measurements)
        return button

    @staticmethod
    def _make_divider() -> QFrame:
        divider = QFrame()
        divider.setObjectName("MapToolbarDivider")
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Plain)
        divider.setFixedWidth(1)
        divider.setFixedHeight(22)
        return divider

    @staticmethod
    def _build_labeled_control(label: str, control: QWidget) -> QWidget:
        host = QWidget()
        layout = QHBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        title = QLabel(label)
        title.setObjectName("MapToolbarLabel")
        layout.addWidget(title)
        layout.addWidget(control)
        return host

    def showEvent(self, event: QShowEvent) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.reposition_overlays()

    def _emit_layer_visibility(self) -> None:
        layers = {
            key: action.isChecked()
            for key, action in self._layer_actions.items()
        }
        self.map_widget.set_layer_visibility(layers)
        self.layer_visibility_changed.emit(layers)

    def _emit_detection_run(self) -> None:
        coordinate_id = str(self.detection_coordinate.currentData() or "")
        if not coordinate_id:
            QMessageBox.warning(
                self,
                "YOLO Detection",
                "ยังไม่มีพิกัดสำหรับ Run Detection\n\n"
                "เลือก Target บนแผนที่หรือ Target Stack ก่อน "
                "แล้วตรวจสอบว่ามีพิกัดในช่องเลือกพิกัด",
            )
            return
        detections = self._layer_actions.get("detections")
        if detections is not None:
            detections.setChecked(True)
        self.detection_run_requested.emit(
            self.detection_radius.value(),
            self.detection_zoom.value(),
            coordinate_id,
        )

    def set_detection_coordinates(
        self,
        coordinates: list[dict[str, object]],
    ) -> None:
        self.detection_coordinate.blockSignals(True)
        self.detection_coordinate.clear()
        for index, coord in enumerate(coordinates):
            coord_id = str(coord.get("id") or f"coord-{index}")
            label = str(coord.get("label") or f"P{index + 1}")
            lat = float(coord.get("lat") or 0.0)
            lng = float(coord.get("lng") or 0.0)
            primary_suffix = " · หลัก" if coord.get("isPrimary") else ""
            self.detection_coordinate.addItem(
                f"{label}{primary_suffix}",
                coord_id,
            )
            item_index = self.detection_coordinate.count() - 1
            self.detection_coordinate.setItemData(
                item_index,
                f"{label} — {lat:.5f}, {lng:.5f}{primary_suffix}",
                Qt.ItemDataRole.ToolTipRole,
            )
        if self.detection_coordinate.count():
            primary_index = next(
                (
                    index
                    for index in range(self.detection_coordinate.count())
                    if " · หลัก" in self.detection_coordinate.itemText(index)
                ),
                0,
            )
            self.detection_coordinate.setCurrentIndex(primary_index)
        self.detection_coordinate.blockSignals(False)

    def show_target_detail(
        self,
        detail: TargetCardDetail,
        markers: list[dict[str, object]] | dict[str, object] | None = None,
        *,
        corridor_flight_summary: str | None = None,
        weaponeering: dict[str, object] | None = None,
    ) -> None:
        self._has_target_detail = True
        self._detail_visible = True
        self.set_detail_toggle_checked(True)
        self._target_detail_overlay.show_target(
            detail,
            markers,
            corridor_flight_summary=corridor_flight_summary,
            weaponeering=weaponeering,
        )
        self._map_container._position_overlays()
        self._target_detail_overlay.raise_()

    def reposition_overlays(self) -> None:
        self._map_container.resizeEvent(
            QResizeEvent(self._map_container.size(), self._map_container.size())
        )

    def hide_target_detail(self) -> None:
        self._has_target_detail = False
        self._target_detail_overlay.clear()
        self._map_container._position_overlays()

    def clear_ingress_corridor_focus(self) -> None:
        self._target_detail_overlay.clear_ingress_focus()

    def set_target_detail_visible(self, visible: bool) -> None:
        self._detail_visible = visible
        if visible and self._has_target_detail:
            self._target_detail_overlay.setVisible(True)
            self._map_container._position_overlays()
            self._target_detail_overlay.raise_()
        else:
            self._target_detail_overlay.setVisible(False)

    def _on_detail_action_toggled(self, checked: bool) -> None:
        if self._detail_syncing:
            return
        self.set_target_detail_visible(checked)
        self.detail_visibility_changed.emit(checked)

    def _on_target_detail_closed(self) -> None:
        self._detail_visible = False
        self._detail_syncing = True
        try:
            self._detail_action.setChecked(False)
        finally:
            self._detail_syncing = False
        self._target_detail_overlay.setVisible(False)
        self.detail_visibility_changed.emit(False)

    def set_detail_toggle_checked(self, checked: bool) -> None:
        self._detail_syncing = True
        try:
            self._detail_action.setChecked(checked)
        finally:
            self._detail_syncing = False

    def _on_measure_toggled(self, checked: bool) -> None:
        if checked:
            self.pick_coord_btn.setChecked(False)
            self._target_detail_overlay.route_editor.add_point_btn.setChecked(False)
        self.map_widget.set_measure_mode(checked)
        if checked:
            self._on_measure_type_changed()

    def _on_pick_coord_toggled(self, checked: bool) -> None:
        if checked:
            self.measure_btn.setChecked(False)
            self._target_detail_overlay.route_editor.add_point_btn.setChecked(False)
        self.map_widget.set_pick_coord_mode(checked)

    def _on_coordinate_picked(self, lat: float, lng: float) -> None:
        self._last_picked_lat = lat
        self._last_picked_lng = lng
        self.pick_coord_label.setText(f"Lat {lat:.5f}, Lng {lng:.5f}")

    def _copy_picked_coordinate(self) -> None:
        if self._last_picked_lat is None or self._last_picked_lng is None:
            QMessageBox.information(
                self,
                "คัดลอกพิกัด",
                "ยังไม่มีพิกัด — เปิดโหมด「พิกัด」แล้วคลิกบนแผนที่ก่อน",
            )
            return
        text = f"{self._last_picked_lat:.5f}, {self._last_picked_lng:.5f}"
        QGuiApplication.clipboard().setText(text)

    def _on_measure_type_changed(self) -> None:
        tool_type = str(self.measure_type.currentData() or "distance")
        self.map_widget.set_measure_type(tool_type)

    def _clear_measurements(self) -> None:
        self.map_widget.clear_measurements()
        self.map_widget.clear_picked_coordinate()
        self._last_distance_m = 0.0
        self._last_radius_m = 0.0
        self._last_picked_lat = None
        self._last_picked_lng = None
        self.pick_coord_label.setText("Lat —, Lng —")

    def _on_measure_updated(self, distance_m: float) -> None:
        self._last_distance_m = max(distance_m, 0.0)

    def _on_measure_radius_updated(self, radius_m: float) -> None:
        self._last_radius_m = max(radius_m, 0.0)
