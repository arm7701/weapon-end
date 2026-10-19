from __future__ import annotations

from PySide6.QtCore import Qt, QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.wing_data.models import WingTableSummary
from maap_app.modules.wing_data.schemas import (
    CreateAircraftRequest,
    CreateAirWingRequest,
    CreateFlyingUnitRequest,
    CreateLogisticsVehicleRequest,
    CreatePilotRequest,
    CreateWingDepotRequest,
    UpdateAircraftRequest,
    UpdateAirWingRequest,
    UpdateFlyingUnitRequest,
    UpdateLogisticsVehicleRequest,
    UpdatePilotRequest,
    UpdateWingDepotRequest,
)
from maap_app.modules.ground_transport.service import GroundTransportService
from maap_app.modules.team_marker.service import TeamMarkerService
from maap_app.modules.wing_data.service import WingDataService
from maap_app.ui.panels.ground_transport_page import GroundTransportPage
from maap_app.ui.panels.team_marker_page import TeamMarkerPage
from maap_app.ui.panels.wing_form_widgets import (
    _coord_spin,
    _field_row,
    _float_spin,
    _form_card,
    _ready_combo,
    _set_ready,
    _table,
)
from maap_app.ui.panels.wing_supply_page import (
    ProductCatalogPage,
    StockInventoryPage,
    TransferInventoryPage,
)

class _RefreshWorker(QThread):
    """Fetches all wing-data DB queries on a background thread."""
    done = Signal(dict)

    def __init__(self, service: WingDataService, scenario_id: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._svc = service
        self._sid = scenario_id

    def run(self) -> None:
        sid = self._sid
        try:
            result: dict = {
                "wings": self._svc.list_wings(sid),
                "wing_summaries": self._svc.list_wing_table_summaries(sid),
                "flying_units": self._svc.list_flying_units(sid),
                "aircraft": self._svc.list_aircraft(sid),
                "pilots": self._svc.list_pilots(sid),
                "depots": self._svc.list_depots(sid),
                "products": self._svc.list_products(sid),
                "inventory": self._svc.list_inventory(sid),
                "transfers": self._svc.list_transfers(sid),
                "vehicles": self._svc.list_vehicles(sid),
            }
        except Exception as exc:
            result = {"error": str(exc)}
        self.done.emit(result)


_TAB_KEYS = {
    "wing_data": 0,
    "organization": 0,
    "unit_info": 0,
    "flying_unit": 1,
    "flying_units": 1,
    "assets": 2,
    "aircraft": 2,
    "pilots": 3,
    "pilot": 3,
    "depot_supply": 4,
    "depot": 4,
    "product": 5,
    "products": 5,
    "stock": 6,
    "inventory": 6,
    "transfer": 7,
    "logistics": 8,
    "route": 8,
    "resource_status": 8,
    "ground_transport": 9,
    "transport": 9,
    "team_marker": 10,
    "map_team": 10,
}

_TABLE_NAV_ITEMS: tuple[tuple[str, str], ...] = (
    ("wing_data", "ข้อมูลกองบิน"),
    ("flying_unit", "ข้อมูลหน่วยบิน"),
    ("aircraft", "ข้อมูลเครื่องบิน"),
    ("pilot", "ข้อมูลนักบิน"),
    ("depot", "ข้อมูลคลัง"),
    ("product", "ข้อมูลสินค้า"),
    ("stock", "ข้อมูลสต็อก"),
    ("transfer", "ข้อมูลย้ายสินค้า"),
    ("logistics", "ข้อมูลส่งกำลังบำรุง"),
    ("ground_transport", "ข้อมูลขนส่งทางบก"),
    ("team_marker", "ข้อมูลพื้นที่ Blue/Red"),
)


def _fmt_ready(status: str) -> str:
    return "พร้อม" if status == "ready" else "ไม่พร้อม"


def _fmt_coord(value: float | None) -> str:
    return f"{value:.5f}" if value is not None else "-"


def _fmt_product_stock(stock: tuple[tuple[str, int], ...]) -> str:
    if not stock:
        return "-"
    return " · ".join(f"{name} × {qty}" for name, qty in stock)


class _EntityTableFormPage(QWidget):
    def __init__(
        self, columns, form_title, form_subtitle, form_widget,
        on_save, on_delete, on_clear, on_row_selected,
    ):
        super().__init__()
        self._selected_id: str | None = None
        self._on_row_selected = on_row_selected
        self._on_save = on_save
        self._on_delete = on_delete
        self._on_clear = on_clear

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)

        # ── Table pane (left, expanding) ──────────────────────────
        table_host = QWidget()
        tl = QVBoxLayout(table_host)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)

        top_bar = QWidget()
        top_bar.setObjectName("TableTopBar")
        tb = QHBoxLayout(top_bar)
        tb.setContentsMargins(10, 8, 10, 8)
        tb.setSpacing(8)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("ค้นหา...")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setObjectName("TableSearchBox")
        self.search_box.textChanged.connect(self._filter_table)
        self.add_btn = QPushButton("+ เพิ่ม")
        self.add_btn.setObjectName("PrimaryButton")
        self.add_btn.clicked.connect(self._enter_add_mode)
        tb.addWidget(self.search_box, 1)
        tb.addWidget(self.add_btn)
        tl.addWidget(top_bar)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("Divider")
        tl.addWidget(divider)

        self.table = _table(columns)
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.installEventFilter(self)
        tl.addWidget(self.table)
        table_host.setMinimumWidth(320)
        splitter.addWidget(table_host)

        # ── Form pane (right, fixed preferred width) ───────────────
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        form_scroll.setMinimumWidth(260)
        form_scroll.setMaximumWidth(400)

        form_card, form_layout = _form_card(form_title, form_subtitle)

        # Mode banner — shows Add vs Edit state prominently
        self.mode_banner = QLabel("➕  เพิ่มข้อมูลใหม่")
        self.mode_banner.setObjectName("FormModeBannerAdd")
        self.mode_banner.setStyleSheet(
            "background: #14532d; color: #86efac; border-radius: 4px;"
            " padding: 4px 10px; font-size: 11px; font-weight: 600;"
        )
        self.mode_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(self.mode_banner)

        form_layout.addWidget(form_widget)
        form_layout.addStretch(1)

        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setObjectName("Divider")
        form_layout.addWidget(divider2)

        self.save_btn = QPushButton("บันทึก")
        self.save_btn.setObjectName("PrimaryButton")
        self.delete_btn = QPushButton("ลบ")
        self.delete_btn.setObjectName("SecondaryButton")
        self.clear_btn = QPushButton("ล้างฟอร์ม")
        self.clear_btn.setObjectName("GhostButton")
        self.delete_btn.setVisible(False)
        self.save_btn.clicked.connect(on_save)
        self.delete_btn.clicked.connect(on_delete)
        self.clear_btn.clicked.connect(self._enter_add_mode)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.addWidget(self.save_btn, 1)
        btn_row.addWidget(self.delete_btn, 1)
        form_layout.addLayout(btn_row)
        form_layout.addWidget(self.clear_btn)

        form_scroll.setWidget(form_card)
        splitter.addWidget(form_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        outer_layout.addWidget(splitter)

    def _enter_add_mode(self) -> None:
        """Switch form to Add-New mode: clear selection, reset buttons/banner."""
        self.table.clearSelection()
        self._selected_id = None
        self._set_add_mode()
        self._on_clear()

    def _set_add_mode(self) -> None:
        self.mode_banner.setText("➕  เพิ่มข้อมูลใหม่")
        self.mode_banner.setStyleSheet(
            "background: #14532d; color: #86efac; border-radius: 4px;"
            " padding: 4px 10px; font-size: 11px; font-weight: 600;"
        )
        self.save_btn.setText("บันทึก")
        self.delete_btn.setVisible(False)
        self.clear_btn.setText("ล้างฟอร์ม")

    def _set_edit_mode(self, name: str) -> None:
        display = name[:28] + "…" if len(name) > 28 else name
        self.mode_banner.setText(f"✏️  กำลังแก้ไข: {display}")
        self.mode_banner.setStyleSheet(
            "background: #1e3a5f; color: #93c5fd; border-radius: 4px;"
            " padding: 4px 10px; font-size: 11px; font-weight: 600;"
        )
        self.save_btn.setText("อัพเดต")
        self.delete_btn.setVisible(True)
        self.clear_btn.setText("ยกเลิกแก้ไข")

    def eventFilter(self, obj, event) -> bool:
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent
        if obj is self.table and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self._enter_add_mode()
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self._selected_id:
                    self._on_save()
                    return True
        return super().eventFilter(obj, event)

    def _on_selection(self):
        row = self.table.currentRow()
        if row < 0:
            self._selected_id = None
            self._set_add_mode()
            return
        item = self.table.item(row, 0)
        eid = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not eid:
            self._selected_id = None
            self._set_add_mode()
            return
        self._selected_id = eid
        name = item.text() if item else ""
        self._set_edit_mode(name)
        self._on_row_selected(self._selected_id)

    def selected_id(self) -> str | None:
        return self._selected_id

    def set_rows(
        self,
        rows: list[list[str]],
        ids: list[str],
        center_columns: set[int] | None = None,
    ) -> None:
        prev_id = self._selected_id
        self.table.setSortingEnabled(False)
        self.table.clearSpans()
        if not rows:
            self.table.setRowCount(1)
            placeholder = QTableWidgetItem(
                "ยังไม่มีข้อมูล — กด '+ เพิ่ม' หรือกรอกฟอร์มด้านขวาเพื่อเพิ่มรายการแรก"
            )
            placeholder.setFlags(Qt.ItemFlag.ItemIsEnabled)
            placeholder.setForeground(
                __import__("PySide6.QtGui", fromlist=["QColor"]).QColor("#6b7f96")
            )
            self.table.setItem(0, 0, placeholder)
            if self.table.columnCount() > 1:
                self.table.setSpan(0, 0, 1, self.table.columnCount())
            self.table.setSortingEnabled(True)
            return
        self.table.setRowCount(len(rows))
        for ri, (cells, eid) in enumerate(zip(rows, ids, strict=True)):
            for ci, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if ci == 0:
                    item.setData(Qt.ItemDataRole.UserRole, eid)
                if center_columns and ci in center_columns:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(ri, ci, item)
        self.table.setSortingEnabled(True)
        # Re-select previously selected row after refresh
        if prev_id:
            for r in range(self.table.rowCount()):
                it = self.table.item(r, 0)
                if it and it.data(Qt.ItemDataRole.UserRole) == prev_id:
                    self.table.blockSignals(True)
                    self.table.selectRow(r)
                    self.table.blockSignals(False)
                    break

    def clear_selection(self) -> None:
        """Reset UI to add-mode without triggering the external clear callback."""
        self.table.clearSelection()
        self._selected_id = None
        self._set_add_mode()

    def _filter_table(self, text: str) -> None:
        text = text.lower().strip()
        for row in range(self.table.rowCount()):
            if not text:
                self.table.setRowHidden(row, False)
                continue
            match = any(
                item is not None and text in item.text().lower()
                for item in (self.table.item(row, col) for col in range(self.table.columnCount()))
            )
            self.table.setRowHidden(row, not match)


class WingDataPanel(QWidget):
    data_changed = Signal()
    team_markers_changed = Signal()
    transport_changed = Signal()

    def __init__(
        self,
        wing_data_service: WingDataService,
        ground_transport_service: GroundTransportService,
        team_marker_service: TeamMarkerService,
    ) -> None:
        super().__init__()
        self.service = wing_data_service
        self._ground_transport_service = ground_transport_service
        self._team_marker_service = team_marker_service
        self._scenario_id: str | None = None
        self._wing_names: dict[str, str] = {}
        self._unit_names: dict[str, str] = {}
        self._flying_units_cache: list = []
        self._worker: _RefreshWorker | None = None
        self.setObjectName("MapWorkspace")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setObjectName("MapWorkspaceHeader")
        header.setFixedHeight(48)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 14, 0)
        tb = QVBoxLayout()
        tb.setSpacing(0)
        t = QLabel("ฐานข้อมูล")
        t.setObjectName("MapWorkspaceTitle")
        self.subtitle = QLabel(
            "เลือกตารางด้านซ้าย · ดูและแก้ไขข้อมูลในตารางและฟอร์มด้านขวา"
        )
        self.subtitle.setObjectName("SectionSubtitle")
        tb.addWidget(t)
        tb.addWidget(self.subtitle)
        hl.addLayout(tb)
        hl.addStretch(1)
        root.addWidget(header)

        self._build_forms()
        self.wing_page = _EntityTableFormPage(
            ["ชื่อกองบิน", "Lat", "Lng", "หน่วยบิน", "เครื่องบิน", "นักบิน", "คลัง", "สินค้า (สต็อก)"],
            "ข้อมูลกองบิน", "กำหนดชื่อและพิกัดกองบินบนแผนที่",
            self.wing_form,
            self._save_wing, self._delete_wing, self._clear_wing, self._load_wing,
        )
        self.flying_unit_page = _EntityTableFormPage(
            ["ชื่อหน่วยบิน", "กองบิน"],
            "ข้อมูลหน่วยบิน", "กำหนดหน่วยบินภายใต้กองบิน (ฝูง/หมวด)",
            self.flying_unit_form,
            self._save_flying_unit, self._delete_flying_unit,
            self._clear_flying_unit, self._load_flying_unit,
        )
        self.aircraft_page = _EntityTableFormPage(
            ["ประเภท", "กองบิน", "หน่วยบิน", "สถานะ"],
            "ข้อมูลเครื่องบิน", "เชื่อมเครื่องบินกับกองบินและเลือกหน่วยบิน",
            self.aircraft_form,
            self._save_aircraft, self._delete_aircraft, self._clear_aircraft, self._load_aircraft,
        )
        self.pilot_page = _EntityTableFormPage(
            ["ชื่อนักบิน", "Callsign", "CEP", "กองบิน", "หน่วยบิน"],
            "ข้อมูลนักบิน", "บันทึกนักบิน เชื่อมกองบินและหน่วยบิน",
            self.pilot_form,
            self._save_pilot, self._delete_pilot, self._clear_pilot, self._load_pilot,
        )
        self.depot_page = _EntityTableFormPage(
            ["ชื่อคลัง", "กองบิน", "Lat", "Lng"],
            "ข้อมูลคลัง", "กำหนดตำแหน่งคลังและเชื่อมกับกองบิน",
            self.depot_form,
            self._save_depot, self._delete_depot, self._clear_depot, self._load_depot,
        )
        _supply_args = (
            self.service,
            lambda: self._scenario_id,
            self._require_scenario,
            self._confirm_delete,
            self._after_change,
        )
        self.product_page = ProductCatalogPage(*_supply_args)
        self.stock_page = StockInventoryPage(*_supply_args)
        self.transfer_page = TransferInventoryPage(*_supply_args)
        self.vehicle_page = _EntityTableFormPage(
            ["ชื่อรถ", "กองบิน", "อัตราเชื้อเพลิง", "สถานะ"],
            "ข้อมูลส่งกำลังบำรุง", "บันทึกรถและสถานะพร้อมปฏิบัติภารกิจ",
            self.vehicle_form,
            self._save_vehicle, self._delete_vehicle, self._clear_vehicle, self._load_vehicle,
        )
        self.ground_transport_page = GroundTransportPage(
            self._ground_transport_service,
            self.service,
            lambda: self._scenario_id,
            self._require_scenario,
            self._confirm_delete,
            self._after_transport_change,
        )
        self.team_marker_page = TeamMarkerPage(
            self._team_marker_service,
            lambda: self._scenario_id,
            self._require_scenario,
            self._confirm_delete,
            self._after_team_marker_change,
        )

        self._table_pages: dict[str, QWidget] = {
            "wing_data": self.wing_page,
            "flying_unit": self.flying_unit_page,
            "aircraft": self.aircraft_page,
            "pilot": self.pilot_page,
            "depot": self.depot_page,
            "product": self.product_page,
            "stock": self.stock_page,
            "transfer": self.transfer_page,
            "logistics": self.vehicle_page,
            "ground_transport": self.ground_transport_page,
            "team_marker": self.team_marker_page,
        }

        self.table_nav = QListWidget()
        self.table_nav.setObjectName("DatabaseTableNav")
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("DatabaseContentStack")
        for key, label in _TABLE_NAV_ITEMS:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.table_nav.addItem(item)
            self.content_stack.addWidget(self._table_pages[key])
        self.table_nav.currentRowChanged.connect(self._on_table_nav_changed)

        nav_panel = QWidget()
        nav_panel.setObjectName("DatabaseNavPanel")
        nav_panel.setMinimumWidth(220)
        nav_panel.setMaximumWidth(280)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(0, 0, 8, 0)
        nav_layout.setSpacing(8)
        nav_title = QLabel("ตารางข้อมูล")
        nav_title.setObjectName("SectionTitle")
        nav_hint = QLabel("เลือกตารางที่ต้องการดู")
        nav_hint.setObjectName("SectionSubtitle")
        nav_layout.addWidget(nav_title)
        nav_layout.addWidget(nav_hint)
        nav_layout.addWidget(self.table_nav, stretch=1)

        content_panel = QWidget()
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        content_layout.addWidget(self.content_stack, stretch=1)
        self.status_label = QLabel(
            "เลือกแถวในตารางเพื่อแก้ไข หรือกรอกฟอร์มด้านล่างเพื่อเพิ่มข้อมูลใหม่"
        )
        self.status_label.setStyleSheet("color: #6b7f96; font-size: 11px;")
        content_layout.addWidget(self.status_label)

        workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        workspace_splitter.setChildrenCollapsible(False)
        workspace_splitter.addWidget(nav_panel)
        workspace_splitter.addWidget(content_panel)
        workspace_splitter.setStretchFactor(0, 0)
        workspace_splitter.setStretchFactor(1, 1)
        workspace_splitter.setSizes([240, 960])

        root.addWidget(workspace_splitter, stretch=1)
        self.table_nav.setCurrentRow(0)

    def _build_forms(self) -> None:
        self.wing_name = QLineEdit("กองบิน 1")
        self.wing_lat = _coord_spin()
        self.wing_lng = _coord_spin()
        self.wing_form = QWidget()
        wing_layout = QVBoxLayout(self.wing_form)
        wing_layout.setContentsMargins(0, 0, 0, 0)
        wing_layout.setSpacing(8)
        wing_layout.addWidget(_field_row("ชื่อกองบิน", self.wing_name))
        wing_layout.addWidget(_field_row("Lat", self.wing_lat))
        wing_layout.addWidget(_field_row("Lng", self.wing_lng))

        self.fu_wing = QComboBox()
        self.fu_name = QLineEdit("ฝูง 1")
        self.flying_unit_form = QWidget()
        fu_layout = QVBoxLayout(self.flying_unit_form)
        fu_layout.setContentsMargins(0, 0, 0, 0)
        fu_layout.setSpacing(8)
        fu_layout.addWidget(_field_row("กองบิน", self.fu_wing))
        fu_layout.addWidget(_field_row("ชื่อหน่วยบิน", self.fu_name))

        self.ac_wing = QComboBox()
        self.ac_unit = QComboBox()
        self.ac_type = QLineEdit("F-16")
        self.ac_ready = _ready_combo()
        self.aircraft_form = QWidget()
        ac_layout = QVBoxLayout(self.aircraft_form)
        ac_layout.setContentsMargins(0, 0, 0, 0)
        ac_layout.setSpacing(8)
        ac_layout.addWidget(_field_row("กองบิน", self.ac_wing))
        ac_layout.addWidget(_field_row("หน่วยบิน", self.ac_unit))
        ac_layout.addWidget(_field_row("ประเภทเครื่องบิน", self.ac_type))
        ac_layout.addWidget(_field_row("สถานะปฏิบัติภารกิจ", self.ac_ready))
        self.ac_wing.currentIndexChanged.connect(
            lambda: self._refresh_unit_combo(self.ac_wing, self.ac_unit)
        )

        self.pilot_wing = QComboBox()
        self.pilot_unit = QComboBox()
        self.pilot_name = QLineEdit("นักบิน 1")
        self.pilot_callsign = QLineEdit("VIPER-01")
        self.pilot_cep = _float_spin(25.0, 500.0)
        self.pilot_form = QWidget()
        pilot_layout = QVBoxLayout(self.pilot_form)
        pilot_layout.setContentsMargins(0, 0, 0, 0)
        pilot_layout.setSpacing(8)
        pilot_layout.addWidget(_field_row("กองบิน", self.pilot_wing))
        pilot_layout.addWidget(_field_row("หน่วยบิน", self.pilot_unit))
        self.pilot_wing.currentIndexChanged.connect(
            lambda: self._refresh_unit_combo(self.pilot_wing, self.pilot_unit)
        )
        pilot_layout.addWidget(_field_row("ชื่อนักบิน", self.pilot_name))
        pilot_layout.addWidget(_field_row("Callsign", self.pilot_callsign))
        pilot_layout.addWidget(_field_row("CEP (m)", self.pilot_cep))

        self.depot_wing = QComboBox()
        self.depot_name = QLineEdit("คลังกลาง")
        self.depot_lat = _coord_spin()
        self.depot_lng = _coord_spin()
        self.depot_form = QWidget()
        depot_grid = QGridLayout(self.depot_form)
        depot_grid.setContentsMargins(0, 0, 0, 0)
        depot_grid.setHorizontalSpacing(12)
        depot_grid.setVerticalSpacing(8)
        depot_grid.addWidget(QLabel("กองบิน"), 0, 0)
        depot_grid.addWidget(self.depot_wing, 0, 1)
        depot_grid.addWidget(QLabel("ชื่อคลัง"), 0, 2)
        depot_grid.addWidget(self.depot_name, 0, 3)
        depot_grid.addWidget(QLabel("Lat"), 1, 0)
        depot_grid.addWidget(self.depot_lat, 1, 1)
        depot_grid.addWidget(QLabel("Lng"), 1, 2)
        depot_grid.addWidget(self.depot_lng, 1, 3)

        self.vehicle_wing = QComboBox()
        self.vehicle_name = QLineEdit("รถบรรทุกน้ำมัน 1")
        self.vehicle_fuel = _float_spin(12.5, 9999)
        self.vehicle_ready = _ready_combo()
        self.vehicle_form = QWidget()
        vehicle_layout = QVBoxLayout(self.vehicle_form)
        vehicle_layout.setContentsMargins(0, 0, 0, 0)
        vehicle_layout.setSpacing(8)
        vehicle_layout.addWidget(_field_row("กองบิน", self.vehicle_wing))
        vehicle_layout.addWidget(_field_row("ชื่อรถ", self.vehicle_name))
        vehicle_layout.addWidget(_field_row("อัตรากินเชื้อเพลิง (L/km)", self.vehicle_fuel))
        vehicle_layout.addWidget(_field_row("สถานะปฏิบัติภารกิจ", self.vehicle_ready))

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("DatabaseSidebar")
        sidebar.setMinimumWidth(150)
        sidebar.setMaximumWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.section_list = QListWidget()
        self.section_list.setObjectName("DatabaseSidebarList")
        self.section_list.setFrameShape(QListWidget.Shape.NoFrame)
        self.section_list.setSpacing(1)

        self._add_sidebar_group("Organization")
        for label, idx in [
            ("กองบิน", 0), ("หน่วยบิน", 1),
            ("เครื่องบิน", 2), ("นักบิน", 3),
        ]:
            self._add_sidebar_item(label, idx)

        self._add_sidebar_group("Logistics")
        for label, idx in [
            ("คลัง", 4), ("สินค้า", 5),
            ("สต็อก", 6), ("ย้ายสินค้า", 7), ("ส่งกำลังบำรุง", 8),
        ]:
            self._add_sidebar_item(label, idx)

        self.section_list.currentItemChanged.connect(self._on_sidebar_changed)
        layout.addWidget(self.section_list, stretch=1)
        return sidebar

    def _add_sidebar_group(self, title: str) -> None:
        item = QListWidgetItem(f"  {title.upper()}")
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setData(Qt.ItemDataRole.UserRole, -1)
        font = item.font()
        font.setPointSize(8)
        font.setBold(True)
        item.setFont(font)
        self.section_list.addItem(item)

    def _add_sidebar_item(self, label: str, index: int) -> None:
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, index)

        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(20, 5, 10, 5)
        rl.setSpacing(4)
        name_lbl = QLabel(label)
        name_lbl.setObjectName("SidebarItemName")
        count_lbl = QLabel("–")
        count_lbl.setObjectName("SidebarItemCount")
        count_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        count_lbl.setMinimumWidth(24)
        rl.addWidget(name_lbl, 1)
        rl.addWidget(count_lbl)

        item.setSizeHint(row.sizeHint())
        self.section_list.addItem(item)
        self.section_list.setItemWidget(item, row)
        self._sidebar_count_labels[index] = count_lbl

    def _on_sidebar_changed(
        self,
        current: QListWidgetItem | None,
        _prev: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return
        index = current.data(Qt.ItemDataRole.UserRole)
        if index is None or index < 0:
            # group header clicked — skip to next real item
            next_row = self.section_list.row(current) + 1
            if next_row < self.section_list.count():
                self.section_list.setCurrentRow(next_row)
            return
        self.content_stack.setCurrentIndex(index)

    def _select_sidebar_index(self, target: int) -> None:
        for i in range(self.section_list.count()):
            item = self.section_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == target:
                self.section_list.setCurrentItem(item)
                return

    def activate_section(self, key: str) -> None:
        index = _TAB_KEYS.get(key, 0)
        self.table_nav.setCurrentRow(index)

    def _on_table_nav_changed(self, index: int) -> None:
        if index < 0:
            return
        self.content_stack.setCurrentIndex(index)

    def set_scenario(self, scenario_id: str | None) -> None:
        self._scenario_id = scenario_id
        self.refresh()

    def refresh(self) -> None:
        if not self._scenario_id:
            for p in (
                self.wing_page,
                self.flying_unit_page,
                self.aircraft_page,
                self.pilot_page,
                self.depot_page,
                self.vehicle_page,
            ):
                p.set_rows([], [])
            for key in ("product", "stock", "transfer", "ground_transport", "team_marker"):
                self._refresh_table_page(key)
            return
        for key in self._table_pages:
            self._refresh_table_page(key)

    def _current_nav_key(self) -> str:
        index = self.table_nav.currentRow()
        if index < 0:
            return "wing_data"
        item = self.table_nav.item(index)
        if item is None:
            return "wing_data"
        key = item.data(Qt.ItemDataRole.UserRole)
        return str(key) if key else "wing_data"

    def _refresh_table_page(self, key: str) -> None:
        if not self._scenario_id:
            page = self._table_pages.get(key)
            if page is not None and hasattr(page, "refresh"):
                page.refresh()
            return

        if key == "wing_data":
            wings = self.service.list_wings(self._scenario_id)
            self._wing_names = {w.id: w.wing_name for w in wings}
            wing_summaries = self.service.list_wing_table_summaries(self._scenario_id)
            wing_rows: list[list[str]] = []
            for wing in wings:
                summary = wing_summaries.get(
                    wing.id,
                    WingTableSummary(0, 0, 0, 0, ()),
                )
                wing_rows.append(
                    [
                        wing.wing_name,
                        _fmt_coord(wing.map_lat),
                        _fmt_coord(wing.map_lng),
                        str(summary.flying_unit_count),
                        str(summary.aircraft_count),
                        str(summary.pilot_count),
                        str(summary.depot_count),
                        _fmt_product_stock(summary.product_stock),
                    ]
                )
            self.wing_page.set_rows(
                wing_rows,
                [w.id for w in wings],
                center_columns={3, 4, 5, 6},
            )
            return

        if key == "flying_unit":
            flying_units = self.service.list_flying_units(self._scenario_id)
            self._unit_names = {u.id: u.unit_name for u in flying_units}
            self.flying_unit_page.set_rows(
                [
                    [u.unit_name, self._wing_names.get(u.wing_id, "-")]
                    for u in flying_units
                ],
                [u.id for u in flying_units],
            )
            return

        if key == "aircraft":
            aircraft = self.service.list_aircraft(self._scenario_id)
            self.aircraft_page.set_rows(
                [
                    [
                        a.aircraft_type,
                        self._wing_names.get(a.wing_id, "-"),
                        self._unit_names.get(a.flying_unit_id or "", "-"),
                        _fmt_ready(a.mission_ready),
                    ]
                    for a in aircraft
                ],
                [a.id for a in aircraft],
            )
            return

        if key == "pilot":
            pilots = self.service.list_pilots(self._scenario_id)
            self.pilot_page.set_rows(
                [
                    [
                        p.pilot_name,
                        p.callsign,
                        f"{p.cep_value:.1f}",
                        self._wing_names.get(p.wing_id or "", "-"),
                        self._unit_names.get(p.flying_unit_id or "", "-"),
                    ]
                    for p in pilots
                ],
                [p.id for p in pilots],
            )
            return

        if key == "depot":
            depots = self.service.list_depots(self._scenario_id)
            self.depot_page.set_rows(
                [
                    [
                        d.depot_name,
                        self._wing_names.get(d.wing_id, "-"),
                        _fmt_coord(d.map_lat),
                        _fmt_coord(d.map_lng),
                    ]
                    for d in depots
                ],
                [d.id for d in depots],
            )
            return

        if key == "logistics":
            vehicles = self.service.list_vehicles(self._scenario_id)
            self.vehicle_page.set_rows(
                [
                    [
                        v.vehicle_name,
                        self._wing_names.get(v.wing_id, "-"),
                        f"{v.fuel_consumption_rate:.2f}",
                        _fmt_ready(v.mission_ready),
                    ]
                    for v in vehicles
                ],
                [v.id for v in vehicles],
            )
            return

        page = self._table_pages.get(key)
        if page is not None and hasattr(page, "refresh"):
            page.refresh()

    def show_entity_detail(self, entity_type: str, entity_id: str) -> None:
        if entity_type == "air_wing":
            self.activate_section("wing_data")
            self._select_row(self.wing_page.table, entity_id)
            self._load_wing(entity_id)
        elif entity_type == "wing_depot":
            self.activate_section("depot")
            self._select_row(self.depot_page.table, entity_id)
            self._load_depot(entity_id)
        elif entity_type == "ground_transport":
            self.activate_section("ground_transport")
            self.ground_transport_page.select_transport(entity_id)
        elif entity_type == "team_marker":
            self.activate_section("team_marker")
            self.team_marker_page.select_marker(entity_id)

    def _select_row(self, table: QTableWidget, eid: str) -> None:
        for r in range(table.rowCount()):
            item = table.item(r, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == eid:
                table.selectRow(r)
                return

    def _apply_wing_combos(self, wings: list) -> None:
        """Populate wing combo boxes from pre-fetched list (no DB query)."""
        for combo in (self.fu_wing, self.ac_wing, self.pilot_wing, self.depot_wing, self.vehicle_wing):
            combo.blockSignals(True)
            combo.clear()
        self.pilot_wing.addItem("(ไม่ระบุ)", "")
        for combo in (self.fu_wing, self.ac_wing, self.depot_wing, self.vehicle_wing):
            combo.addItem("(เลือกกองบิน)", "")
            for w in wings:
                combo.addItem(w.wing_name, w.id)
        for w in wings:
            self.pilot_wing.addItem(w.wing_name, w.id)
        for combo in (self.fu_wing, self.ac_wing, self.pilot_wing, self.depot_wing, self.vehicle_wing):
            combo.blockSignals(False)
        self._refresh_unit_combo(self.ac_wing, self.ac_unit)
        self._refresh_unit_combo(self.pilot_wing, self.pilot_unit)

    def _refresh_unit_combo(self, wing_combo: QComboBox, unit_combo: QComboBox) -> None:
        """Filter unit combo to the selected wing, using cached flying-units list."""
        selected = unit_combo.currentData()
        unit_combo.blockSignals(True)
        unit_combo.clear()
        unit_combo.addItem("(เลือกหน่วยบิน)", "")
        wing_id = wing_combo.currentData()
        if wing_id:
            for unit in self._flying_units_cache:
                if unit.wing_id == wing_id:
                    unit_combo.addItem(unit.unit_name, unit.id)
        if selected:
            idx = unit_combo.findData(selected)
            if idx >= 0:
                unit_combo.setCurrentIndex(idx)
        unit_combo.blockSignals(False)

    def _set_wing_combo(self, combo: QComboBox, wing_id: str | None) -> None:
        if not wing_id:
            combo.setCurrentIndex(0)
            return
        idx = combo.findData(wing_id)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _require_scenario(self) -> bool:
        if self._scenario_id:
            return True
        QMessageBox.warning(self, "ไม่มี scenario", "ยังไม่มี scenario ที่ใช้งาน")
        return False

    def _require_wing(self, combo: QComboBox) -> str | None:
        wid = combo.currentData()
        if not wid:
            QMessageBox.information(self, "กรุณาเลือกกองบิน", "ต้องเลือกกองบินก่อนบันทึก")
            return None
        return str(wid)

    def _require_flying_unit(self, combo: QComboBox) -> str | None:
        uid = combo.currentData()
        if not uid:
            QMessageBox.information(
                self,
                "กรุณาเลือกหน่วยบิน",
                "ต้องเลือกหน่วยบินก่อนบันทึก (สร้างได้ที่แท็บข้อมูลหน่วยบิน)",
            )
            return None
        return str(uid)

    def _after_change(self, msg: str = "") -> None:
        self._refresh_wing_combos()
        current_key = self._current_nav_key()
        self._refresh_table_page(current_key)
        if current_key in {"flying_unit", "aircraft", "pilot", "depot", "product", "stock"}:
            self._refresh_table_page("wing_data")
        self.data_changed.emit()
        if msg:
            self.status_label.setText(f"✓ {msg}")
            self.status_label.setStyleSheet("color: #4ade80; font-size: 11px;")
            self._status_timer.start(4000)
        self.data_changed.emit()
        self.refresh()  # launches background worker; returns immediately

    def _reset_status(self) -> None:
        self.status_label.setText(
            "เลือกแถวในตารางเพื่อแก้ไข หรือกรอกฟอร์มด้านล่างเพื่อเพิ่มข้อมูลใหม่"
        )
        self.status_label.setStyleSheet("color: #6b7f96; font-size: 11px;")

    def _after_team_marker_change(self, msg: str = "") -> None:
        self.team_marker_page.refresh()
        self.team_markers_changed.emit()
        if msg:
            self.status_label.setText(msg)

    def _after_transport_change(self, msg: str = "") -> None:
        self.ground_transport_page.refresh()
        self.transport_changed.emit()
        if msg:
            self.status_label.setText(msg)

    def _confirm_delete(self, label: str) -> bool:
        return QMessageBox.question(
            self, "ยืนยันการลบ", f"ลบ{label}ที่เลือก?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    # --- Wing CRUD ---
    def _load_wing(self, wid: str) -> None:
        w = self.service.get_wing(wid)
        if not w:
            return
        self.wing_name.setText(w.wing_name)
        self.wing_lat.setValue(w.map_lat or 0)
        self.wing_lng.setValue(w.map_lng or 0)

    def _clear_wing(self) -> None:
        self.wing_page.clear_selection()
        self.wing_name.setText("กองบิน 1")
        self.wing_lat.setValue(0.0)
        self.wing_lng.setValue(0.0)

    def _save_wing(self) -> None:
        if not self._require_scenario():
            return
        data = dict(wing_name=self.wing_name.text().strip(),
                    map_lat=self.wing_lat.value(), map_lng=self.wing_lng.value())
        wid = self.wing_page.selected_id()
        try:
            if wid:
                self.service.update_wing(UpdateAirWingRequest(wing_id=wid, **data))
                self._after_change("บันทึกกองบินแล้ว")
            else:
                self.service.create_wing(CreateAirWingRequest(scenario_id=self._scenario_id, **data))
                self._clear_wing()
                self._after_change("เพิ่มกองบินแล้ว")
        except ValueError as e:
            QMessageBox.warning(self, "Guardrail", str(e))

    def _delete_wing(self) -> None:
        wid = self.wing_page.selected_id()
        if wid and self._confirm_delete("กองบิน"):
            self.service.delete_wing(wid)
            self._clear_wing()
            self._after_change("ลบกองบินแล้ว")

    # --- Flying unit CRUD ---
    def _load_flying_unit(self, uid: str) -> None:
        unit = self.service.get_flying_unit(uid)
        if not unit:
            return
        self._set_wing_combo(self.fu_wing, unit.wing_id)
        self.fu_name.setText(unit.unit_name)

    def _clear_flying_unit(self) -> None:
        self.flying_unit_page.clear_selection()
        self.fu_wing.setCurrentIndex(0)
        self.fu_name.setText("ฝูง 1")

    def _save_flying_unit(self) -> None:
        if not self._require_scenario():
            return
        wing_id = self._require_wing(self.fu_wing)
        if not wing_id:
            return
        data = dict(wing_id=wing_id, unit_name=self.fu_name.text().strip())
        uid = self.flying_unit_page.selected_id()
        try:
            if uid:
                self.service.update_flying_unit(
                    UpdateFlyingUnitRequest(flying_unit_id=uid, **data)
                )
                self._after_change("บันทึกหน่วยบินแล้ว")
            else:
                self.service.create_flying_unit(
                    CreateFlyingUnitRequest(scenario_id=self._scenario_id, **data)
                )
                self._clear_flying_unit()
                self._after_change("เพิ่มหน่วยบินแล้ว")
        except ValueError as e:
            QMessageBox.warning(self, "Guardrail", str(e))

    def _delete_flying_unit(self) -> None:
        uid = self.flying_unit_page.selected_id()
        if uid and self._confirm_delete("หน่วยบิน"):
            self.service.delete_flying_unit(uid)
            self._clear_flying_unit()
            self._after_change("ลบหน่วยบินแล้ว")

    # --- Aircraft CRUD ---
    def _load_aircraft(self, aid: str) -> None:
        a = self.service.get_aircraft(aid)
        if not a:
            return
        self._set_wing_combo(self.ac_wing, a.wing_id)
        self._refresh_unit_combo(self.ac_wing, self.ac_unit)
        if a.flying_unit_id:
            idx = self.ac_unit.findData(a.flying_unit_id)
            if idx >= 0:
                self.ac_unit.setCurrentIndex(idx)
        self.ac_type.setText(a.aircraft_type)
        _set_ready(self.ac_ready, a.mission_ready)

    def _clear_aircraft(self) -> None:
        self.aircraft_page.clear_selection()
        self.ac_wing.setCurrentIndex(0)
        self._refresh_unit_combo(self.ac_wing, self.ac_unit)
        self.ac_type.setText("F-16")
        _set_ready(self.ac_ready, "not_ready")

    def _save_aircraft(self) -> None:
        if not self._require_scenario():
            return
        wing_id = self._require_wing(self.ac_wing)
        if not wing_id:
            return
        flying_unit_id = self._require_flying_unit(self.ac_unit)
        if not flying_unit_id:
            return
        data = dict(
            wing_id=wing_id,
            aircraft_type=self.ac_type.text().strip(),
            flying_unit_id=flying_unit_id,
            mission_ready=self.ac_ready.currentData(),
        )
        aid = self.aircraft_page.selected_id()
        try:
            if aid:
                self.service.update_aircraft(UpdateAircraftRequest(aircraft_id=aid, **data))
                self._after_change("บันทึกเครื่องบินแล้ว")
            else:
                self.service.create_aircraft(CreateAircraftRequest(scenario_id=self._scenario_id, **data))
                self._clear_aircraft()
                self._after_change("เพิ่มเครื่องบินแล้ว")
        except ValueError as e:
            QMessageBox.warning(self, "Guardrail", str(e))

    def _delete_aircraft(self) -> None:
        aid = self.aircraft_page.selected_id()
        if aid and self._confirm_delete("เครื่องบิน"):
            self.service.delete_aircraft(aid)
            self._clear_aircraft()
            self._after_change("ลบเครื่องบินแล้ว")

    # --- Pilot CRUD ---
    def _load_pilot(self, pid: str) -> None:
        p = self.service.get_pilot(pid)
        if not p:
            return
        self._set_wing_combo(self.pilot_wing, p.wing_id)
        self._refresh_unit_combo(self.pilot_wing, self.pilot_unit)
        if p.flying_unit_id:
            idx = self.pilot_unit.findData(p.flying_unit_id)
            if idx >= 0:
                self.pilot_unit.setCurrentIndex(idx)
        self.pilot_name.setText(p.pilot_name)
        self.pilot_callsign.setText(p.callsign)
        self.pilot_cep.setValue(p.cep_value)

    def _clear_pilot(self) -> None:
        self.pilot_page.clear_selection()
        self.pilot_wing.setCurrentIndex(0)
        self._refresh_unit_combo(self.pilot_wing, self.pilot_unit)
        self.pilot_name.setText("นักบิน 1")
        self.pilot_callsign.setText("VIPER-01")
        self.pilot_cep.setValue(25.0)

    def _save_pilot(self) -> None:
        if not self._require_scenario():
            return
        wing_id = self.pilot_wing.currentData() or None
        flying_unit_id = self.pilot_unit.currentData() or None
        if flying_unit_id and not wing_id:
            QMessageBox.information(
                self,
                "กรุณาเลือกกองบิน",
                "ต้องเลือกกองบินเมื่อระบุหน่วยบิน",
            )
            return
        data = dict(
            wing_id=wing_id,
            flying_unit_id=flying_unit_id,
            pilot_name=self.pilot_name.text().strip(),
            callsign=self.pilot_callsign.text().strip(),
            cep_value=self.pilot_cep.value(),
        )
        pid = self.pilot_page.selected_id()
        try:
            if pid:
                self.service.update_pilot(UpdatePilotRequest(pilot_id=pid, **data))
                self._after_change("บันทึกนักบินแล้ว")
            else:
                self.service.create_pilot(CreatePilotRequest(scenario_id=self._scenario_id, **data))
                self._clear_pilot()
                self._after_change("เพิ่มนักบินแล้ว")
        except ValueError as e:
            QMessageBox.warning(self, "Guardrail", str(e))

    def _delete_pilot(self) -> None:
        pid = self.pilot_page.selected_id()
        if pid and self._confirm_delete("นักบิน"):
            self.service.delete_pilot(pid)
            self._clear_pilot()
            self._after_change("ลบนักบินแล้ว")

    # --- Depot CRUD ---
    def _load_depot(self, did: str) -> None:
        d = self.service.get_depot(did)
        if not d:
            return
        self._set_wing_combo(self.depot_wing, d.wing_id)
        self.depot_name.setText(d.depot_name)
        self.depot_lat.setValue(d.map_lat or 0)
        self.depot_lng.setValue(d.map_lng or 0)

    def _clear_depot(self) -> None:
        self.depot_page.clear_selection()
        self.depot_wing.setCurrentIndex(0)
        self.depot_name.setText("คลังกลาง")
        self.depot_lat.setValue(0.0)
        self.depot_lng.setValue(0.0)

    def _save_depot(self) -> None:
        if not self._require_scenario():
            return
        wing_id = self._require_wing(self.depot_wing)
        if not wing_id:
            return
        data = dict(
            wing_id=wing_id, depot_name=self.depot_name.text().strip(),
            map_lat=self.depot_lat.value(), map_lng=self.depot_lng.value(),
        )
        did = self.depot_page.selected_id()
        try:
            if did:
                self.service.update_depot(UpdateWingDepotRequest(depot_id=did, **data))
                self._after_change("บันทึกคลังแล้ว")
            else:
                self.service.create_depot(CreateWingDepotRequest(scenario_id=self._scenario_id, **data))
                self._clear_depot()
                self._after_change("เพิ่มคลังแล้ว")
        except ValueError as e:
            QMessageBox.warning(self, "Guardrail", str(e))

    def _delete_depot(self) -> None:
        did = self.depot_page.selected_id()
        if did and self._confirm_delete("คลัง"):
            self.service.delete_depot(did)
            self._clear_depot()
            self._after_change("ลบคลังแล้ว")

    # --- Vehicle CRUD ---
    def _load_vehicle(self, vid: str) -> None:
        v = self.service.get_vehicle(vid)
        if not v:
            return
        self._set_wing_combo(self.vehicle_wing, v.wing_id)
        self.vehicle_name.setText(v.vehicle_name)
        self.vehicle_fuel.setValue(v.fuel_consumption_rate)
        _set_ready(self.vehicle_ready, v.mission_ready)

    def _clear_vehicle(self) -> None:
        self.vehicle_page.clear_selection()
        self.vehicle_wing.setCurrentIndex(0)
        self.vehicle_name.setText("รถบรรทุกน้ำมัน 1")
        self.vehicle_fuel.setValue(12.5)
        _set_ready(self.vehicle_ready, "not_ready")

    def _save_vehicle(self) -> None:
        if not self._require_scenario():
            return
        wing_id = self._require_wing(self.vehicle_wing)
        if not wing_id:
            return
        data = dict(
            wing_id=wing_id, vehicle_name=self.vehicle_name.text().strip(),
            fuel_consumption_rate=self.vehicle_fuel.value(),
            mission_ready=self.vehicle_ready.currentData(),
        )
        vid = self.vehicle_page.selected_id()
        try:
            if vid:
                self.service.update_vehicle(UpdateLogisticsVehicleRequest(vehicle_id=vid, **data))
                self._after_change("บันทึกรถส่งกำลังบำรุงแล้ว")
            else:
                self.service.create_vehicle(CreateLogisticsVehicleRequest(scenario_id=self._scenario_id, **data))
                self._clear_vehicle()
                self._after_change("เพิ่มรถส่งกำลังบำรุงแล้ว")
        except ValueError as e:
            QMessageBox.warning(self, "Guardrail", str(e))

    def _delete_vehicle(self) -> None:
        vid = self.vehicle_page.selected_id()
        if vid and self._confirm_delete("รถส่งกำลังบำรุง"):
            self.service.delete_vehicle(vid)
            self._clear_vehicle()
            self._after_change("ลบรถส่งกำลังบำรุงแล้ว")
