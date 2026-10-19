from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.detection.persistence_service import TargetDetectionService
from maap_app.modules.ground_transport.service import GroundTransportService
from maap_app.modules.target.models import TargetCardDetail
from maap_app.modules.target.service import TargetService
from maap_app.modules.wing_data.models import WingMapDetail
from maap_app.modules.wing_data.service import WingDataService
from maap_app.ui.panels.map_ground_transport_panel import MapGroundTransportPanel
from maap_app.ui.panels.map_targets_list_panel import MapTargetsListPanel
from maap_app.ui.panels.map_wing_detail_panel import MapWingDetailPanel


class MapDetailSidebar(QWidget):
    """Collapsible left sidebar for map targets list and wing details."""

    expanded_changed = Signal(bool)
    open_in_target_stack = Signal(str)
    open_wing_in_database = Signal(str)
    target_entry_selected = Signal(str, str)
    view_all_targets = Signal()
    transport_selected = Signal(str)
    sidebar_view_changed = Signal(str)

    COLLAPSED_WIDTH = 30
    EXPANDED_WIDTH = 320

    def __init__(
        self,
        target_service: TargetService,
        detection_service: TargetDetectionService,
        transport_service: GroundTransportService,
        wing_data_service: WingDataService,
    ) -> None:
        super().__init__()
        self.setObjectName("DetailPanel")
        self._expanded = True
        self._syncing = False
        self._mode = "targets"
        self._sidebar_view = "targets"

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._apply_width()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.outer_stack = QStackedWidget()

        expanded_host = QWidget()
        expanded_layout = QVBoxLayout(expanded_host)
        expanded_layout.setContentsMargins(0, 0, 0, 0)
        expanded_layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("MapTargetSidebarHeader")
        header.setFixedHeight(42)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 6, 0)
        header_layout.setSpacing(4)
        self.title_label = QLabel("TARGETS")
        self.title_label.setObjectName("MapTargetSidebarTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)

        self.targets_view_btn = QPushButton("Target")
        self.targets_view_btn.setObjectName("MapSidebarModeButton")
        self.targets_view_btn.setCheckable(True)
        self.targets_view_btn.setChecked(True)
        self.targets_view_btn.setFixedHeight(24)
        self.targets_view_btn.clicked.connect(
            lambda: self.set_sidebar_view("targets")
        )
        header_layout.addWidget(self.targets_view_btn)

        self.transport_view_btn = QPushButton("ขนส่ง")
        self.transport_view_btn.setObjectName("MapSidebarModeButton")
        self.transport_view_btn.setCheckable(True)
        self.transport_view_btn.setFixedHeight(24)
        self.transport_view_btn.clicked.connect(
            lambda: self.set_sidebar_view("transport")
        )
        header_layout.addWidget(self.transport_view_btn)

        self.collapse_btn = QPushButton("‹")
        self.collapse_btn.setObjectName("MapTargetIconButton")
        self.collapse_btn.setFixedSize(26, 26)
        self.collapse_btn.setToolTip("ซ่อนรายการ Target")
        self.collapse_btn.clicked.connect(lambda: self.set_expanded(False))
        header_layout.addWidget(self.collapse_btn)
        expanded_layout.addWidget(header)

        self.content_stack = QStackedWidget()
        self.targets_list_panel = MapTargetsListPanel(target_service, detection_service)
        self.transport_panel = MapGroundTransportPanel(
            transport_service,
            wing_data_service,
        )
        self.wing_panel = MapWingDetailPanel()
        self.content_stack.addWidget(self.targets_list_panel)
        self.content_stack.addWidget(self.transport_panel)
        self.content_stack.addWidget(self.wing_panel)
        expanded_layout.addWidget(self.content_stack, stretch=1)

        collapsed_host = QWidget()
        collapsed_layout = QVBoxLayout(collapsed_host)
        collapsed_layout.setContentsMargins(0, 0, 0, 0)
        collapsed_layout.setSpacing(0)
        collapsed_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        collapsed_header = QWidget()
        collapsed_header.setObjectName("MapTargetSidebarHeader")
        collapsed_header.setFixedHeight(42)
        ch_layout = QHBoxLayout(collapsed_header)
        ch_layout.setContentsMargins(0, 0, 0, 0)
        ch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.expand_btn = QPushButton("›")
        self.expand_btn.setObjectName("MapTargetIconButton")
        self.expand_btn.setFixedSize(26, 26)
        self.expand_btn.setToolTip("แสดงรายการ Target")
        self.expand_btn.clicked.connect(lambda: self.set_expanded(True))
        ch_layout.addWidget(self.expand_btn)
        collapsed_layout.addWidget(collapsed_header)

        self.outer_stack.addWidget(expanded_host)
        self.outer_stack.addWidget(collapsed_host)
        root.addWidget(self.outer_stack)

        self.targets_list_panel.entry_selected.connect(self.target_entry_selected.emit)
        self.targets_list_panel.view_all_requested.connect(self.view_all_targets.emit)
        self.targets_list_panel.open_in_target_stack.connect(self.open_in_target_stack.emit)
        self.transport_panel.transport_selected.connect(self.transport_selected.emit)
        self.wing_panel.open_in_database.connect(self.open_wing_in_database.emit)
        self.set_expanded(True)
        self.set_sidebar_view("targets")

    def set_sidebar_view(self, view: str) -> None:
        normalized = "transport" if view == "transport" else "targets"
        if self._sidebar_view == normalized and self._mode != "wing":
            self._sync_sidebar_view_buttons()
            return
        self._sidebar_view = normalized
        self._mode = normalized
        self.targets_view_btn.setChecked(normalized == "targets")
        self.transport_view_btn.setChecked(normalized == "transport")
        if normalized == "transport":
            self.title_label.setText("ขนส่งทางบก")
            self.content_stack.setCurrentWidget(self.transport_panel)
            self.collapse_btn.setToolTip("ซ่อนรายการขนส่ง")
            self.expand_btn.setToolTip("แสดงรายการขนส่ง")
        else:
            self.title_label.setText("TARGETS")
            self.content_stack.setCurrentWidget(self.targets_list_panel)
            self.collapse_btn.setToolTip("ซ่อนรายการ Target")
            self.expand_btn.setToolTip("แสดงรายการ Target")
        self.sidebar_view_changed.emit(normalized)

    def _sync_sidebar_view_buttons(self) -> None:
        self.targets_view_btn.setChecked(self._sidebar_view == "targets")
        self.transport_view_btn.setChecked(self._sidebar_view == "transport")

    def is_expanded(self) -> bool:
        return self._expanded

    def set_expanded(self, expanded: bool) -> None:
        if self._expanded == expanded:
            return
        self._expanded = expanded
        self.outer_stack.setCurrentIndex(0 if expanded else 1)
        self._apply_width()
        if not self._syncing:
            self.expanded_changed.emit(expanded)

    def set_expanded_silent(self, expanded: bool) -> None:
        self._syncing = True
        try:
            self.set_expanded(expanded)
        finally:
            self._syncing = False

    def _apply_width(self) -> None:
        width = self.EXPANDED_WIDTH if self._expanded else self.COLLAPSED_WIDTH
        self.setFixedWidth(width)

    def set_scenario(self, scenario_id: str | None) -> None:
        self.targets_list_panel.set_scenario(scenario_id)
        self.transport_panel.set_scenario(scenario_id)

    def refresh_targets(self) -> None:
        self.targets_list_panel.refresh()

    def refresh_transports(self) -> None:
        self.transport_panel.refresh()

    def select_transport(self, transport_id: str | None) -> None:
        self.transport_panel.select_transport(transport_id)

    def clear(self) -> None:
        self._mode = self._sidebar_view
        if self._sidebar_view == "transport":
            self.title_label.setText("ขนส่งทางบก")
            self.content_stack.setCurrentWidget(self.transport_panel)
            self.transport_panel.clear_selection()
        else:
            self.title_label.setText("TARGETS")
            self.content_stack.setCurrentWidget(self.targets_list_panel)
            self.targets_list_panel.clear_selection()
        self.wing_panel.clear()

    def show_target(
        self,
        detail: TargetCardDetail,
        marker: dict[str, Any] | None = None,
    ) -> None:
        if not self._expanded:
            self.set_expanded(True)
        self._mode = "targets"
        self.set_sidebar_view("targets")
        coordinate_id = ""
        if marker is not None:
            coordinate_id = str(
                marker.get("coordinateId") or f"legacy-{detail.card.id}"
            )
        elif detail.coordinates:
            primary = next(
                (coord for coord in detail.coordinates if coord.is_primary),
                detail.coordinates[0],
            )
            coordinate_id = primary.id
        elif detail.map_lat is not None:
            coordinate_id = f"legacy-{detail.card.id}"
        self.targets_list_panel.select_entry(detail.card.id, coordinate_id or None)

    def show_wing(self, detail: WingMapDetail) -> None:
        if not self._expanded:
            self.set_expanded(True)
        self._mode = "wing"
        self.title_label.setText("กองบิน")
        self.content_stack.setCurrentWidget(self.wing_panel)
        self.wing_panel.show_wing(detail)

    def show_targets_list(self) -> None:
        self.set_sidebar_view("targets")
