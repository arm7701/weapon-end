from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.flight_route.params import (
    MAX_FLIGHT_ALTITUDE_FT,
    MIN_FLIGHT_ALTITUDE_FT,
    RouteStyle,
)


class MapAiRoutePlannerPanel(QWidget):
    """Floating AI route planner on the map workspace."""

    closed = Signal()
    plan_requested = Signal()
    apply_requested = Signal()
    clear_requested = Signal()
    use_plan_endpoints_requested = Signal()
    takeoff_pick_toggled = Signal(bool)
    landing_pick_toggled = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MapAiRoutePlannerPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setVisible(False)
        self.setFixedWidth(280)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setObjectName("MapFlightRouteEditorHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 8, 8)
        title = QLabel("AI Route Planner")
        title.setObjectName("MapFlightRouteEditorTitle")
        header_layout.addWidget(title, stretch=1)
        close_btn = QPushButton("×")
        close_btn.setObjectName("MapTargetDetailCloseButton")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.closed.emit)
        header_layout.addWidget(close_btn)
        root.addWidget(header)

        body = QWidget()
        body.setObjectName("MapFlightRouteEditorBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 8, 12, 12)
        body_layout.setSpacing(8)

        pick_row = QHBoxLayout()
        pick_row.setSpacing(6)
        self.takeoff_btn = QPushButton("Takeoff")
        self.takeoff_btn.setObjectName("MapTargetIngressViewButton")
        self.takeoff_btn.setCheckable(True)
        self.takeoff_btn.setToolTip("Takeoff ใช้พิกัดกองบินที่ผูกกับแผน (กด ใช้จากแผนการบิน)")
        self.takeoff_btn.toggled.connect(self._on_takeoff_toggled)
        pick_row.addWidget(self.takeoff_btn)
        self.landing_btn = QPushButton("Landing")
        self.landing_btn.setObjectName("MapTargetIngressViewButton")
        self.landing_btn.setCheckable(True)
        self.landing_btn.setToolTip(
            "Landing = RTB กลับพิกัดกองบินเดิม (อัตโนมัติ)"
        )
        self.landing_btn.toggled.connect(self._on_landing_toggled)
        pick_row.addWidget(self.landing_btn)
        body_layout.addLayout(pick_row)

        self.takeoff_label = QLabel("TO: —")
        self.takeoff_label.setObjectName("FormSectionSubtitle")
        self.takeoff_label.setWordWrap(True)
        body_layout.addWidget(self.takeoff_label)
        self.landing_label = QLabel("LD: —")
        self.landing_label.setObjectName("FormSectionSubtitle")
        self.landing_label.setWordWrap(True)
        body_layout.addWidget(self.landing_label)

        self.use_plan_btn = QPushButton("ใช้จากแผนการบิน")
        self.use_plan_btn.setObjectName("SecondaryButton")
        self.use_plan_btn.setToolTip(
            "โหลดพิกัดกองบินจากแผน Weaponeering ของ Target นี้"
        )
        self.use_plan_btn.clicked.connect(self.use_plan_endpoints_requested.emit)
        body_layout.addWidget(self.use_plan_btn)

        style_title = QLabel("Route Style")
        style_title.setObjectName("FormFieldLabel")
        body_layout.addWidget(style_title)
        self._style_group = QButtonGroup(self)
        styles = (
            (RouteStyle.LOW_LEVEL, "Low-Level (AGL)"),
            (RouteStyle.CRUISE, "Pilot Cruise (MSL)"),
            (RouteStyle.VALLEY, "Valley Cruise"),
            (RouteStyle.HYBRID, "Hybrid LL"),
        )
        for index, (style, label) in enumerate(styles):
            radio = QRadioButton(label)
            radio.setObjectName("MapAiRouteStyleRadio")
            radio.setProperty("routeStyle", style.value)
            if index == 0:
                radio.setChecked(True)
            self._style_group.addButton(radio, index)
            body_layout.addWidget(radio)

        params_grid = QGridLayout()
        params_grid.setHorizontalSpacing(8)
        params_grid.setVerticalSpacing(6)
        self.min_agl = self._spin("Min AGL (m)", 50, 500, 80)
        self.pref_agl = self._spin("Pref AGL (m)", 50, 800, 105)
        self.max_agl = self._spin("Max AGL (m)", 50, 1000, 120)
        self.cruise_alt_ft = self._spin(
            "Flight Alt (ft)",
            MIN_FLIGHT_ALTITUDE_FT,
            MAX_FLIGHT_ALTITUDE_FT,
            25000,
        )
        self.cruise_alt_ft.setToolTip(
            "ความสูงบิน en-route / จำลอง AI (500–100,000 ft)"
        )
        self.cruise_pad = self._spin("Cruise Pad (m)", 0, 500, 105)
        self.grid_m = self._spin("Grid (m)", 40, 500, 80)
        self.cruise_kts = self._spin("Cruise (kts)", 60, 600, 250)
        self.turn_radius = self._spin("Turn R (m)", 200, 5000, 800)
        fields = (
            ("Min AGL (m)", self.min_agl),
            ("Pref AGL (m)", self.pref_agl),
            ("Max AGL (m)", self.max_agl),
            ("Flight Alt (ft)", self.cruise_alt_ft),
            ("Cruise Pad (m)", self.cruise_pad),
            ("Grid (m)", self.grid_m),
            ("Cruise (kts)", self.cruise_kts),
            ("Turn R (m)", self.turn_radius),
        )
        for row, (label, spin) in enumerate(fields):
            title = QLabel(label)
            title.setObjectName("FormFieldLabel")
            params_grid.addWidget(title, row, 0)
            params_grid.addWidget(spin, row, 1)
        body_layout.addLayout(params_grid)

        self.status_label = QLabel("เลือก Target · กำหนด Takeoff/Landing แล้วกด Plan Route")
        self.status_label.setObjectName("FormSectionSubtitle")
        self.status_label.setWordWrap(True)
        body_layout.addWidget(self.status_label)

        plan_row = QHBoxLayout()
        plan_row.setSpacing(6)
        self.plan_btn = QPushButton("Plan Route")
        self.plan_btn.setObjectName("PrimaryButton")
        self.plan_btn.clicked.connect(self.plan_requested.emit)
        plan_row.addWidget(self.plan_btn)
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("MapTargetIngressViewButton")
        self.apply_btn.setEnabled(False)
        self._route_ready = False
        self._planning_busy = False
        self.apply_btn.clicked.connect(self.apply_requested.emit)
        plan_row.addWidget(self.apply_btn)
        body_layout.addLayout(plan_row)

        clear_btn = QPushButton("Clear Route")
        clear_btn.setObjectName("MapTargetFooterButton")
        clear_btn.clicked.connect(self.clear_requested.emit)
        body_layout.addWidget(clear_btn)

        root.addWidget(body)

    @staticmethod
    def _spin(_label: str, min_v: int, max_v: int, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setObjectName("MapToolbarSpin")
        spin.setRange(min_v, max_v)
        spin.setValue(value)
        return spin

    def _on_takeoff_toggled(self, checked: bool) -> None:
        if checked:
            self.landing_btn.blockSignals(True)
            self.landing_btn.setChecked(False)
            self.landing_btn.blockSignals(False)
        self.takeoff_pick_toggled.emit(checked)

    def _on_landing_toggled(self, checked: bool) -> None:
        if checked:
            self.takeoff_btn.blockSignals(True)
            self.takeoff_btn.setChecked(False)
            self.takeoff_btn.blockSignals(False)
        self.landing_pick_toggled.emit(checked)

    def selected_route_style(self) -> RouteStyle:
        button = self._style_group.checkedButton()
        if button is None:
            return RouteStyle.LOW_LEVEL
        value = str(button.property("routeStyle") or RouteStyle.LOW_LEVEL.value)
        try:
            return RouteStyle(value)
        except ValueError:
            return RouteStyle.LOW_LEVEL

    def set_takeoff_label(self, text: str) -> None:
        self.takeoff_label.setText(f"TO: {text}")

    def set_landing_label(self, text: str) -> None:
        self.landing_label.setText(f"LD: {text}")

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def set_route_ready(self, ready: bool) -> None:
        self._route_ready = ready
        if not self._planning_busy:
            self.apply_btn.setEnabled(ready)

    def set_planning_busy(self, busy: bool, message: str | None = None) -> None:
        self._planning_busy = busy
        self.plan_btn.setEnabled(not busy)
        if busy:
            self.set_status(message or "กำลังวางเส้นทาง…")
            self.apply_btn.setEnabled(False)
        else:
            self.apply_btn.setEnabled(self._route_ready)

    def clear_pick_modes(self) -> None:
        self.takeoff_btn.blockSignals(True)
        self.landing_btn.blockSignals(True)
        self.takeoff_btn.setChecked(False)
        self.landing_btn.setChecked(False)
        self.takeoff_btn.blockSignals(False)
        self.landing_btn.blockSignals(False)

    def position_in_container(self, container_width: int, container_height: int) -> None:
        margin = 12
        top = 54
        max_height = max(container_height - top - margin, 200)
        self.setMaximumHeight(max_height)
        self.adjustSize()
        height = min(self.sizeHint().height(), max_height)
        self.setFixedHeight(height)
        self.move(margin, top)
