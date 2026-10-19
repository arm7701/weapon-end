from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.ai.service import AiAssistantService
from maap_app.modules.ranking.service import RankingService
from maap_app.modules.target.models import TargetCard
from maap_app.modules.target.profile_fields import TargetProfileFields
from maap_app.modules.target.schemas import UpdateTargetCardRequest
from maap_app.modules.target.service import TargetService
from maap_app.modules.weaponeering.jmem_calculator import (
    EFFECT_ZONE_COLORS,
    JmemWeaponInputs,
    apply_selected_product_rank,
    build_target_context,
    estimate_mae_building_ft2,
    format_orange_range_m_ft,
    format_range_m_ft,
    rank_weapons,
)
from maap_app.modules.weaponeering.flight_path import (
    FlightProfileSettings,
    FlightWaypointSpec,
    bearing_deg,
    compute_flight_profile,
    format_distance_km,
    format_duration_min,
)
from maap_app.modules.weaponeering.mission_defaults import SIM_FLIGHT_DEFAULTS
from maap_app.modules.weaponeering.trajectory import (
    climb_horizontal_distance_m,
    descent_horizontal_distance_m,
)
from maap_app.modules.weaponeering.schemas import (
    DeploymentAircraftLineRequest,
    DeploymentWaypointRequest,
    UpsertDeploymentPlanRequest,
)
from maap_app.modules.weaponeering.service import WeaponeeringService
from maap_app.modules.weaponeering.product_advisor import (
    ProductRecommendation,
    product_analysis_prompt,
    recommend_product,
)
from maap_app.modules.weaponeering.laser_designation import designation_info_for
from maap_app.modules.weaponeering.weapon_effects import weapon_effects_info
from maap_app.modules.weaponeering.circular_error import circular_error_info
from maap_app.modules.wing_data.service import WingDataService
from maap_app.ui.panels.target_panel import TargetCalculationSnapshot
from maap_app.ui.panels.wing_form_widgets import _coord_spin, _field_row, _form_card, _int_spin
from maap_app.ui.product_images import ProductImageLabel


_RANGE_COLORS = EFFECT_ZONE_COLORS
_AI_ANALYZE_BTN_LABEL = "AI วิเคราะห์สินค้า"
_AI_ANALYZE_LOADING_LABEL = "กำลังวิเคราะห์..."


def _merge_card_profile(card: TargetCard, profile: TargetProfileFields) -> TargetCard:
    return replace(
        card,
        target_type=profile.target_type,
        target_subtype=profile.target_subtype,
        material_class=profile.material_class,
        target_description=profile.target_description,
        floor_count=profile.floor_count,
        width_m=profile.width_m,
        length_m=profile.length_m,
        height_m=profile.height_m,
        desired_model_result=profile.desired_model_result,
        coordinate_error_m=profile.coordinate_error_m,
        data_source=profile.data_source,
        cep=profile.cep,
        target_pk=profile.target_pk,
        reference_pk=profile.reference_pk,
        resistance=profile.resistance,
        capacity=profile.capacity,
        damage_fit=profile.damage_fit,
        model_version=profile.model_version,
    )


def _fmt_ready(status: str) -> str:
    return "พร้อม" if status == "ready" else "ไม่พร้อม"


@dataclass
class _PointWeaponeeringResult:
    key: str
    label: str
    lat: float
    lng: float
    is_primary: bool
    results: list
    mission: object
    coordinate_id: str | None = None
    selected_product_id: str | None = None
    ranked_wings: list | None = None


def _point_key(label: str, lat: float, lng: float) -> str:
    return f"{label}|{lat:.5f}|{lng:.5f}"


def _collect_target_points(
    detail,
    snapshot: TargetCalculationSnapshot | None,
) -> list[tuple[str, float, float, bool, str | None, str | None]]:
    points: list[tuple[str, float, float, bool, str | None, str | None]] = []
    if snapshot is not None and snapshot.coordinates:
        for index, coord in enumerate(snapshot.coordinates):
            label = coord.label.strip() or f"P{index + 1}"
            points.append(
                (
                    label,
                    coord.map_lat,
                    coord.map_lng,
                    coord.is_primary,
                    coord.id,
                    coord.selected_product_id,
                )
            )
    elif detail.coordinates:
        for index, coord in enumerate(detail.coordinates):
            label = coord.label.strip() or f"P{index + 1}"
            points.append(
                (
                    label,
                    coord.map_lat,
                    coord.map_lng,
                    coord.is_primary,
                    coord.id,
                    coord.selected_product_id,
                )
            )
    elif detail.map_lat is not None and detail.map_lng is not None:
        points.append(
            (
                "P1",
                detail.map_lat,
                detail.map_lng,
                True,
                None,
                detail.card.selected_product_id,
            )
        )
    return points


def _wrap_layout(layout: QHBoxLayout) -> QWidget:
    host = QWidget()
    host.setLayout(layout)
    return host


def _zone_legend_row() -> QWidget:
    host = QWidget()
    layout = QHBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for label, color in (
        ("แดง", _RANGE_COLORS["red"]),
        ("ส้ม", _RANGE_COLORS["orange"]),
        ("เหลืองเข้ม", _RANGE_COLORS["yellow_dark"]),
        ("เหลือง", _RANGE_COLORS["yellow_light"]),
    ):
        chip = QLabel(label)
        chip.setStyleSheet(
            f"background:{color}; color:#0a1018; font-size:9px; "
            "font-weight:700; border-radius:4px; padding:2px 6px;"
        )
        layout.addWidget(chip)
    layout.addStretch(1)
    return host


class _PlanAircraftRow(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.aircraft = QComboBox()
        self.count = _int_spin(1, 99)
        self.remove_btn = QPushButton("ลบ")
        self.remove_btn.setObjectName("GhostButton")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.aircraft, stretch=1)
        layout.addWidget(self.count)
        layout.addWidget(self.remove_btn)

    def populate_options(
        self,
        wing_data_service: WingDataService,
        scenario_id: str | None,
        wing_id: str | None,
        unit_id: str | None,
        selected_aircraft_id: str | None = None,
    ) -> None:
        selected = selected_aircraft_id or self.aircraft.currentData()
        self.aircraft.blockSignals(True)
        self.aircraft.clear()
        self.aircraft.addItem("(เลือกเครื่องบิน)", "")
        unit_names = {
            unit.id: unit.unit_name
            for unit in (
                wing_data_service.list_flying_units(scenario_id)
                if scenario_id
                else []
            )
        }
        if scenario_id and wing_id:
            for aircraft in wing_data_service.list_aircraft(scenario_id):
                if aircraft.wing_id != wing_id:
                    continue
                if unit_id and aircraft.flying_unit_id != unit_id:
                    continue
                unit_label = unit_names.get(aircraft.flying_unit_id or "", "—")
                label = (
                    f"{aircraft.aircraft_type} · {unit_label} · "
                    f"{_fmt_ready(aircraft.mission_ready)}"
                )
                self.aircraft.addItem(label, aircraft.id)
        if selected:
            idx = self.aircraft.findData(selected)
            if idx >= 0:
                self.aircraft.setCurrentIndex(idx)
        self.aircraft.blockSignals(False)

    def values(self) -> tuple[str, int] | None:
        aircraft_id = self.aircraft.currentData()
        if not aircraft_id:
            return None
        return str(aircraft_id), self.count.value()


class _PlanWaypointRow(QWidget):
    def __init__(
        self,
        *,
        labels: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.label = QComboBox()
        self.label.setEditable(True)
        self.label.addItems(labels or ["WP", "Corridor", "IP", "CAP"])
        self.lat = _coord_spin()
        self.lng = _coord_spin(100.0)
        self.altitude_ft = _int_spin(0, 55000)
        self.altitude_ft.setSpecialValueText("Cruise")
        self.remove_btn = QPushButton("ลบ")
        self.remove_btn.setObjectName("GhostButton")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.label, stretch=1)
        layout.addWidget(self.lat)
        layout.addWidget(self.lng)
        layout.addWidget(self.altitude_ft)
        layout.addWidget(self.remove_btn)

    def values(self) -> tuple[str, float, float, int | None] | None:
        label = self.label.currentText().strip()
        if not label:
            label = "WP"
        altitude = self.altitude_ft.value()
        altitude_ft = None if altitude <= 0 else altitude
        return label, self.lat.value(), self.lng.value(), altitude_ft


class _RangeZonesBar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._red = 0.0
        self._orange = 0.0
        self._yellow_dark = 0.0
        self._yellow_light = 0.0
        self.setMinimumHeight(18)
        self.setMaximumHeight(18)

    def set_ranges(
        self,
        red_km: float,
        orange_km: float,
        yellow_dark_km: float,
        yellow_light_km: float,
    ) -> None:
        self._red = red_km
        self._orange = orange_km
        self._yellow_dark = yellow_dark_km
        self._yellow_light = yellow_light_km
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        from PySide6.QtGui import QColor, QPainter

        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width()
        height = self.height()
        if width <= 0:
            return

        max_km = max(self._yellow_light, 1.0)
        segments = (
            (self._red, _RANGE_COLORS["red"]),
            (self._orange, _RANGE_COLORS["orange"]),
            (self._yellow_dark, _RANGE_COLORS["yellow_dark"]),
            (self._yellow_light, _RANGE_COLORS["yellow_light"]),
        )
        x = 0
        for km, color in segments:
            segment_w = max(int(width * (km / max_km)), 1)
            painter.fillRect(x, 0, segment_w, height, QColor(color))
            x += segment_w
        if x < width:
            painter.fillRect(x, 0, width - x, height, QColor("#1a2433"))


class WeaponeeringPanel(QWidget):
    weaponeering_changed = Signal()
    ranking_completed = Signal()

    def __init__(
        self,
        weaponeering_service: WeaponeeringService,
        target_service: TargetService,
        ranking_service: RankingService,
        wing_data_service: WingDataService,
        ai_service: AiAssistantService | None = None,
    ) -> None:
        super().__init__()
        self.weaponeering_service = weaponeering_service
        self.target_service = target_service
        self.ranking_service = ranking_service
        self.wing_data_service = wing_data_service
        self.ai_service = ai_service
        self._scenario_id: str | None = None
        self._selected_target_id: str | None = None
        self._target_lat: float | None = None
        self._target_lng: float | None = None
        self._target_inputs_provider: Callable[
            [str], TargetCalculationSnapshot | None
        ] | None = None
        self._point_results: list[_PointWeaponeeringResult] = []
        self._active_point_key: str | None = None
        self._manual_product_selection = False
        self._mission_cep_ft: float | None = None
        self._ai_product_recommendation: ProductRecommendation | None = None
        self._ai_product_summary: str | None = None
        self._ai_product_analyzing = False
        self._build_ui()

    def set_target_inputs_provider(
        self,
        provider: Callable[[str], TargetCalculationSnapshot | None] | None,
    ) -> None:
        self._target_inputs_provider = provider

    def recalculate(self) -> None:
        self._recalculate()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        active = self._active_point_result()
        if active is not None and active.results:
            self._update_top_product_image(active.results[0].product_name)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)

        target_card, target_layout = _form_card(
            "เป้าหมาย",
            "ค่าจาก Target Stack สำหรับคำนวณ JMEM",
        )
        self.target_hero = QLabel("ยังไม่ได้เลือก Target")
        self.target_hero.setStyleSheet("color: #e8f0f8; font-size: 12px; font-weight: 700;")
        self.target_hero.setWordWrap(True)
        target_layout.addWidget(self.target_hero)

        self.target_meta = QLabel("เลือก Target จาก Target Stack")
        self.target_meta.setObjectName("FormSectionSubtitle")
        self.target_meta.setWordWrap(True)
        target_layout.addWidget(self.target_meta)

        self.inputs_grid = QGridLayout()
        self.inputs_grid.setHorizontalSpacing(10)
        self.inputs_grid.setVerticalSpacing(6)
        self._input_labels: dict[str, QLabel] = {}
        for index, (key, title) in enumerate(
            (
                ("cep", "CEP"),
                ("tle", "TLE"),
                ("pk", "Desired PK"),
                ("size", "Area"),
                ("angle", "Impact θ"),
                ("burial", "Burial %"),
            )
        ):
            row = index // 3
            col = (index % 3) * 2
            name = QLabel(title)
            name.setObjectName("FormFieldLabel")
            value = QLabel("—")
            value.setStyleSheet("color: #d7dee8; font-size: 11px; font-weight: 600;")
            self.inputs_grid.addWidget(name, row, col)
            self.inputs_grid.addWidget(value, row, col + 1)
            self._input_labels[key] = value
        target_layout.addLayout(self.inputs_grid)

        self.warnings_label = QLabel("")
        self.warnings_label.setWordWrap(True)
        self.warnings_label.setStyleSheet("color: #d4a017; font-size: 10px;")
        target_layout.addWidget(self.warnings_label)
        body_layout.addWidget(target_card)

        rank_card, rank_layout = _form_card(
            "สินค้า",
            "จัดอันดับ Pd · N · เลือกสินค้าแยกตามแต่ละพิกัด (P1/P2/P3)",
        )
        self.top_product_hero = QLabel("—")
        self.top_product_hero.setStyleSheet("color: #e8f0f8; font-size: 12px; font-weight: 700;")
        rank_layout.addWidget(self.top_product_hero)
        self.top_product_stats = QLabel("กด คำนวณใหม่ หลังเลือก Target")
        self.top_product_stats.setStyleSheet("color: #9fb0c2; font-size: 10px;")
        self.top_product_stats.setWordWrap(True)
        rank_layout.addWidget(self.top_product_stats)
        self.laser_designation_box = QLabel()
        self.laser_designation_box.setWordWrap(True)
        self.laser_designation_box.setStyleSheet(
            "color: #fcd34d; font-size: 10px; padding: 6px 0;"
        )
        self.laser_designation_box.setVisible(False)
        rank_layout.addWidget(self.laser_designation_box)
        self.weapon_effects_box = QLabel()
        self.weapon_effects_box.setWordWrap(True)
        self.weapon_effects_box.setStyleSheet(
            "color: #fecaca; font-size: 10px; padding: 6px 0;"
        )
        self.weapon_effects_box.setVisible(False)
        rank_layout.addWidget(self.weapon_effects_box)
        self.circular_error_box = QLabel()
        self.circular_error_box.setWordWrap(True)
        self.circular_error_box.setStyleSheet(
            "color: #c7d2fe; font-size: 10px; padding: 6px 0;"
        )
        self.circular_error_box.setVisible(False)
        rank_layout.addWidget(self.circular_error_box)

        image_row = QHBoxLayout()
        image_row.setContentsMargins(0, 0, 0, 0)
        image_row.setSpacing(0)
        self.top_product_image = ProductImageLabel()
        image_row.addWidget(self.top_product_image)
        image_row.addStretch(1)
        rank_layout.addLayout(image_row)

        selection_row = QHBoxLayout()
        selection_row.setSpacing(6)
        self.selected_product_combo = QComboBox()
        self.selected_product_combo.currentIndexChanged.connect(
            self._on_selected_product_combo_changed
        )
        self.use_table_row_btn = QPushButton("ใช้แถวที่เลือก")
        self.use_table_row_btn.setObjectName("SecondaryButton")
        self.use_table_row_btn.clicked.connect(self._on_use_table_row_for_selection)
        self.clear_product_btn = QPushButton("ยกเลิก")
        self.clear_product_btn.setObjectName("SecondaryButton")
        self.clear_product_btn.clicked.connect(self._on_clear_product_selection)
        selection_row.addWidget(self.selected_product_combo, stretch=1)
        selection_row.addWidget(self.use_table_row_btn)
        selection_row.addWidget(self.clear_product_btn)
        rank_layout.addLayout(selection_row)

        ai_product_row = QHBoxLayout()
        ai_product_row.setSpacing(6)
        self.ai_analyze_btn = QPushButton(_AI_ANALYZE_BTN_LABEL)
        self.ai_analyze_btn.setObjectName("SecondaryButton")
        self.ai_analyze_btn.clicked.connect(self._on_ai_analyze_product)
        self.ai_apply_btn = QPushButton("ใช้คำแนะนำ AI")
        self.ai_apply_btn.setObjectName("PrimaryButton")
        self.ai_apply_btn.clicked.connect(self._on_ai_apply_product_recommendation)
        self.ai_apply_btn.setEnabled(False)
        ai_product_row.addWidget(self.ai_analyze_btn)
        ai_product_row.addWidget(self.ai_apply_btn)
        ai_product_row.addStretch(1)
        rank_layout.addLayout(ai_product_row)

        self.ai_product_summary = QLabel(
            "กด AI วิเคราะห์สินค้า หลังคำนวณ JMEM — ระบบจะพิจารณา Pd, N, Desired PK, ค่าใช้จ่าย และสต็อก"
        )
        self.ai_product_summary.setObjectName("FormSectionSubtitle")
        self.ai_product_summary.setWordWrap(True)
        rank_layout.addWidget(self.ai_product_summary)

        product_toolbar = QHBoxLayout()
        product_toolbar.setSpacing(6)
        self.coord_selector = QComboBox()
        self.coord_selector.currentIndexChanged.connect(self._on_coord_selector_changed)
        self.recalc_btn = QPushButton("คำนวณใหม่")
        self.recalc_btn.setObjectName("PrimaryButton")
        self.recalc_btn.clicked.connect(self.recalculate)
        product_toolbar.addWidget(self.coord_selector, stretch=1)
        product_toolbar.addWidget(self.recalc_btn)
        rank_layout.addLayout(product_toolbar)
        rank_layout.addWidget(_zone_legend_row())

        self.rank_table = QTableWidget(0, 6)
        self.rank_table.setHorizontalHeaderLabels(
            [
                "#",
                "สินค้า",
                "Pd",
                "PK₁",
                "N",
                "PKₙ",
            ]
        )
        self.rank_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rank_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.rank_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.rank_table.setAlternatingRowColors(True)
        self.rank_table.doubleClicked.connect(self._on_rank_table_double_clicked)
        self.rank_table.verticalHeader().setVisible(False)
        self.rank_table.setMaximumHeight(220)
        header = self.rank_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        rank_layout.addWidget(self.rank_table)

        self.range_bars_host = QWidget()
        self.range_bars_layout = QVBoxLayout(self.range_bars_host)
        self.range_bars_layout.setContentsMargins(0, 0, 0, 0)
        self.range_bars_layout.setSpacing(4)
        rank_layout.addWidget(self.range_bars_host)

        self.recommendations_host = QWidget()
        self.recommendations_layout = QVBoxLayout(self.recommendations_host)
        self.recommendations_layout.setContentsMargins(0, 0, 0, 0)
        self.recommendations_layout.setSpacing(2)
        self.recalc_status = QLabel("เลือก Target แล้วกด คำนวณใหม่")
        self.recalc_status.setObjectName("FormSectionSubtitle")
        self.recalc_status.setWordWrap(True)
        self.recommendations_layout.addWidget(self.recalc_status)
        rank_layout.addWidget(self.recommendations_host)
        body_layout.addWidget(rank_card)

        wing_card, wing_layout = _form_card(
            "Nearest Air Wing",
            "ค้นหากองบินที่ใกล้เป้าหมายที่สุดจากพิกัด Target Stack (Haversine)",
        )
        wing_action_row = QHBoxLayout()
        self.find_wing_btn = QPushButton("ค้นหากองบินใกล้เคียง")
        self.find_wing_btn.setObjectName("SecondaryButton")
        self.find_wing_btn.clicked.connect(self._search_nearest_wing)
        wing_action_row.addWidget(self.find_wing_btn)
        wing_action_row.addStretch(1)
        wing_layout.addLayout(wing_action_row)

        self.nearest_wing_label = QLabel("ยังไม่ได้ค้นหา — ต้องมีพิกัดเป้าหมายและกองบินใน Database")
        self.nearest_wing_label.setObjectName("FormSectionSubtitle")
        self.nearest_wing_label.setWordWrap(True)
        wing_layout.addWidget(self.nearest_wing_label)

        self.wing_table = QTableWidget(0, 6)
        self.wing_table.setHorizontalHeaderLabels(
            ["Rank", "กองบิน", "ระยะ (km)", "ระยะ (nm)", "LAT", "LNG"]
        )
        self.wing_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.wing_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.wing_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.wing_table.setAlternatingRowColors(True)
        self.wing_table.verticalHeader().setVisible(False)
        self.wing_table.setMaximumHeight(160)
        wing_header = self.wing_table.horizontalHeader()
        wing_header.setStretchLastSection(True)
        wing_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        wing_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        wing_layout.addWidget(self.wing_table)
        body_layout.addWidget(wing_card)

        plan_card, plan_layout = _form_card(
            "แผนประจำ Target",
            "กำหนดกองบิน หน่วยบิน และรายการเครื่องบิน (หลายรายการได้) สำหรับเป้าหมายนี้",
        )
        self.plan_wing = QComboBox()
        self.plan_unit = QComboBox()
        self._plan_aircraft_rows: list[_PlanAircraftRow] = []
        self.plan_aircraft_rows_host = QWidget()
        self.plan_aircraft_rows_layout = QVBoxLayout(self.plan_aircraft_rows_host)
        self.plan_aircraft_rows_layout.setContentsMargins(0, 0, 0, 0)
        self.plan_aircraft_rows_layout.setSpacing(6)
        self.plan_wing.currentIndexChanged.connect(self._on_plan_wing_changed)
        self.plan_unit.currentIndexChanged.connect(self._on_plan_unit_changed)
        self.plan_wing.currentIndexChanged.connect(self._apply_wing_takeoff_coords)
        plan_layout.addWidget(_field_row("กองบิน", self.plan_wing))
        plan_layout.addWidget(_field_row("หน่วยบิน", self.plan_unit))
        plan_layout.addWidget(QLabel("รายการเครื่องบิน"))
        plan_layout.addWidget(self.plan_aircraft_rows_host)
        add_aircraft_row = QHBoxLayout()
        self.add_plan_aircraft_btn = QPushButton("+ เพิ่มเครื่องบิน")
        self.add_plan_aircraft_btn.setObjectName("SecondaryButton")
        self.add_plan_aircraft_btn.clicked.connect(
            lambda _checked=False: self._add_plan_aircraft_row()
        )
        add_aircraft_row.addWidget(self.add_plan_aircraft_btn)
        add_aircraft_row.addStretch(1)
        plan_layout.addLayout(add_aircraft_row)

        plan_layout.addWidget(
            QLabel("แผนการบิน (Takeoff → Climb → Cruise → Descent → Attack → RTB)")
        )
        takeoff_row = QHBoxLayout()
        self.takeoff_lat = _coord_spin()
        self.takeoff_lng = _coord_spin(100.0)
        self.use_wing_takeoff_btn = QPushButton("ใช้พิกัดกองบิน")
        self.use_wing_takeoff_btn.setObjectName("SecondaryButton")
        self.use_wing_takeoff_btn.clicked.connect(self._apply_wing_takeoff_coords)
        takeoff_row.addWidget(self.takeoff_lat)
        takeoff_row.addWidget(self.takeoff_lng)
        takeoff_row.addWidget(self.use_wing_takeoff_btn)
        plan_layout.addWidget(_field_row("Takeoff (LAT/LNG)", _wrap_layout(takeoff_row)))

        alt_row = QHBoxLayout()
        self.cruise_altitude_ft = _int_spin(25000, 55000)
        self.ingress_altitude_ft = _int_spin(500, 40000)
        self.target_altitude_ft = _int_spin(500, 20000)
        alt_row.addWidget(QLabel("Cruise"))
        alt_row.addWidget(self.cruise_altitude_ft)
        alt_row.addWidget(QLabel("Ingress"))
        alt_row.addWidget(self.ingress_altitude_ft)
        alt_row.addWidget(QLabel("Fly-through"))
        alt_row.addWidget(self.target_altitude_ft)
        alt_row.addStretch(1)
        plan_layout.addWidget(_field_row("ความสูง (ft)", _wrap_layout(alt_row)))

        rate_row = QHBoxLayout()
        self.climb_rate_ft_min = _int_spin(3000, 12000)
        self.descent_rate_ft_min = _int_spin(2000, 8000)
        rate_row.addWidget(QLabel("Climb"))
        rate_row.addWidget(self.climb_rate_ft_min)
        rate_row.addWidget(QLabel("ft/min"))
        rate_row.addWidget(QLabel("Descent"))
        rate_row.addWidget(self.descent_rate_ft_min)
        rate_row.addWidget(QLabel("ft/min"))
        rate_row.addStretch(1)
        plan_layout.addWidget(_field_row("อัตราขึ้น/ลง", _wrap_layout(rate_row)))

        speed_row = QHBoxLayout()
        self.cruise_speed_kt = _int_spin(150, 600)
        self.climb_speed_kt = _int_spin(120, 500)
        self.descent_speed_kt = _int_spin(120, 500)
        self.ingress_speed_kt = _int_spin(100, 450)
        speed_row.addWidget(QLabel("Cruise"))
        speed_row.addWidget(self.cruise_speed_kt)
        speed_row.addWidget(QLabel("Climb"))
        speed_row.addWidget(self.climb_speed_kt)
        speed_row.addWidget(QLabel("Desc"))
        speed_row.addWidget(self.descent_speed_kt)
        speed_row.addWidget(QLabel("Ingress"))
        speed_row.addWidget(self.ingress_speed_kt)
        speed_row.addWidget(QLabel("kt"))
        speed_row.addStretch(1)
        plan_layout.addWidget(_field_row("ความเร็ว (kt)", _wrap_layout(speed_row)))

        realism_row = QHBoxLayout()
        self.bank_angle_deg = _int_spin(10, 45)
        self.turn_mode = QComboBox()
        self.turn_mode.addItem("Fly-by", "fly_by")
        self.turn_mode.addItem("Fly-over", "fly_over")
        self.auto_toc_tod = QCheckBox("Auto TOC/TOD")
        self.auto_toc_tod.setChecked(True)
        realism_row.addWidget(QLabel("Bank"))
        realism_row.addWidget(self.bank_angle_deg)
        realism_row.addWidget(QLabel("°"))
        realism_row.addWidget(self.turn_mode)
        realism_row.addWidget(self.auto_toc_tod)
        realism_row.addStretch(1)
        plan_layout.addWidget(_field_row("เส้นทางสมจริง", _wrap_layout(realism_row)))

        ingress_row = QHBoxLayout()
        self.use_ingress_bearing = QCheckBox("กำหนดทิศเข้าพื้นที่")
        self.ingress_bearing = QSpinBox()
        self.ingress_bearing.setRange(0, 359)
        self.ingress_bearing.setSuffix("°")
        self.ingress_bearing.setEnabled(False)
        self.use_ingress_bearing.toggled.connect(self.ingress_bearing.setEnabled)
        self.calc_ingress_btn = QPushButton("คำนวณทิศจาก Takeoff")
        self.calc_ingress_btn.setObjectName("SecondaryButton")
        self.calc_ingress_btn.clicked.connect(self._calculate_ingress_bearing)
        ingress_row.addWidget(self.use_ingress_bearing)
        ingress_row.addWidget(self.ingress_bearing)
        ingress_row.addWidget(self.calc_ingress_btn)
        ingress_row.addStretch(1)
        plan_layout.addWidget(_field_row("Ingress", _wrap_layout(ingress_row)))

        self.ingress_offset_m = _int_spin(5000, 200000)
        plan_layout.addWidget(_field_row("ระยะ Ingress (m)", self.ingress_offset_m))

        self._plan_waypoint_rows: list[_PlanWaypointRow] = []
        self.plan_waypoint_rows_host = QWidget()
        self.plan_waypoint_rows_layout = QVBoxLayout(self.plan_waypoint_rows_host)
        self.plan_waypoint_rows_layout.setContentsMargins(0, 0, 0, 0)
        self.plan_waypoint_rows_layout.setSpacing(6)
        plan_layout.addWidget(QLabel("จุดบินผ่าน (Fly-through) · Alt=0 ใช้ Cruise"))
        plan_layout.addWidget(self.plan_waypoint_rows_host)
        waypoint_actions = QHBoxLayout()
        self.add_plan_waypoint_btn = QPushButton("+ เพิ่มจุดบินผ่าน")
        self.add_plan_waypoint_btn.setObjectName("SecondaryButton")
        self.add_plan_waypoint_btn.clicked.connect(
            lambda _checked=False: self._add_plan_waypoint_row()
        )
        waypoint_actions.addWidget(self.add_plan_waypoint_btn)
        waypoint_actions.addStretch(1)
        plan_layout.addLayout(waypoint_actions)

        self.return_enabled = QCheckBox("บินกลับฐาน (RTB) — ใช้เส้นทางย้อนกลับอัตโนมัติถ้าไม่กำหนดจุด")
        plan_layout.addWidget(self.return_enabled)

        self._plan_return_waypoint_rows: list[_PlanWaypointRow] = []
        self.plan_return_waypoint_rows_host = QWidget()
        self.plan_return_waypoint_rows_layout = QVBoxLayout(
            self.plan_return_waypoint_rows_host
        )
        self.plan_return_waypoint_rows_layout.setContentsMargins(0, 0, 0, 0)
        self.plan_return_waypoint_rows_layout.setSpacing(6)
        plan_layout.addWidget(QLabel("จุดบินกลับ (RTB) · ว่าง = ย้อน outbound"))
        plan_layout.addWidget(self.plan_return_waypoint_rows_host)
        return_actions = QHBoxLayout()
        self.add_plan_return_waypoint_btn = QPushButton("+ เพิ่มจุด RTB")
        self.add_plan_return_waypoint_btn.setObjectName("SecondaryButton")
        self.add_plan_return_waypoint_btn.clicked.connect(
            lambda _checked=False: self._add_plan_return_waypoint_row()
        )
        self.preview_flight_btn = QPushButton("คำนวณแผนการบิน")
        self.preview_flight_btn.setObjectName("SecondaryButton")
        self.preview_flight_btn.clicked.connect(self._preview_flight_plan)
        return_actions.addWidget(self.add_plan_return_waypoint_btn)
        return_actions.addWidget(self.preview_flight_btn)
        return_actions.addStretch(1)
        plan_layout.addLayout(return_actions)

        self.flight_plan_summary = QLabel(
            "กำหนด Takeoff, จุดบินผ่าน และทิศ Ingress แล้วกดคำนวณแผนการบิน"
        )
        self.flight_plan_summary.setObjectName("FormSectionSubtitle")
        self.flight_plan_summary.setWordWrap(True)
        plan_layout.addWidget(self.flight_plan_summary)

        self._apply_sim_flight_defaults(include_waypoint=True)

        plan_actions = QHBoxLayout()
        self.save_plan_btn = QPushButton("บันทึกแผน")
        self.save_plan_btn.setObjectName("PrimaryButton")
        self.save_plan_btn.clicked.connect(self._save_deployment_plan)
        self.clear_plan_btn = QPushButton("ล้างแผน")
        self.clear_plan_btn.setObjectName("GhostButton")
        self.clear_plan_btn.clicked.connect(self._clear_deployment_plan)
        plan_actions.addWidget(self.save_plan_btn)
        plan_actions.addWidget(self.clear_plan_btn)
        plan_actions.addStretch(1)
        plan_layout.addLayout(plan_actions)

        self.plan_status = QLabel("ยังไม่ได้บันทึกแผนสำหรับ Target นี้")
        self.plan_status.setObjectName("FormSectionSubtitle")
        self.plan_status.setWordWrap(True)
        plan_layout.addWidget(self.plan_status)
        body_layout.addWidget(plan_card)

        body_layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

    def set_scenario(self, scenario_id: str | None) -> None:
        self._scenario_id = scenario_id
        self._clear_ai_product_state()
        self._recalculate()

    def select_target(self, target_id: str) -> None:
        self._selected_target_id = target_id
        self._clear_ai_product_state()
        self._recalculate()

    def reload_deployment_plan_for_target(self, target_id: str) -> None:
        if self._selected_target_id != target_id:
            return
        self._load_deployment_plan()

    def _recalculate(self) -> None:
        self._clear_range_bars()
        if not self._scenario_id:
            self._set_empty_state("ยังไม่มี scenario ที่ใช้งาน")
            return
        if not self._selected_target_id:
            self._set_empty_state("เลือก Target Card จาก Target Stack ด้านซ้าย")
            return

        detail = self.target_service.get_target_detail(self._selected_target_id)
        if detail is None:
            self._set_empty_state("ไม่พบ Target Card")
            return

        card = detail.card
        using_pending_form = False
        snapshot: TargetCalculationSnapshot | None = None
        if self._target_inputs_provider is not None:
            snapshot = self._target_inputs_provider(self._selected_target_id)
            if snapshot is not None:
                card = _merge_card_profile(card, snapshot.profile)
                using_pending_form = True

        context = build_target_context(self._selected_target_id, card)
        mission = context.mission
        self._mission_cep_ft = mission.cep_ft
        self.target_hero.setText(context.label)
        meta_lines = [context.target_element]
        if card.material_class and card.material_class != "UNKNOWN":
            meta_lines[0] = f"{meta_lines[0]} · {card.material_class}"
        meta_lines.append(
            f"σ {mission.cep_ft:.0f}+{mission.tle_ft:.1f} ft · "
            f"{mission.target_length_ft:.0f}×{mission.target_width_ft:.0f} ft"
        )
        if card.target_description:
            desc = card.target_description.strip()
            if len(desc) > 140:
                desc = desc[:137] + "…"
            meta_lines.append(desc)
        self.target_meta.setText("\n".join(meta_lines))
        self._input_labels["cep"].setText(f"{mission.cep_ft:.1f} ft")
        self._input_labels["tle"].setText(f"{mission.tle_ft:.1f} ft")
        self._input_labels["size"].setText(
            f"{mission.target_length_ft:.0f}×{mission.target_width_ft:.0f} ft"
        )
        self._input_labels["pk"].setText(f"{mission.pk_desired:.2f}")
        self._input_labels["angle"].setText(f"{mission.impact_angle_deg:.0f}°")
        self._input_labels["burial"].setText(f"{mission.burial_pct:.0f}%")
        warnings = list(context.warnings)
        if using_pending_form:
            warnings.insert(
                0,
                "ใช้ค่าจากฟอร์ม Target Stack ปัจจุบัน (ยังไม่บันทึกก็คำนวณได้)",
            )
        self.warnings_label.setText(" · ".join(warnings) if warnings else "")

        target_points = _collect_target_points(detail, snapshot)
        self._manual_product_selection = bool(card.selected_product_id) or any(
            point_product_id for *_, point_product_id in target_points if point_product_id
        )
        if not target_points:
            self._point_results = []
            self._populate_coord_selector()
            self._target_lat = None
            self._target_lng = None
            self._clear_wing_results(
                "เป้าหมายยังไม่มีพิกัด — เพิ่มพิกัดใน Target Stack หรือเลือกจากแผนที่"
            )
            self._load_deployment_plan()
            self.rank_table.setRowCount(0)
            self._update_top_product([])
            self._populate_recommendations([], mission.pk_desired)
            self.recalc_status.setText("ยังไม่มีพิกัดเป้าหมายสำหรับคำนวณ")
            return

        products = self.wing_data_service.list_products(self._scenario_id)
        if not products:
            self._point_results = []
            self._populate_coord_selector()
            self._sync_selected_product_combo(None, [], None)
            self.rank_table.setRowCount(0)
            self._update_top_product([])
            self._populate_recommendations([], mission.pk_desired)
            self.recalc_status.setText(
                "ไม่มีสินค้าใน Database — เพิ่มสินค้าในแท็บ Database > ข้อมูลสินค้า"
            )
            return

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
        self._sync_selected_product_combo(card, products, None)
        card_selected_product_id = card.selected_product_id
        point_results: list[_PointWeaponeeringResult] = []
        for label, lat, lng, is_primary, coordinate_id, point_product_id in target_points:
            selected_product_id = point_product_id or card_selected_product_id
            results = apply_selected_product_rank(
                rank_weapons(mission, weapons),
                selected_product_id,
            )
            ranked_wings = None
            if self._scenario_id:
                ranked_wings = self.wing_data_service.find_wings_by_distance(
                    self._scenario_id,
                    lat,
                    lng,
                )
            point_results.append(
                _PointWeaponeeringResult(
                    key=_point_key(label, lat, lng),
                    label=label,
                    lat=lat,
                    lng=lng,
                    is_primary=is_primary,
                    results=results,
                    mission=mission,
                    coordinate_id=coordinate_id,
                    selected_product_id=selected_product_id,
                    ranked_wings=ranked_wings,
                )
            )

        self._point_results = point_results
        previous_key = self._active_point_key
        self._populate_coord_selector(previous_key)
        active = self._active_point_result()
        if active is None:
            self._set_empty_state("ไม่พบผลคำนวณต่อพิกัด")
            return
        self._sync_selected_product_combo(card, products, active.selected_product_id)
        self._display_point_result(active)
        self._load_deployment_plan()
        suffix = " · จากฟอร์มปัจจุบัน" if using_pending_form else ""
        manual_suffix = " · สินค้าหลักเลือกแล้ว" if self._manual_product_selection else ""
        self.recalc_status.setText(
            f"คำนวณแล้ว {len(active.results)} สินค้า × {len(point_results)} พิกัด"
            f" · Desired PK {mission.pk_desired:.2f}{suffix}{manual_suffix}"
        )
        self.ranking_completed.emit()

    def _active_point_result(self) -> _PointWeaponeeringResult | None:
        if not self._point_results:
            return None
        if self._active_point_key:
            for point in self._point_results:
                if point.key == self._active_point_key:
                    return point
        return self._point_results[0]

    def _populate_coord_selector(self, preferred_key: str | None = None) -> None:
        self.coord_selector.blockSignals(True)
        self.coord_selector.clear()
        for point in self._point_results:
            primary_suffix = " ★" if point.is_primary else ""
            self.coord_selector.addItem(
                f"{point.label} {point.lat:.4f},{point.lng:.4f}{primary_suffix}",
                point.key,
            )
        if preferred_key:
            index = self.coord_selector.findData(preferred_key)
            if index >= 0:
                self.coord_selector.setCurrentIndex(index)
        elif self.coord_selector.count():
            self.coord_selector.setCurrentIndex(0)
        self.coord_selector.blockSignals(False)
        if self.coord_selector.count():
            self._active_point_key = str(self.coord_selector.currentData())
        else:
            self._active_point_key = None

    def _on_coord_selector_changed(self, _index: int) -> None:
        key = self.coord_selector.currentData()
        if not key:
            return
        self._active_point_key = str(key)
        point = self._active_point_result()
        if point is None:
            return
        detail = self.target_service.get_target_detail(self._selected_target_id or "")
        card = detail.card if detail is not None else None
        products = (
            self.wing_data_service.list_products(self._scenario_id)
            if self._scenario_id
            else []
        )
        self._sync_selected_product_combo(card, products, point.selected_product_id)
        self._display_point_result(point)

    def _display_point_result(self, point: _PointWeaponeeringResult) -> None:
        self._target_lat = point.lat
        self._target_lng = point.lng
        self._populate_rank_table(point.results)
        self._populate_recommendations(point.results, point.mission.pk_desired)
        if point.ranked_wings:
            nearest = point.ranked_wings[0]
            self.nearest_wing_label.setText(
                f"[{point.label}] กองบินใกล้ที่สุด: {nearest.wing_name} · "
                f"{nearest.distance_km:.1f} km ({nearest.distance_nm:.1f} nm)\n"
                f"พิกัด: {point.lat:.5f}, {point.lng:.5f}"
            )
            self.wing_table.setRowCount(len(point.ranked_wings))
            for row_index, row in enumerate(point.ranked_wings):
                values = [
                    str(row.rank),
                    row.wing_name,
                    f"{row.distance_km:.1f}",
                    f"{row.distance_nm:.1f}",
                    f"{row.map_lat:.5f}",
                    f"{row.map_lng:.5f}",
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if col == 0 and row.rank == 1:
                        item.setForeground(Qt.GlobalColor.green)
                    self.wing_table.setItem(row_index, col, item)
        else:
            self._clear_wing_results(
                f"[{point.label}] ไม่พบกองบินที่มีพิกัด — เพิ่มกองบินใน Database"
            )

    def _clear_top_product_image(self) -> None:
        self.top_product_image.clear_product()

    def _update_top_product_image(self, product_name: str) -> None:
        self.top_product_image.set_product(product_name)
        QTimer.singleShot(0, self.top_product_image.refresh_display)

    def _update_top_product(self, results) -> None:
        if not results:
            self.top_product_hero.setText("ยังไม่มีสินค้าที่คำนวณ")
            self.top_product_stats.setText("เลือก Target และกด คำนวณใหม่")
            self._clear_top_product_image()
            self._update_laser_designation(None)
            self._update_weapon_effects(visible=False)
            self._update_circular_error(visible=False)
            return
        best = results[0]
        selection_note = " · เลือกแล้ว" if self._manual_product_selection else ""
        self.top_product_hero.setText(f"#{best.rank} {best.product_name}{selection_note}")
        self.top_product_stats.setText(
            f"Pd {best.pd_base:.3f} · PK₁ {best.pk_single:.3f} · "
            f"N {best.n_required} · PKₙ {best.pk_n:.3f} · {best.weight_pounds:.0f} lb"
        )
        self._update_top_product_image(best.product_name)
        self._update_laser_designation(best.product_name)
        self._update_weapon_effects(visible=True)
        self._update_circular_error(visible=True, product_name=best.product_name)

    def _update_laser_designation(self, product_name: str | None) -> None:
        info = designation_info_for(product_name or "")
        if info is None:
            self.laser_designation_box.clear()
            self.laser_designation_box.setVisible(False)
            return
        lines = [info.title, info.intro]
        for index, flow in enumerate(info.workflows, start=1):
            lines.append(f"{index}) {flow.label_th} ({flow.label_en}): {flow.summary}")
        if info.weather_limitation:
            lines.append(info.weather_limitation)
        self.laser_designation_box.setText("\n".join(lines))
        self.laser_designation_box.setVisible(True)

    def _update_weapon_effects(self, *, visible: bool) -> None:
        if not visible:
            self.weapon_effects_box.clear()
            self.weapon_effects_box.setVisible(False)
            return
        info = weapon_effects_info()
        lines = [info.title, info.intro]
        for index, effect in enumerate(info.effects, start=1):
            lines.append(
                f"{index}) {effect.label_th} ({effect.label_en}): {effect.summary}"
            )
        self.weapon_effects_box.setText("\n".join(lines))
        self.weapon_effects_box.setVisible(True)

    def _update_circular_error(self, *, visible: bool, product_name: str = "") -> None:
        if not visible:
            self.circular_error_box.clear()
            self.circular_error_box.setVisible(False)
            return
        info = circular_error_info(
            ce50_ft=self._mission_cep_ft, product_name=product_name
        )
        lines = [info.title, info.intro]
        for index, metric in enumerate(info.metrics, start=1):
            lines.append(
                f"{index}) {metric.label_th} ({metric.label_en}): {metric.summary}"
            )
        if info.ce50_ft is not None and info.ce90_ft is not None:
            source = (
                "ความแม่นยำระบบอาวุธ"
                if info.cep_source == "weapon"
                else "Pilot CEP"
            )
            lines.append(
                f"CE50 {info.ce50_ft:.0f} ft · CE90 {info.ce90_ft:.0f} ft · จาก {source}"
            )
        if info.application:
            lines.append(info.application)
        self.circular_error_box.setText("\n".join(lines))
        self.circular_error_box.setVisible(True)

    def _populate_recommendations(self, results, pk_desired: float) -> None:
        while self.recommendations_layout.count() > 1:
            item = self.recommendations_layout.takeAt(1)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not results:
            empty = QLabel("ไม่มีผลลัพธ์การคำนวณ")
            empty.setObjectName("FormSectionSubtitle")
            empty.setWordWrap(True)
            self.recommendations_layout.addWidget(empty)
            return

        for row in results[:5]:
            prefix = "★ " if row.rank == 1 else ""
            text = (
                f"{prefix}#{row.rank} {row.product_name} · "
                f"Pd{row.pd_base:.3f} · N{row.n_required} · PKₙ{row.pk_n:.3f}"
            )
            label = QLabel(text)
            label.setWordWrap(True)
            if row.rank == 1:
                label.setStyleSheet("color: #67e8f9; font-size: 10px; font-weight: 700;")
            else:
                label.setStyleSheet("color: #9fb0c2; font-size: 10px;")
            self.recommendations_layout.addWidget(label)

        best = results[0]
        if self._manual_product_selection:
            summary = QLabel(
                f"ใช้ {best.product_name} (เลือกแล้ว) · Desired PK {pk_desired:.2f}"
            )
        else:
            summary = QLabel(
                f"แนะนำ {best.product_name} เพื่อบรรลุ Desired PK {pk_desired:.2f}"
            )
        summary.setStyleSheet("color: #d7dee8; font-size: 10px;")
        summary.setWordWrap(True)
        self.recommendations_layout.addWidget(summary)

    def _set_empty_state(self, message: str) -> None:
        self.target_hero.setText("—")
        self.target_meta.setText(message)
        for label in self._input_labels.values():
            label.setText("—")
        self.warnings_label.setText("")
        self._point_results = []
        self._active_point_key = None
        self.coord_selector.blockSignals(True)
        self.coord_selector.clear()
        self.coord_selector.blockSignals(False)
        self._target_lat = None
        self._target_lng = None
        self._clear_wing_results(message)
        self._reset_deployment_plan_form("ยังไม่ได้บันทึกแผนสำหรับ Target นี้")
        self.rank_table.setRowCount(0)
        self._update_top_product([])
        self._populate_recommendations([], 0.90)
        self._clear_ai_product_state()
        self.recalc_status.setText(message)

    def _search_nearest_wing(self) -> None:
        point = self._active_point_result()
        if point is not None and point.ranked_wings is not None:
            self._display_point_result(point)
            return
        if not self._scenario_id:
            self._clear_wing_results("ยังไม่มี scenario ที่ใช้งาน")
            return
        if self._target_lat is None or self._target_lng is None:
            self._clear_wing_results(
                "เป้าหมายยังไม่มีพิกัด — กรอก LAT/LNG ใน Target Stack หรือเลือกจากแผนที่"
            )
            return

        ranked = self.wing_data_service.find_wings_by_distance(
            self._scenario_id,
            self._target_lat,
            self._target_lng,
        )
        if not ranked:
            self._clear_wing_results(
                "ไม่พบกองบินที่มีพิกัด — เพิ่มกองบินในแท็บ Database > ข้อมูลกองบิน"
            )
            return

        nearest = ranked[0]
        self.nearest_wing_label.setText(
            f"กองบินใกล้ที่สุด: {nearest.wing_name} · "
            f"{nearest.distance_km:.1f} km ({nearest.distance_nm:.1f} nm)\n"
            f"พิกัดเป้าหมาย: {self._target_lat:.5f}, {self._target_lng:.5f}"
        )
        self.wing_table.setRowCount(len(ranked))
        for row_index, row in enumerate(ranked):
            values = [
                str(row.rank),
                row.wing_name,
                f"{row.distance_km:.1f}",
                f"{row.distance_nm:.1f}",
                f"{row.map_lat:.5f}",
                f"{row.map_lng:.5f}",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0 and row.rank == 1:
                    item.setForeground(Qt.GlobalColor.green)
                self.wing_table.setItem(row_index, col, item)

    def _clear_wing_results(self, message: str) -> None:
        self.nearest_wing_label.setText(message)
        self.wing_table.setRowCount(0)

    def _sync_selected_product_combo(
        self,
        card: TargetCard | None,
        products,
        selected_product_id: str | None = None,
    ) -> None:
        self.selected_product_combo.blockSignals(True)
        self.selected_product_combo.clear()
        self.selected_product_combo.addItem("— อัตโนมัติ (อันดับ JMEM) —", None)
        for product in products:
            self.selected_product_combo.addItem(product.product_name, product.id)
        resolved = selected_product_id
        if not resolved and card is not None:
            resolved = card.selected_product_id
        if resolved:
            index = self.selected_product_combo.findData(resolved)
            self.selected_product_combo.setCurrentIndex(index if index >= 0 else 0)
        else:
            self.selected_product_combo.setCurrentIndex(0)
        self.selected_product_combo.blockSignals(False)

    def _product_id_from_rank_row(self, row_index: int) -> str | None:
        if row_index < 0:
            return None
        item = self.rank_table.item(row_index, 1)
        if item is None:
            return None
        product_id = item.data(Qt.ItemDataRole.UserRole)
        return str(product_id) if product_id else None

    def _save_selected_product(
        self,
        product_id: str | None,
        *,
        coordinate_id: str | None = None,
    ) -> None:
        if not self._selected_target_id:
            return
        try:
            if coordinate_id:
                self.target_service.set_coordinate_selected_product(
                    coordinate_id,
                    product_id,
                )
            else:
                detail = self.target_service.get_target_detail(self._selected_target_id)
                if detail is None:
                    return
                card = detail.card
                profile = replace(
                    TargetProfileFields.from_card(card),
                    selected_product_id=product_id,
                )
                self.target_service.update_target_card(
                    UpdateTargetCardRequest(
                        target_card_id=self._selected_target_id,
                        label=card.label,
                        priority_score=card.priority_score,
                        complexity_score=card.complexity_score,
                        profile=profile,
                    )
                )
        except ValueError as exc:
            QMessageBox.warning(self, "Guardrail", str(exc))
            return
        self.weaponeering_changed.emit()
        self._recalculate()

    def _on_selected_product_combo_changed(self, _index: int) -> None:
        if not self._selected_target_id or self.selected_product_combo.signalsBlocked():
            return
        product_id = self.selected_product_combo.currentData()
        point = self._active_point_result()
        current = point.selected_product_id if point is not None else None
        selected = str(product_id) if product_id else None
        if current == selected:
            return
        self._save_selected_product(
            selected,
            coordinate_id=point.coordinate_id if point is not None else None,
        )

    def _on_use_table_row_for_selection(self) -> None:
        product_id = self._product_id_from_rank_row(self.rank_table.currentRow())
        if not product_id:
            QMessageBox.information(self, "เลือกสินค้า", "เลือกแถวในตารางก่อน")
            return
        index = self.selected_product_combo.findData(product_id)
        if index >= 0:
            self.selected_product_combo.setCurrentIndex(index)
        else:
            point = self._active_point_result()
            self._save_selected_product(
                product_id,
                coordinate_id=point.coordinate_id if point is not None else None,
            )

    def _on_rank_table_double_clicked(self, _index) -> None:
        self._on_use_table_row_for_selection()

    def _on_clear_product_selection(self) -> None:
        if self.selected_product_combo.currentData() is None:
            return
        self.selected_product_combo.setCurrentIndex(0)

    def _clear_ai_product_state(self) -> None:
        if self._ai_product_analyzing:
            self._set_ai_product_analyzing(False)
        self._ai_product_recommendation = None
        self._ai_product_summary = None
        self.ai_apply_btn.setEnabled(False)
        self.ai_product_summary.setText(
            "กด AI วิเคราะห์สินค้า หลังคำนวณ JMEM — "
            "ระบบจะพิจารณา Pd, N, Desired PK, ค่าใช้จ่าย และสต็อก"
        )

    def _stock_by_product(self) -> dict[str, int]:
        if not self._scenario_id:
            return {}
        totals: dict[str, int] = {}
        for row in self.wing_data_service.list_inventory(self._scenario_id):
            totals[row.product_id] = totals.get(row.product_id, 0) + int(row.quantity)
        return totals

    def _ai_engine_label(self) -> str:
        if self.ai_service is None:
            return "ไม่ได้เชื่อม AI"
        mode = self.ai_service.adapter_mode
        labels = {
            "rule_based": "Rule-based (ในเครื่อง — ไม่เรียก LLM)",
            "local_model": "LLM ในเครื่อง (Ollama / local_model)",
            "openai": "LLM ภายนอก (OpenAI-compatible)",
            "gemini": "LLM ภายนอก (Gemini)",
            "disabled": "ปิดใช้งาน",
            "sandboxed": "Sandboxed",
        }
        return labels.get(mode, mode)

    def _refresh_ai_product_summary(self) -> None:
        recommendation = self._ai_product_recommendation
        if recommendation is None:
            self._clear_ai_product_state()
            return
        lines = [
            f"เครื่องมือ: {self._ai_engine_label()}",
            recommendation.rationale,
            f"ความมั่นใจ: {recommendation.confidence}",
        ]
        if recommendation.mission_cost > 0:
            lines.append(
                f"ค่าใช้จ่ายภารกิจ ~{recommendation.mission_cost:,.0f} บาท "
                f"(N={recommendation.n_required})"
            )
        for factor in recommendation.factors[:4]:
            lines.append(f"• {factor}")
        if self._ai_product_summary:
            lines.extend(["", "AI:", self._ai_product_summary.strip()])
        self.ai_product_summary.setText("\n".join(lines))
        self.ai_apply_btn.setEnabled(True)

    def _set_ai_product_analyzing(self, analyzing: bool) -> None:
        self._ai_product_analyzing = analyzing
        if analyzing:
            self.ai_analyze_btn.setEnabled(False)
            self.ai_apply_btn.setEnabled(False)
            self.ai_analyze_btn.setText(_AI_ANALYZE_LOADING_LABEL)
            self.ai_product_summary.setText(
                "กำลังวิเคราะห์สินค้าด้วย AI — โปรดรอสักครู่\n"
                "• คำนวณคะแนน JMEM และค่าใช้จ่าย\n"
                "• ตรวจสอบสต็อกคลัง\n"
                "• สร้างคำอธิบาย AI"
            )
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            return

        self.ai_analyze_btn.setText(_AI_ANALYZE_BTN_LABEL)
        self.ai_analyze_btn.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def _on_ai_analyze_product(self) -> None:
        if self._ai_product_analyzing:
            return
        if not self._selected_target_id or not self._scenario_id:
            QMessageBox.information(self, "AI วิเคราะห์", "เลือก Target และคำนวณ JMEM ก่อน")
            return
        active = self._active_point_result()
        if active is None or not active.results:
            QMessageBox.information(self, "AI วิเคราะห์", "ยังไม่มีผลคำนวณสินค้า")
            return
        if self.ai_service is None or not self.ai_service.is_enabled():
            QMessageBox.information(
                self,
                "AI วิเคราะห์",
                "เปิดใช้งาน AI ใน Settings ก่อน (rule_based / local_model / openai)",
            )
            return

        detail = self.target_service.get_target_detail(self._selected_target_id)
        if detail is None:
            QMessageBox.warning(self, "AI วิเคราะห์", "ไม่พบ Target Card")
            return

        products = self.wing_data_service.list_products(self._scenario_id)
        if not products:
            QMessageBox.information(self, "AI วิเคราะห์", "ไม่มีสินค้าให้วิเคราะห์")
            return

        self._set_ai_product_analyzing(True)
        QApplication.processEvents()
        QTimer.singleShot(0, self._execute_ai_analyze_product)

    def _execute_ai_analyze_product(self) -> None:
        try:
            if not self._selected_target_id or not self._scenario_id:
                return
            active = self._active_point_result()
            if active is None or not active.results:
                return
            detail = self.target_service.get_target_detail(self._selected_target_id)
            if detail is None:
                return
            products = self.wing_data_service.list_products(self._scenario_id)
            if not products:
                return

            recommendation = recommend_product(
                detail.card,
                active.mission,
                list(active.results),
                products,
                stock_by_product=self._stock_by_product(),
            )
            if recommendation is None:
                QMessageBox.information(self, "AI วิเคราะห์", "ไม่สามารถสร้างคำแนะนำได้")
                self._clear_ai_product_state()
                return

            self._ai_product_recommendation = recommendation
            self._ai_product_summary = None
            prompt = product_analysis_prompt(
                recommendation,
                target_label=detail.card.label,
                target_type=detail.card.target_type,
            )
            interaction = self.ai_service.analyze_product_selection(
                self._scenario_id,
                self._selected_target_id,
                analysis_prompt=prompt,
            )
            if interaction is not None and interaction.sanitized_output.strip():
                self._ai_product_summary = interaction.sanitized_output.strip()
            self._refresh_ai_product_summary()
        finally:
            self._set_ai_product_analyzing(False)
            if self._ai_product_recommendation is not None:
                self.ai_apply_btn.setEnabled(True)

    def _on_ai_apply_product_recommendation(self) -> None:
        recommendation = self._ai_product_recommendation
        if recommendation is None:
            QMessageBox.information(self, "ใช้คำแนะนำ AI", "กด AI วิเคราะห์สินค้าก่อน")
            return
        index = self.selected_product_combo.findData(recommendation.product_id)
        if index >= 0:
            self.selected_product_combo.setCurrentIndex(index)
        else:
            point = self._active_point_result()
            self._save_selected_product(
                recommendation.product_id,
                coordinate_id=point.coordinate_id if point is not None else None,
            )

    def _populate_rank_table(self, results) -> None:
        self.rank_table.setRowCount(len(results))
        self._clear_range_bars()
        self._update_top_product(results)
        for row_index, row in enumerate(results):
            values = [
                str(row.rank),
                row.product_name,
                f"{row.pd_base:.3f}",
                f"{row.pk_single:.3f}",
                str(row.n_required),
                f"{row.pk_n:.3f}",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 1:
                    item.setData(Qt.ItemDataRole.UserRole, row.product_id)
                if col == 0 and row.rank == 1:
                    item.setForeground(Qt.GlobalColor.green)
                self.rank_table.setItem(row_index, col, item)

            if row_index >= 5:
                continue

            bar_row = QWidget()
            bar_layout = QHBoxLayout(bar_row)
            bar_layout.setContentsMargins(0, 0, 0, 0)
            bar_layout.setSpacing(6)
            name = QLabel(f"#{row.rank}")
            name.setFixedWidth(24)
            name.setObjectName("FormFieldLabel")
            bar = _RangeZonesBar()
            bar.set_ranges(
                row.range_red_ft,
                row.range_orange_max_ft,
                row.range_yellow_dark_ft,
                row.range_yellow_light_ft,
            )
            bar_layout.addWidget(name)
            bar_layout.addWidget(bar, stretch=1)
            km_label = QLabel(
                " · ".join(
                    (
                        format_range_m_ft(row.range_red_ft),
                        format_orange_range_m_ft(
                            row.range_orange_min_ft,
                            row.range_orange_max_ft,
                        ),
                        format_range_m_ft(row.range_yellow_dark_ft),
                        format_range_m_ft(row.range_yellow_light_ft),
                    )
                )
            )
            km_label.setStyleSheet("color:#6b7f96; font-size:9px;")
            bar_layout.addWidget(km_label)
            self.range_bars_layout.addWidget(bar_row)

    def _clear_range_bars(self) -> None:
        while self.range_bars_layout.count():
            item = self.range_bars_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _refresh_plan_wing_combo(self, selected_wing_id: str | None = None) -> None:
        self.plan_wing.blockSignals(True)
        self.plan_wing.clear()
        self.plan_wing.addItem("(เลือกกองบิน)", "")
        if self._scenario_id:
            for wing in self.wing_data_service.list_wings(self._scenario_id):
                self.plan_wing.addItem(wing.wing_name, wing.id)
        if selected_wing_id:
            idx = self.plan_wing.findData(selected_wing_id)
            if idx >= 0:
                self.plan_wing.setCurrentIndex(idx)
        self.plan_wing.blockSignals(False)

    def _refresh_plan_unit_combo(
        self,
        wing_id: str | None,
        selected_unit_id: str | None = None,
    ) -> None:
        self.plan_unit.blockSignals(True)
        self.plan_unit.clear()
        self.plan_unit.addItem("(เลือกหน่วยบิน)", "")
        if self._scenario_id and wing_id:
            for unit in self.wing_data_service.list_flying_units(self._scenario_id):
                if unit.wing_id == wing_id:
                    self.plan_unit.addItem(unit.unit_name, unit.id)
        if selected_unit_id:
            idx = self.plan_unit.findData(selected_unit_id)
            if idx >= 0:
                self.plan_unit.setCurrentIndex(idx)
        self.plan_unit.blockSignals(False)

    def _clear_plan_aircraft_rows(self) -> None:
        while self.plan_aircraft_rows_layout.count():
            item = self.plan_aircraft_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._plan_aircraft_rows.clear()

    def _current_plan_wing_unit(self) -> tuple[str | None, str | None]:
        wing_id = self.plan_wing.currentData() or None
        unit_id = self.plan_unit.currentData() or None
        return wing_id, unit_id

    def _refresh_plan_aircraft_rows(self) -> None:
        wing_id, unit_id = self._current_plan_wing_unit()
        for row in self._plan_aircraft_rows:
            row.populate_options(
                self.wing_data_service,
                self._scenario_id,
                wing_id,
                unit_id,
            )

    def _add_plan_aircraft_row(
        self,
        aircraft_id: str | None = None,
        aircraft_count: int = 1,
    ) -> None:
        row = _PlanAircraftRow()
        row.remove_btn.clicked.connect(
            lambda _checked=False, r=row: self._remove_plan_aircraft_row(r)
        )
        wing_id, unit_id = self._current_plan_wing_unit()
        row.populate_options(
            self.wing_data_service,
            self._scenario_id,
            wing_id,
            unit_id,
            aircraft_id,
        )
        if aircraft_id:
            row.count.setValue(aircraft_count)
        self._plan_aircraft_rows.append(row)
        self.plan_aircraft_rows_layout.addWidget(row)

    def _remove_plan_aircraft_row(self, row: _PlanAircraftRow) -> None:
        if row in self._plan_aircraft_rows:
            self._plan_aircraft_rows.remove(row)
        row.deleteLater()

    def _on_plan_wing_changed(self) -> None:
        wing_id = self.plan_wing.currentData() or None
        self._refresh_plan_unit_combo(wing_id)
        self._refresh_plan_aircraft_rows()

    def _on_plan_unit_changed(self) -> None:
        self._refresh_plan_aircraft_rows()

    def _reset_deployment_plan_form(self, status: str) -> None:
        self._refresh_plan_wing_combo()
        self._refresh_plan_unit_combo(None)
        self._clear_plan_aircraft_rows()
        self._add_plan_aircraft_row()
        self._reset_flight_plan_form()
        self.plan_status.setText(status)

    def _apply_sim_flight_defaults(self, *, include_waypoint: bool = False) -> None:
        sim = SIM_FLIGHT_DEFAULTS
        self.takeoff_lat.setValue(sim.takeoff_lat)
        self.takeoff_lng.setValue(sim.takeoff_lng)
        self.cruise_altitude_ft.setValue(sim.cruise_altitude_ft)
        self.ingress_altitude_ft.setValue(sim.ingress_altitude_ft)
        self.target_altitude_ft.setValue(sim.fly_through_altitude_ft)
        self.climb_rate_ft_min.setValue(sim.climb_rate_ft_min)
        self.descent_rate_ft_min.setValue(sim.descent_rate_ft_min)
        self.cruise_speed_kt.setValue(int(sim.cruise_speed_kt))
        self.climb_speed_kt.setValue(int(sim.climb_speed_kt))
        self.descent_speed_kt.setValue(int(sim.descent_speed_kt))
        self.ingress_speed_kt.setValue(int(sim.ingress_speed_kt))
        self.bank_angle_deg.setValue(int(sim.cruise_bank_deg))
        turn_index = self.turn_mode.findData(sim.turn_mode)
        self.turn_mode.setCurrentIndex(turn_index if turn_index >= 0 else 0)
        self.auto_toc_tod.setChecked(sim.auto_toc_tod)
        self.use_ingress_bearing.setChecked(sim.ingress_enabled)
        self.ingress_bearing.setValue(sim.ingress_heading_deg)
        self.ingress_offset_m.setValue(sim.ingress_distance_m)
        self.return_enabled.setChecked(sim.rtb_enabled)
        if include_waypoint:
            self._clear_plan_waypoint_rows()
            self._add_plan_waypoint_row(
                label=sim.objective_name,
                lat=sim.objective_lat,
                lng=sim.objective_lng,
                altitude_ft=sim.fly_through_altitude_ft,
            )

    def _reset_flight_plan_form(self) -> None:
        self._apply_sim_flight_defaults(include_waypoint=True)
        self._clear_plan_return_waypoint_rows()
        self.flight_plan_summary.setText(
            f"ชุดจำลอง {SIM_FLIGHT_DEFAULTS.mission_id} — "
            "กดคำนวณแผนการบินเพื่อดู trajectory"
        )

    def _clear_plan_return_waypoint_rows(self) -> None:
        while self._plan_return_waypoint_rows:
            row = self._plan_return_waypoint_rows.pop()
            self.plan_return_waypoint_rows_layout.removeWidget(row)
            row.deleteLater()

    def _add_plan_return_waypoint_row(
        self,
        label: str = SIM_FLIGHT_DEFAULTS.rtb_name,
        lat: float = SIM_FLIGHT_DEFAULTS.rtb_lat,
        lng: float = SIM_FLIGHT_DEFAULTS.rtb_lng,
        altitude_ft: int | None = SIM_FLIGHT_DEFAULTS.rtb_alt_ft,
    ) -> None:
        row = _PlanWaypointRow(labels=["RTB", "Recovery", "Tanker", "Hold"])
        row.label.setCurrentText(label)
        row.lat.setValue(lat)
        row.lng.setValue(lng)
        if altitude_ft is not None:
            row.altitude_ft.setValue(altitude_ft)
        row.remove_btn.clicked.connect(
            lambda _checked=False, target=row: self._remove_plan_return_waypoint_row(
                target
            )
        )
        self._plan_return_waypoint_rows.append(row)
        self.plan_return_waypoint_rows_layout.addWidget(row)

    def _remove_plan_return_waypoint_row(self, row: _PlanWaypointRow) -> None:
        if row not in self._plan_return_waypoint_rows:
            return
        self._plan_return_waypoint_rows.remove(row)
        self.plan_return_waypoint_rows_layout.removeWidget(row)
        row.deleteLater()

    def _clear_plan_waypoint_rows(self) -> None:
        while self._plan_waypoint_rows:
            row = self._plan_waypoint_rows.pop()
            self.plan_waypoint_rows_layout.removeWidget(row)
            row.deleteLater()

    def _add_plan_waypoint_row(
        self,
        label: str = SIM_FLIGHT_DEFAULTS.objective_name,
        lat: float = SIM_FLIGHT_DEFAULTS.objective_lat,
        lng: float = SIM_FLIGHT_DEFAULTS.objective_lng,
        altitude_ft: int | None = SIM_FLIGHT_DEFAULTS.fly_through_altitude_ft,
    ) -> None:
        row = _PlanWaypointRow()
        row.label.setCurrentText(label)
        row.lat.setValue(lat)
        row.lng.setValue(lng)
        if altitude_ft is not None:
            row.altitude_ft.setValue(altitude_ft)
        row.remove_btn.clicked.connect(
            lambda _checked=False, target=row: self._remove_plan_waypoint_row(target)
        )
        self._plan_waypoint_rows.append(row)
        self.plan_waypoint_rows_layout.addWidget(row)

    def _remove_plan_waypoint_row(self, row: _PlanWaypointRow) -> None:
        if row not in self._plan_waypoint_rows:
            return
        self._plan_waypoint_rows.remove(row)
        self.plan_waypoint_rows_layout.removeWidget(row)
        row.deleteLater()

    def _apply_wing_takeoff_coords(self) -> None:
        wing_id = self.plan_wing.currentData()
        if not wing_id:
            QMessageBox.information(self, "Takeoff", "เลือกกองบินก่อน")
            return
        wing = self.wing_data_service.get_wing(str(wing_id))
        if wing is None or wing.map_lat is None or wing.map_lng is None:
            QMessageBox.information(
                self,
                "Takeoff",
                "กองบินที่เลือกยังไม่มีพิกัดบนแผนที่",
            )
            return
        self.takeoff_lat.setValue(wing.map_lat)
        self.takeoff_lng.setValue(wing.map_lng)

    def _target_coords(self) -> tuple[float, float] | None:
        point = self._active_point_result()
        if point is not None:
            return point.lat, point.lng
        if not self._selected_target_id:
            return None
        detail = self.target_service.get_target_detail(self._selected_target_id)
        if detail is None or detail.map_lat is None or detail.map_lng is None:
            return None
        return detail.map_lat, detail.map_lng

    def _profile_settings(self) -> FlightProfileSettings:
        return FlightProfileSettings(
            cruise_altitude_ft=self.cruise_altitude_ft.value(),
            ingress_altitude_ft=self.ingress_altitude_ft.value(),
            target_altitude_ft=self.target_altitude_ft.value(),
            climb_rate_ft_min=self.climb_rate_ft_min.value(),
            descent_rate_ft_min=self.descent_rate_ft_min.value(),
            return_enabled=self.return_enabled.isChecked(),
            cruise_speed_kt=float(self.cruise_speed_kt.value()),
            climb_speed_kt=float(self.climb_speed_kt.value()),
            descent_speed_kt=float(self.descent_speed_kt.value()),
            ingress_speed_kt=float(self.ingress_speed_kt.value()),
            bank_angle_deg=float(self.bank_angle_deg.value()),
            turn_mode=str(self.turn_mode.currentData() or "fly_by"),
            auto_toc_tod=self.auto_toc_tod.isChecked(),
        )

    def _collect_waypoint_specs(
        self,
        rows: list[_PlanWaypointRow],
        *,
        waypoint_type: str,
    ) -> list[FlightWaypointSpec]:
        specs: list[FlightWaypointSpec] = []
        for row in rows:
            values = row.values()
            if values is None:
                continue
            label, lat, lng, altitude_ft = values
            specs.append(
                FlightWaypointSpec(
                    lat=lat,
                    lng=lng,
                    label=label,
                    waypoint_type=waypoint_type,
                    altitude_ft=altitude_ft,
                )
            )
        return specs

    def _collect_flight_plan_inputs(self) -> tuple[
        tuple[float, float] | None,
        tuple[float, float] | None,
        list[FlightWaypointSpec],
        list[FlightWaypointSpec],
        float | None,
        int,
        FlightProfileSettings,
    ]:
        takeoff = (self.takeoff_lat.value(), self.takeoff_lng.value())
        destination = self._target_coords()
        outbound = self._collect_waypoint_specs(
            self._plan_waypoint_rows,
            waypoint_type="fly_through",
        )
        return_waypoints = self._collect_waypoint_specs(
            self._plan_return_waypoint_rows,
            waypoint_type="return",
        )
        ingress_bearing = (
            float(self.ingress_bearing.value())
            if self.use_ingress_bearing.isChecked()
            else None
        )
        return (
            takeoff,
            destination,
            outbound,
            return_waypoints,
            ingress_bearing,
            self.ingress_offset_m.value(),
            self._profile_settings(),
        )

    def _calculate_ingress_bearing(self) -> None:
        takeoff, destination, outbound, _, _, _, _ = self._collect_flight_plan_inputs()
        if destination is None:
            QMessageBox.information(
                self,
                "Ingress",
                "เป้าหมายยังไม่มีพิกัดบนแผนที่",
            )
            return
        if outbound:
            origin = (outbound[-1].lat, outbound[-1].lng)
        elif takeoff is not None:
            origin = takeoff
        else:
            QMessageBox.information(self, "Ingress", "กำหนด Takeoff หรือจุดบินผ่านก่อน")
            return
        bearing = bearing_deg(origin[0], origin[1], destination[0], destination[1])
        self.use_ingress_bearing.setChecked(True)
        self.ingress_bearing.setValue(int(round(bearing)) % 360)

    def _preview_flight_plan(self) -> None:
        (
            takeoff,
            destination,
            outbound,
            return_waypoints,
            ingress_bearing,
            ingress_offset,
            profile,
        ) = self._collect_flight_plan_inputs()
        if takeoff is None:
            QMessageBox.information(self, "แผนการบิน", "กำหนดพิกัด Takeoff ก่อน")
            return
        if destination is None:
            QMessageBox.information(
                self,
                "แผนการบิน",
                "เป้าหมายยังไม่มีพิกัดบนแผนที่",
            )
            return
        result = compute_flight_profile(
            takeoff=takeoff,
            destination=destination,
            outbound_waypoints=outbound,
            return_waypoints=return_waypoints,
            ingress_bearing_deg=ingress_bearing,
            ingress_offset_m=ingress_offset,
            profile=profile,
        )
        segment_lines = [
            f"{segment['label']} · {segment['distanceLabel']} · "
            f"{segment['startAltFt']}→{segment['endAltFt']} ft · "
            f"{segment['durationLabel']}"
            for segment in result.profile_segments
        ]
        approach = (
            f"ทิศเข้าเป้า: {result.final_approach_bearing_deg:.0f}°"
            if result.final_approach_bearing_deg is not None
            else "ทิศเข้าเป้า: ตามเส้นทางสุดท้าย"
        )
        realism = (
            f"Trajectory {len(result.trajectory_samples)} pts · "
            f"Bank {profile.bank_angle_deg:.0f}° · {profile.turn_mode}"
        )
        if profile.auto_toc_tod:
            realism += (
                f" · TOC ~{climb_horizontal_distance_m(profile) / 1000:.0f} km · "
                f"TOD ~{descent_horizontal_distance_m(profile) / 1000:.0f} km ก่อนเป้า"
            )
        self.flight_plan_summary.setText(
            f"รวม {format_distance_km(result.total_distance_m)} · "
            f"เวลา ~{format_duration_min(result.total_duration_min)} · "
            f"{len(result.points)} จุด · {approach}\n"
            f"{realism}\n"
            + "\n".join(segment_lines)
        )

    def _flight_plan_request_values(
        self,
    ) -> tuple[
        float | None,
        float | None,
        float | None,
        int,
        FlightProfileSettings,
        tuple[DeploymentWaypointRequest, ...],
    ]:
        takeoff, _, _, _, ingress_bearing, ingress_offset, profile = (
            self._collect_flight_plan_inputs()
        )
        wing_id = self.plan_wing.currentData()
        takeoff_lat: float | None = takeoff[0] if takeoff else None
        takeoff_lng: float | None = takeoff[1] if takeoff else None
        if wing_id:
            wing = self.wing_data_service.get_wing(str(wing_id))
            if (
                wing
                and wing.map_lat is not None
                and wing.map_lng is not None
                and takeoff_lat is not None
                and takeoff_lng is not None
                and abs(wing.map_lat - takeoff_lat) < 1e-5
                and abs(wing.map_lng - takeoff_lng) < 1e-5
            ):
                takeoff_lat = None
                takeoff_lng = None
        waypoint_requests: list[DeploymentWaypointRequest] = []
        for row in self._plan_waypoint_rows:
            values = row.values()
            if values is None:
                continue
            label, lat, lng, altitude_ft = values
            waypoint_requests.append(
                DeploymentWaypointRequest(
                    lat=lat,
                    lng=lng,
                    label=label,
                    waypoint_type="fly_through",
                    altitude_ft=altitude_ft,
                )
            )
        for row in self._plan_return_waypoint_rows:
            values = row.values()
            if values is None:
                continue
            label, lat, lng, altitude_ft = values
            waypoint_requests.append(
                DeploymentWaypointRequest(
                    lat=lat,
                    lng=lng,
                    label=label,
                    waypoint_type="return",
                    altitude_ft=altitude_ft,
                )
            )
        return (
            takeoff_lat,
            takeoff_lng,
            ingress_bearing,
            ingress_offset,
            profile,
            tuple(waypoint_requests),
        )

    def _load_deployment_plan(self) -> None:
        if not self._scenario_id or not self._selected_target_id:
            self._reset_deployment_plan_form("ยังไม่ได้บันทึกแผนสำหรับ Target นี้")
            return

        plan = self.weaponeering_service.get_deployment_plan_for_target(
            self._selected_target_id
        )
        if plan is None:
            self._reset_deployment_plan_form("ยังไม่ได้บันทึกแผนสำหรับ Target นี้")
            return

        self._refresh_plan_wing_combo(plan.wing_id)
        self._refresh_plan_unit_combo(plan.wing_id, plan.flying_unit_id)
        self._clear_plan_aircraft_rows()
        for line in plan.aircraft_lines:
            self._add_plan_aircraft_row(line.aircraft_id, line.aircraft_count)
        if not plan.aircraft_lines:
            self._add_plan_aircraft_row()

        wing = self.wing_data_service.get_wing(plan.wing_id)
        if plan.takeoff_lat is not None and plan.takeoff_lng is not None:
            self.takeoff_lat.setValue(plan.takeoff_lat)
            self.takeoff_lng.setValue(plan.takeoff_lng)
        elif wing and wing.map_lat is not None and wing.map_lng is not None:
            self.takeoff_lat.setValue(wing.map_lat)
            self.takeoff_lng.setValue(wing.map_lng)
        if plan.ingress_bearing_deg is not None:
            self.use_ingress_bearing.setChecked(True)
            self.ingress_bearing.setValue(int(round(plan.ingress_bearing_deg)) % 360)
        else:
            self.use_ingress_bearing.setChecked(False)
        self.ingress_offset_m.setValue(plan.ingress_offset_m)
        self.cruise_altitude_ft.setValue(plan.cruise_altitude_ft)
        self.ingress_altitude_ft.setValue(plan.ingress_altitude_ft)
        self.target_altitude_ft.setValue(plan.target_altitude_ft)
        self.climb_rate_ft_min.setValue(plan.climb_rate_ft_min)
        self.descent_rate_ft_min.setValue(plan.descent_rate_ft_min)
        self.cruise_speed_kt.setValue(int(round(plan.cruise_speed_kt)))
        self.climb_speed_kt.setValue(int(round(plan.climb_speed_kt)))
        self.descent_speed_kt.setValue(int(round(plan.descent_speed_kt)))
        self.ingress_speed_kt.setValue(int(round(plan.ingress_speed_kt)))
        self.bank_angle_deg.setValue(int(round(plan.bank_angle_deg)))
        turn_index = self.turn_mode.findData(plan.turn_mode)
        self.turn_mode.setCurrentIndex(turn_index if turn_index >= 0 else 0)
        self.auto_toc_tod.setChecked(plan.auto_toc_tod)
        self.return_enabled.setChecked(plan.return_enabled)
        self._clear_plan_waypoint_rows()
        self._clear_plan_return_waypoint_rows()
        for waypoint in plan.waypoints:
            if waypoint.waypoint_type == "return":
                self._add_plan_return_waypoint_row(
                    label=waypoint.label or "RTB",
                    lat=waypoint.lat,
                    lng=waypoint.lng,
                    altitude_ft=waypoint.altitude_ft,
                )
            else:
                self._add_plan_waypoint_row(
                    label=waypoint.label or "WP",
                    lat=waypoint.lat,
                    lng=waypoint.lng,
                    altitude_ft=waypoint.altitude_ft,
                )
        self._preview_flight_plan()

        unit = self.wing_data_service.get_flying_unit(plan.flying_unit_id)
        wing_name = wing.wing_name if wing else plan.wing_id
        unit_name = unit.unit_name if unit else plan.flying_unit_id
        line_summaries: list[str] = []
        for line in plan.aircraft_lines:
            aircraft = self.wing_data_service.get_aircraft(line.aircraft_id)
            label = aircraft.aircraft_type if aircraft else line.aircraft_id
            line_summaries.append(f"{label} × {line.aircraft_count}")
        aircraft_text = ", ".join(line_summaries) if line_summaries else "—"
        self.plan_status.setText(
            f"แผนที่บันทึก: {wing_name} · {unit_name} · "
            f"{aircraft_text} (รวม {plan.total_aircraft_count} ลำ)"
        )

    def _save_deployment_plan(self) -> None:
        if not self._scenario_id or not self._selected_target_id:
            QMessageBox.information(self, "เลือก Target", "ต้องเลือก Target Card ก่อน")
            return
        wing_id = self.plan_wing.currentData()
        unit_id = self.plan_unit.currentData()
        if not wing_id or not unit_id:
            QMessageBox.information(
                self,
                "ข้อมูลไม่ครบ",
                "กรุณาเลือกกองบินและหน่วยบิน",
            )
            return
        aircraft_lines: list[DeploymentAircraftLineRequest] = []
        for row in self._plan_aircraft_rows:
            values = row.values()
            if values is None:
                continue
            aircraft_id, count = values
            aircraft_lines.append(
                DeploymentAircraftLineRequest(
                    aircraft_id=aircraft_id,
                    aircraft_count=count,
                )
            )
        if not aircraft_lines:
            QMessageBox.information(
                self,
                "ข้อมูลไม่ครบ",
                "กรุณาเพิ่มเครื่องบินอย่างน้อย 1 รายการ",
            )
            return
        (
            takeoff_lat,
            takeoff_lng,
            ingress_bearing,
            ingress_offset,
            profile,
            waypoint_requests,
        ) = self._flight_plan_request_values()
        try:
            self.weaponeering_service.upsert_deployment_plan(
                UpsertDeploymentPlanRequest(
                    scenario_id=self._scenario_id,
                    target_card_id=self._selected_target_id,
                    wing_id=str(wing_id),
                    flying_unit_id=str(unit_id),
                    aircraft_lines=tuple(aircraft_lines),
                    takeoff_lat=takeoff_lat,
                    takeoff_lng=takeoff_lng,
                    ingress_bearing_deg=ingress_bearing,
                    ingress_offset_m=ingress_offset,
                    cruise_altitude_ft=profile.cruise_altitude_ft,
                    ingress_altitude_ft=profile.ingress_altitude_ft,
                    target_altitude_ft=profile.target_altitude_ft,
                    climb_rate_ft_min=profile.climb_rate_ft_min,
                    descent_rate_ft_min=profile.descent_rate_ft_min,
                    return_enabled=profile.return_enabled,
                    cruise_speed_kt=profile.cruise_speed_kt,
                    climb_speed_kt=profile.climb_speed_kt,
                    descent_speed_kt=profile.descent_speed_kt,
                    ingress_speed_kt=profile.ingress_speed_kt,
                    bank_angle_deg=profile.bank_angle_deg,
                    turn_mode=profile.turn_mode,
                    auto_toc_tod=profile.auto_toc_tod,
                    waypoints=waypoint_requests,
                )
            )
            self._load_deployment_plan()
            self.weaponeering_changed.emit()
        except ValueError as error:
            QMessageBox.warning(self, "บันทึกแผนไม่สำเร็จ", str(error))

    def _clear_deployment_plan(self) -> None:
        if not self._selected_target_id:
            return
        self.weaponeering_service.delete_deployment_plan(self._selected_target_id)
        self._reset_deployment_plan_form("ล้างแผนสำหรับ Target นี้แล้ว")
        self.weaponeering_changed.emit()
