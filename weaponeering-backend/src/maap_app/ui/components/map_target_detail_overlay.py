from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.target.models import TargetCardDetail
from maap_app.ui.components.map_building_detection_editor_card import (
    MapBuildingDetectionEditorCard,
)
from maap_app.ui.components.map_flight_route_editor_card import MapFlightRouteEditorCard
from maap_app.ui.panels.map_target_detail_panel import MapTargetDetailPanel


class MapTargetDetailOverlay(QWidget):
    """Floating target detail card anchored to the top-right of the map."""

    closed = Signal()
    open_in_target_stack = Signal(str)
    ingress_corridor_view_requested = Signal(str, object, int)
    flight_route_approve_requested = Signal()
    flight_route_delete_waypoint_requested = Signal()
    flight_route_waypoint_label_changed = Signal(str)
    flight_route_waypoint_altitude_changed = Signal(int)
    flight_route_add_mode_toggled = Signal(bool)
    flight_route_waypoints_visibility_changed = Signal(bool)
    flight_route_waypoint_labels_visibility_changed = Signal(bool)
    flight_route_editor_closed = Signal()
    detection_editor_requested = Signal()
    detection_add_mode_toggled = Signal(bool)
    detection_delete_requested = Signal()
    detection_object_selected = Signal(str)
    detection_delete_object_requested = Signal(str)
    detection_risk_level_changed = Signal(str)
    detection_editor_closed = Signal()
    coordinate_product_changed = Signal(str, object)

    CARD_WIDTH = 300

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MapTargetDetailOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setVisible(False)

        shell = QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        header = QWidget()
        header.setObjectName("MapTargetDetailOverlayHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 8, 8)
        header_layout.setSpacing(6)
        self.title_label = QLabel("Target Detail")
        self.title_label.setObjectName("MapTargetDetailOverlayTitle")
        header_layout.addWidget(self.title_label, stretch=1)
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("MapTargetDetailCloseButton")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setToolTip("ปิดรายละเอียด Target")
        self.close_btn.clicked.connect(self.closed.emit)
        header_layout.addWidget(self.close_btn)
        shell.addWidget(header)

        self.detail_panel = MapTargetDetailPanel()
        self.detail_panel.setObjectName("MapTargetDetailOverlayBody")
        shell.addWidget(self.detail_panel, stretch=1)

        self.route_editor = MapFlightRouteEditorCard()
        shell.addWidget(self.route_editor)

        self.detection_editor = MapBuildingDetectionEditorCard()
        shell.addWidget(self.detection_editor)

        self.detail_panel.open_in_target_stack.connect(self.open_in_target_stack.emit)
        self.detail_panel.detection_editor_requested.connect(
            self.detection_editor_requested.emit
        )
        self.detail_panel.ingress_corridor_view_requested.connect(
            self.ingress_corridor_view_requested.emit
        )
        self.route_editor.approve_requested.connect(self.flight_route_approve_requested.emit)
        self.route_editor.delete_waypoint_requested.connect(
            self.flight_route_delete_waypoint_requested.emit
        )
        self.route_editor.waypoint_label_changed.connect(
            self.flight_route_waypoint_label_changed.emit
        )
        self.route_editor.waypoint_altitude_changed.connect(
            self.flight_route_waypoint_altitude_changed.emit
        )
        self.route_editor.add_mode_toggled.connect(self.flight_route_add_mode_toggled.emit)
        self.route_editor.waypoints_visibility_changed.connect(
            self.flight_route_waypoints_visibility_changed.emit
        )
        self.route_editor.waypoint_labels_visibility_changed.connect(
            self.flight_route_waypoint_labels_visibility_changed.emit
        )
        self.route_editor.closed.connect(self.flight_route_editor_closed.emit)
        self.detection_editor.closed.connect(self.detection_editor_closed.emit)
        self.detection_editor.add_mode_toggled.connect(
            self.detection_add_mode_toggled.emit
        )
        self.detection_editor.delete_requested.connect(
            self.detection_delete_requested.emit
        )
        self.detection_editor.object_selected.connect(
            self.detection_object_selected.emit
        )
        self.detection_editor.delete_object_requested.connect(
            self.detection_delete_object_requested.emit
        )
        self.detection_editor.risk_level_changed.connect(
            self.detection_risk_level_changed.emit
        )
        self.detail_panel.coordinate_product_changed.connect(
            self.coordinate_product_changed.emit
        )

    def show_target(
        self,
        detail: TargetCardDetail,
        markers: dict[str, Any] | list[dict[str, Any]] | None = None,
        *,
        corridor_flight_summary: str | None = None,
        weaponeering: dict[str, object] | None = None,
    ) -> None:
        self.title_label.setText(detail.card.label)
        self.detail_panel.show_target(
            detail,
            markers,
            corridor_flight_summary=corridor_flight_summary,
            weaponeering=weaponeering,
        )
        self.setVisible(True)
        self.raise_()

    def clear(self) -> None:
        self.title_label.setText("Target Detail")
        self.detail_panel.clear()
        self.route_editor.hide_editor()
        self.detection_editor.hide_editor()
        self.setVisible(False)

    def clear_ingress_focus(self) -> None:
        self.detail_panel.clear_ingress_focus()

    def show_flight_route_editor(self, *, target_label: str, wing_name: str) -> None:
        self.route_editor.show_editor(target_label=target_label, wing_name=wing_name)
        self._relayout()

    def hide_flight_route_editor(self) -> None:
        self.route_editor.hide_editor()
        self._relayout()

    def hide_detection_editor(self) -> None:
        self.detection_editor.hide_editor()
        self._relayout()

    def show_detection_editor(
        self,
        *,
        target_label: str,
        coordinate_label: str,
    ) -> None:
        self.detection_editor.show_editor(
            target_label=target_label,
            coordinate_label=coordinate_label,
        )
        self._relayout()

    def update_detection_editor(
        self,
        *,
        object_count: int,
        objects: list[dict[str, Any]] | None = None,
        selected_label: str | None = None,
        selected_risk: str | None = None,
        selected_object_id: str | None = None,
    ) -> None:
        self.detection_editor.update_state(
            object_count=object_count,
            objects=objects,
            selected_label=selected_label,
            selected_risk=selected_risk,
            selected_object_id=selected_object_id,
        )
        if self.detection_editor.isVisible():
            self._relayout()

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
        self.route_editor.update_state(
            waypoint_count=waypoint_count,
            distance_label=distance_label,
            dirty=dirty,
            selected_label=selected_label,
            selected_waypoint_id=selected_waypoint_id,
            selected_altitude_ft=selected_altitude_ft,
        )
        self.route_editor.set_waypoints_visible(show_waypoints)
        self.route_editor.set_waypoint_labels_visible(show_waypoint_labels)
        if self.route_editor.isVisible():
            self._relayout()

    def _relayout(self) -> None:
        parent = self.parentWidget()
        if parent is not None and self.isVisible():
            self.position_in_container(parent.width(), parent.height())

    def position_in_container(
        self,
        container_width: int,
        container_height: int,
    ) -> None:
        margin = 12
        top = 54
        max_height = max(container_height - top - margin, 200)
        self.setFixedWidth(self.CARD_WIDTH)
        self.setMaximumHeight(max_height)
        self.adjustSize()
        height = min(self.sizeHint().height(), max_height)
        self.setFixedHeight(height)
        x = max(margin, container_width - self.CARD_WIDTH - margin)
        self.move(x, top)
