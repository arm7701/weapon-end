from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.logistics.schemas import (
    CalculateLogisticsRequest,
    CreateDepotRequest,
    CreateOrganizationRequest,
    CreateRouteSegmentRequest,
    CreateSimulatedPlatformRequest,
    UpdateDepotRequest,
    UpdateOrganizationRequest,
    UpdateRouteSegmentRequest,
    UpdateSimulatedPlatformRequest,
)
from maap_app.modules.logistics.service import LogisticsService

_WING_SECTIONS = {
    "wing_data": 0,
    "unit_info": 0,
    "organization": 0,
    "assets": 1,
    "resource_status": 1,
    "depot_supply": 2,
    "route": 3,
}


def _coord_spin(value: float = 16.81230) -> QDoubleSpinBox:
    spin = QDoubleSpinBox()
    spin.setDecimals(5)
    spin.setRange(-180, 180)
    spin.setValue(value)
    return spin


def _table(columns: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    header = table.horizontalHeader()
    header.setStretchLastSection(True)
    header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    return table


class _EntityTableFormPage(QWidget):
    def __init__(
        self,
        columns: list[str],
        form_title: str,
        form_widget: QWidget,
        on_save,
        on_delete,
        on_clear,
        on_row_selected,
    ) -> None:
        super().__init__()
        self._selected_id: str | None = None
        self._on_row_selected = on_row_selected

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        table_host = QWidget()
        table_layout = QVBoxLayout(table_host)
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.table = _table(columns)
        self.table.itemSelectionChanged.connect(self._on_selection)
        table_layout.addWidget(self.table)
        splitter.addWidget(table_host)

        form_host = QWidget()
        form_host.setObjectName("DetailPanel")
        form_outer = QVBoxLayout(form_host)
        form_outer.setContentsMargins(12, 10, 12, 10)
        form_outer.setSpacing(8)

        title = QLabel(form_title)
        title.setStyleSheet("color: #c8d4e0; font-size: 12px; font-weight: 700;")
        form_outer.addWidget(title)
        form_outer.addWidget(form_widget)

        actions = QHBoxLayout()
        self.save_btn = QPushButton("บันทึก")
        self.save_btn.setObjectName("PrimaryButton")
        self.delete_btn = QPushButton("ลบ")
        self.delete_btn.setObjectName("SecondaryButton")
        self.clear_btn = QPushButton("ล้างฟอร์ม")
        self.clear_btn.setObjectName("GhostButton")
        self.delete_btn.setEnabled(False)
        self.save_btn.clicked.connect(on_save)
        self.delete_btn.clicked.connect(on_delete)
        self.clear_btn.clicked.connect(on_clear)
        actions.addWidget(self.save_btn)
        actions.addWidget(self.delete_btn)
        actions.addWidget(self.clear_btn)
        actions.addStretch(1)
        form_outer.addLayout(actions)
        splitter.addWidget(form_host)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([320, 220])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

    def _on_selection(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            self._selected_id = None
            self.delete_btn.setEnabled(False)
            return
        id_item = self.table.item(row, 0)
        self._selected_id = id_item.data(Qt.ItemDataRole.UserRole) if id_item else None
        self.delete_btn.setEnabled(bool(self._selected_id))
        if self._selected_id:
            self._on_row_selected(self._selected_id)

    def selected_id(self) -> str | None:
        return self._selected_id

    def set_rows(self, rows: list[list[str]], ids: list[str]) -> None:
        self.table.setRowCount(len(rows))
        for row_index, (cells, entity_id) in enumerate(zip(rows, ids, strict=True)):
            for col_index, value in enumerate(cells):
                item = QTableWidgetItem(value)
                if col_index == 0:
                    item.setData(Qt.ItemDataRole.UserRole, entity_id)
                self.table.setItem(row_index, col_index, item)

    def clear_selection(self) -> None:
        self.table.clearSelection()
        self._selected_id = None
        self.delete_btn.setEnabled(False)


class AssetsLogisticsPanel(QWidget):
    assets_changed = Signal()
    logistics_calculated = Signal()
    entity_detail_changed = Signal(str, str)

    def __init__(self, logistics_service: LogisticsService) -> None:
        super().__init__()
        self.logistics_service = logistics_service
        self._scenario_id: str | None = None
        self._org_names: dict[str, str] = {}

        self.setObjectName("MapWorkspace")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setObjectName("MapWorkspaceHeader")
        header.setFixedHeight(48)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 14, 0)

        title_block = QVBoxLayout()
        title_block.setSpacing(0)
        title = QLabel("ข้อมูลกองบิน")
        title.setObjectName("MapWorkspaceTitle")
        self.subtitle = QLabel("ข้อมูลกองทัพอากาศ — จัดการองค์กร แพลตฟอร์ม คลัง และเส้นทาง")
        self.subtitle.setObjectName("SectionSubtitle")
        title_block.addWidget(title)
        title_block.addWidget(self.subtitle)
        header_layout.addLayout(title_block)
        header_layout.addStretch(1)

        calc_btn = QPushButton("คำนวณโลจิสติกส์")
        calc_btn.setObjectName("PrimaryButton")
        calc_btn.clicked.connect(self._calculate_logistics)
        header_layout.addWidget(calc_btn)
        root.addWidget(header)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 12, 14, 12)
        body_layout.setSpacing(10)

        self._build_org_form()
        self._build_platform_form()
        self._build_depot_form()
        self._build_route_form()

        self.tabs = QTabWidget()
        self.tabs.setObjectName("WingDataTabs")
        self.org_page = _EntityTableFormPage(
            ["ชื่อ", "Lat", "Lng", "สถานะ"],
            "ฟอร์มองค์กร",
            self.org_form,
            self._save_organization,
            self._delete_organization,
            self._clear_org_form,
            self._load_org_form,
        )
        self.platform_page = _EntityTableFormPage(
            ["รหัส", "องค์กร", "Capability", "Availability", "Readiness"],
            "ฟอร์มแพลตฟอร์ม",
            self.platform_form,
            self._save_platform,
            self._delete_platform,
            self._clear_platform_form,
            self._load_platform_form,
        )
        self.depot_page = _EntityTableFormPage(
            ["ชื่อ", "Lat", "Lng", "ความจุ"],
            "ฟอร์มคลัง/ส่งกำลัง",
            self.depot_form,
            self._save_depot,
            self._delete_depot,
            self._clear_depot_form,
            self._load_depot_form,
        )
        self.route_page = _EntityTableFormPage(
            ["ต้นทาง", "ปลายทาง", "Friction", "Fuel-stop", "Distance"],
            "ฟอร์มเส้นทาง",
            self.route_form,
            self._save_route,
            self._delete_route,
            self._clear_route_form,
            self._load_route_form,
        )
        self.tabs.addTab(self.org_page, "องค์กร")
        self.tabs.addTab(self.platform_page, "แพลตฟอร์ม")
        self.tabs.addTab(self.depot_page, "คลัง/ส่งกำลัง")
        self.tabs.addTab(self.route_page, "เส้นทาง")
        tab_bar = self.tabs.tabBar()
        tab_bar.setElideMode(Qt.TextElideMode.ElideNone)
        tab_bar.setUsesScrollButtons(True)
        tab_bar.setExpanding(True)
        for index, label in enumerate(
            ("องค์กร", "แพลตฟอร์ม", "คลัง/ส่งกำลัง", "เส้นทาง")
        ):
            tab_bar.setTabToolTip(index, label)
        body_layout.addWidget(self.tabs, stretch=1)

        self.status_label = QLabel("เลือกแถวในตารางเพื่อแก้ไข หรือกรอกฟอร์มด้านล่างเพื่อเพิ่มข้อมูลใหม่")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #6b7f96; font-size: 11px;")
        body_layout.addWidget(self.status_label)
        root.addWidget(body, stretch=1)

        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _build_org_form(self) -> None:
        self.org_name = QLineEdit("ORG-ALPHA")
        self.org_location = QLineEdit("synthetic training area")
        self.org_lat = _coord_spin()
        self.org_lng = _coord_spin(100.12345)
        self.org_form = QWidget()
        form = QFormLayout(self.org_form)
        form.addRow("ชื่อ", self.org_name)
        form.addRow("ตำแหน่ง", self.org_location)
        form.addRow("Lat", self.org_lat)
        form.addRow("Lng", self.org_lng)

    def _build_platform_form(self) -> None:
        self.plat_label = QLineEdit("PLAT-01")
        self.plat_org = QComboBox()
        self.plat_capability = QComboBox()
        self.plat_capability.addItems(["low", "medium", "high"])
        self.plat_availability = QSpinBox()
        self.plat_availability.setRange(1, 5)
        self.plat_availability.setValue(3)
        self.plat_readiness = QComboBox()
        self.plat_readiness.addItems(["unknown", "ready", "degraded", "unavailable"])
        self.platform_form = QWidget()
        form = QFormLayout(self.platform_form)
        form.addRow("รหัส", self.plat_label)
        form.addRow("องค์กร", self.plat_org)
        form.addRow("Capability", self.plat_capability)
        form.addRow("Availability", self.plat_availability)
        form.addRow("Readiness", self.plat_readiness)

    def _build_depot_form(self) -> None:
        self.depot_name = QLineEdit("DEPOT-NORTH")
        self.depot_lat = _coord_spin()
        self.depot_lng = _coord_spin(100.12345)
        self.depot_capacity = QSpinBox()
        self.depot_capacity.setRange(1, 100)
        self.depot_capacity.setValue(50)
        self.depot_form = QWidget()
        form = QFormLayout(self.depot_form)
        form.addRow("ชื่อ", self.depot_name)
        form.addRow("Lat", self.depot_lat)
        form.addRow("Lng", self.depot_lng)
        form.addRow("ความจุ", self.depot_capacity)

    def _build_route_form(self) -> None:
        self.route_origin = QComboBox()
        self.route_dest = QComboBox()
        self.route_friction = QSpinBox()
        self.route_friction.setRange(1, 100)
        self.route_friction.setValue(40)
        self.route_fuel = QSpinBox()
        self.route_fuel.setRange(1, 100)
        self.route_fuel.setValue(50)
        self.route_distance = QSpinBox()
        self.route_distance.setRange(1, 100)
        self.route_distance.setValue(50)
        self.route_form = QWidget()
        form = QFormLayout(self.route_form)
        form.addRow("ต้นทาง", self.route_origin)
        form.addRow("ปลายทาง", self.route_dest)
        form.addRow("Friction", self.route_friction)
        form.addRow("Fuel-stop", self.route_fuel)
        form.addRow("Distance", self.route_distance)

    def activate_section(self, section_key: str) -> None:
        self.tabs.setCurrentIndex(_WING_SECTIONS.get(section_key, 0))

    def set_scenario(self, scenario_id: str | None) -> None:
        self._scenario_id = scenario_id
        if scenario_id:
            self.subtitle.setText(f"ข้อมูลกองทัพอากาศ | {scenario_id[:8]}...")
        else:
            self.subtitle.setText("ยังไม่มี scenario ที่ใช้งาน")
        self.refresh()

    def refresh(self) -> None:
        self._refresh_entity_combos()
        if not self._scenario_id:
            for page in (
                self.org_page,
                self.platform_page,
                self.depot_page,
                self.route_page,
            ):
                page.set_rows([], [])
            return

        orgs = self.logistics_service.list_organizations(self._scenario_id)
        self._org_names = {org.id: org.name for org in orgs}
        self.org_page.set_rows(
            [
                [
                    org.name,
                    _fmt_coord(org.map_lat),
                    _fmt_coord(org.map_lng),
                    org.readiness_summary,
                ]
                for org in orgs
            ],
            [org.id for org in orgs],
        )

        platforms = self.logistics_service.list_simulated_platforms(self._scenario_id)
        self.platform_page.set_rows(
            [
                [
                    platform.label,
                    self._org_names.get(platform.organization_id or "", "-"),
                    platform.capability_band,
                    str(platform.availability_score),
                    platform.readiness_status,
                ]
                for platform in platforms
            ],
            [platform.id for platform in platforms],
        )

        depots = self.logistics_service.list_depots(self._scenario_id)
        self.depot_page.set_rows(
            [
                [
                    depot.name,
                    _fmt_coord(depot.map_lat),
                    _fmt_coord(depot.map_lng),
                    str(depot.capacity_score),
                ]
                for depot in depots
            ],
            [depot.id for depot in depots],
        )

        routes = self.logistics_service.list_route_segments(self._scenario_id)
        self.route_page.set_rows(
            [
                [
                    self._entity_label(route.origin_entity_type, route.origin_entity_id),
                    self._entity_label(
                        route.destination_entity_type, route.destination_entity_id
                    ),
                    str(route.route_friction_score),
                    str(route.fuel_stop_score),
                    str(route.distance_score),
                ]
                for route in routes
            ],
            [route.id for route in routes],
        )

    def show_entity_detail(self, entity_type: str, entity_id: str) -> None:
        if entity_type == "organization":
            self.activate_section("organization")
            self._select_table_row(self.org_page.table, entity_id)
            self._load_org_form(entity_id)
        elif entity_type == "depot":
            self.activate_section("depot_supply")
            self._select_table_row(self.depot_page.table, entity_id)
            self._load_depot_form(entity_id)
        elif entity_type == "route":
            self.activate_section("route")
            self._select_table_row(self.route_page.table, entity_id)
            self._load_route_form(entity_id)

    def _select_table_row(self, table: QTableWidget, entity_id: str) -> None:
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == entity_id:
                table.selectRow(row)
                return

    def _entity_label(self, entity_type: str, entity_id: str) -> str:
        if entity_type == "organization":
            return self._org_names.get(entity_id, entity_id[:8])
        if entity_type == "depot":
            depot = self.logistics_service.get_depot(entity_id)
            return depot.name if depot else entity_id[:8]
        return f"{entity_type}:{entity_id[:8]}"

    def _refresh_entity_combos(self) -> None:
        for combo in (self.plat_org, self.route_origin, self.route_dest):
            combo.clear()
            combo.addItem("(ไม่ระบุ)", "")
        if not self._scenario_id:
            return
        for org in self.logistics_service.list_organizations(self._scenario_id):
            self.plat_org.addItem(org.name, org.id)
            payload = ("organization", org.id, org.map_lat, org.map_lng)
            label = f"org:{org.name}"
            self.route_origin.addItem(label, payload)
            self.route_dest.addItem(label, payload)
        for depot in self.logistics_service.list_depots(self._scenario_id):
            payload = ("depot", depot.id, depot.map_lat, depot.map_lng)
            label = f"depot:{depot.name}"
            self.route_origin.addItem(label, payload)
            self.route_dest.addItem(label, payload)

    def _on_tab_changed(self) -> None:
        self.status_label.setText("เลือกแถวในตารางเพื่อแก้ไข หรือกรอกฟอร์มด้านล่างเพื่อเพิ่มข้อมูลใหม่")

    def _require_scenario(self) -> bool:
        if self._scenario_id:
            return True
        QMessageBox.warning(self, "ไม่มี scenario", "ยังไม่มี scenario ที่ใช้งาน")
        return False

    def _guardrail_error(self, exc: ValueError) -> None:
        QMessageBox.warning(self, "Guardrail", str(exc))

    def _confirm_delete(self, label: str) -> bool:
        answer = QMessageBox.question(
            self,
            "ยืนยันการลบ",
            f"ลบ{label}ที่เลือกออกจากระบบ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _after_change(self, message: str = "") -> None:
        self.refresh()
        self.assets_changed.emit()
        if message:
            self.status_label.setText(message)

    def _load_org_form(self, org_id: str) -> None:
        org = self.logistics_service.get_organization(org_id)
        if not org:
            return
        self.org_name.setText(org.name)
        self.org_location.setText(org.location_label or "")
        self.org_lat.setValue(org.map_lat if org.map_lat is not None else 0.0)
        self.org_lng.setValue(org.map_lng if org.map_lng is not None else 0.0)
        self.status_label.setText(f"กำลังแก้ไของค์กร: {org.name}")

    def _clear_org_form(self) -> None:
        self.org_page.clear_selection()
        self.org_name.setText("ORG-ALPHA")
        self.org_location.setText("synthetic training area")
        self.org_lat.setValue(16.81230)
        self.org_lng.setValue(100.12345)
        self.status_label.setText("พร้อมเพิ่มองค์กรใหม่")

    def _save_organization(self) -> None:
        if not self._require_scenario():
            return
        data = {
            "name": self.org_name.text().strip(),
            "organization_type": "unit",
            "location_label": self.org_location.text().strip(),
            "map_lat": self.org_lat.value(),
            "map_lng": self.org_lng.value(),
        }
        org_id = self.org_page.selected_id()
        try:
            if org_id:
                existing = self.logistics_service.get_organization(org_id)
                if existing:
                    data["organization_type"] = existing.organization_type
                self.logistics_service.update_organization(
                    UpdateOrganizationRequest(organization_id=org_id, **data)
                )
                self._after_change(f"บันทึกการแก้ไของค์กร {data['name']} แล้ว")
            else:
                self.logistics_service.create_organization(
                    CreateOrganizationRequest(scenario_id=self._scenario_id, **data)
                )
                self._clear_org_form()
                self._after_change(f"เพิ่มองค์กร {data['name']} แล้ว")
        except ValueError as exc:
            self._guardrail_error(exc)

    def _delete_organization(self) -> None:
        org_id = self.org_page.selected_id()
        if not org_id or not self._confirm_delete("องค์กร"):
            return
        self.logistics_service.delete_organization(org_id)
        self._clear_org_form()
        self._after_change("ลบองค์กรแล้ว")

    def _load_platform_form(self, platform_id: str) -> None:
        platform = self.logistics_service.get_simulated_platform(platform_id)
        if not platform:
            return
        self.plat_label.setText(platform.label)
        if platform.organization_id:
            index = self.plat_org.findData(platform.organization_id)
            if index >= 0:
                self.plat_org.setCurrentIndex(index)
        self.plat_capability.setCurrentText(platform.capability_band)
        self.plat_availability.setValue(platform.availability_score)
        self.plat_readiness.setCurrentText(platform.readiness_status)
        self.status_label.setText(f"กำลังแก้ไขแพลตฟอร์ม: {platform.label}")

    def _clear_platform_form(self) -> None:
        self.platform_page.clear_selection()
        self.plat_label.setText("PLAT-01")
        self.plat_org.setCurrentIndex(0)
        self.plat_capability.setCurrentIndex(1)
        self.plat_availability.setValue(3)
        self.plat_readiness.setCurrentIndex(0)
        self.status_label.setText("พร้อมเพิ่มแพลตฟอร์มใหม่")

    def _save_platform(self) -> None:
        if not self._require_scenario():
            return
        org_id = self.plat_org.currentData() or None
        data = {
            "label": self.plat_label.text().strip(),
            "organization_id": org_id,
            "capability_band": self.plat_capability.currentText(),
            "availability_score": self.plat_availability.value(),
            "readiness_status": self.plat_readiness.currentText(),
        }
        platform_id = self.platform_page.selected_id()
        try:
            if platform_id:
                self.logistics_service.update_simulated_platform(
                    UpdateSimulatedPlatformRequest(platform_id=platform_id, **data)
                )
                self._after_change(f"บันทึกการแก้ไขแพลตฟอร์ม {data['label']} แล้ว")
            else:
                self.logistics_service.create_simulated_platform(
                    CreateSimulatedPlatformRequest(scenario_id=self._scenario_id, **data)
                )
                self._clear_platform_form()
                self._after_change(f"เพิ่มแพลตฟอร์ม {data['label']} แล้ว")
        except ValueError as exc:
            self._guardrail_error(exc)

    def _delete_platform(self) -> None:
        platform_id = self.platform_page.selected_id()
        if not platform_id or not self._confirm_delete("แพลตฟอร์ม"):
            return
        self.logistics_service.delete_simulated_platform(platform_id)
        self._clear_platform_form()
        self._after_change("ลบแพลตฟอร์มแล้ว")

    def _load_depot_form(self, depot_id: str) -> None:
        depot = self.logistics_service.get_depot(depot_id)
        if not depot:
            return
        self.depot_name.setText(depot.name)
        self.depot_lat.setValue(depot.map_lat if depot.map_lat is not None else 0.0)
        self.depot_lng.setValue(depot.map_lng if depot.map_lng is not None else 0.0)
        self.depot_capacity.setValue(depot.capacity_score)
        self.status_label.setText(f"กำลังแก้ไขคลัง: {depot.name}")

    def _clear_depot_form(self) -> None:
        self.depot_page.clear_selection()
        self.depot_name.setText("DEPOT-NORTH")
        self.depot_lat.setValue(16.81230)
        self.depot_lng.setValue(100.12345)
        self.depot_capacity.setValue(50)
        self.status_label.setText("พร้อมเพิ่มคลังใหม่")

    def _save_depot(self) -> None:
        if not self._require_scenario():
            return
        data = {
            "name": self.depot_name.text().strip(),
            "depot_type": "abstract_store",
            "map_lat": self.depot_lat.value(),
            "map_lng": self.depot_lng.value(),
            "capacity_score": self.depot_capacity.value(),
        }
        depot_id = self.depot_page.selected_id()
        try:
            if depot_id:
                existing = self.logistics_service.get_depot(depot_id)
                if existing:
                    data["depot_type"] = existing.depot_type
                self.logistics_service.update_depot(
                    UpdateDepotRequest(depot_id=depot_id, **data)
                )
                self._after_change(f"บันทึกการแก้ไขคลัง {data['name']} แล้ว")
            else:
                self.logistics_service.create_depot(
                    CreateDepotRequest(scenario_id=self._scenario_id, **data)
                )
                self._clear_depot_form()
                self._after_change(f"เพิ่มคลัง {data['name']} แล้ว")
        except ValueError as exc:
            self._guardrail_error(exc)

    def _delete_depot(self) -> None:
        depot_id = self.depot_page.selected_id()
        if not depot_id or not self._confirm_delete("คลัง"):
            return
        self.logistics_service.delete_depot(depot_id)
        self._clear_depot_form()
        self._after_change("ลบคลังแล้ว")

    def _load_route_form(self, route_id: str) -> None:
        route = self.logistics_service.get_route_segment(route_id)
        if not route:
            return
        self._set_route_combo(
            self.route_origin,
            route.origin_entity_type,
            route.origin_entity_id,
        )
        self._set_route_combo(
            self.route_dest,
            route.destination_entity_type,
            route.destination_entity_id,
        )
        self.route_friction.setValue(route.route_friction_score)
        self.route_fuel.setValue(route.fuel_stop_score)
        self.route_distance.setValue(route.distance_score)
        self.route_origin.setEnabled(False)
        self.route_dest.setEnabled(False)
        self.status_label.setText("กำลังแก้ไขเส้นทาง — แก้ไขคะแนนได้ ต้นทาง/ปลายทางล็อก")

    def _set_route_combo(self, combo: QComboBox, entity_type: str, entity_id: str) -> None:
        for index in range(combo.count()):
            payload = combo.itemData(index)
            if payload and payload[0] == entity_type and payload[1] == entity_id:
                combo.setCurrentIndex(index)
                return

    def _clear_route_form(self) -> None:
        self.route_page.clear_selection()
        self.route_origin.setCurrentIndex(0)
        self.route_dest.setCurrentIndex(0)
        self.route_origin.setEnabled(True)
        self.route_dest.setEnabled(True)
        self.route_friction.setValue(40)
        self.route_fuel.setValue(50)
        self.route_distance.setValue(50)
        self.status_label.setText("พร้อมเพิ่มเส้นทางใหม่")

    def _save_route(self) -> None:
        if not self._require_scenario():
            return
        route_id = self.route_page.selected_id()
        try:
            if route_id:
                self.logistics_service.update_route_segment(
                    UpdateRouteSegmentRequest(
                        route_id=route_id,
                        route_friction_score=self.route_friction.value(),
                        fuel_stop_score=self.route_fuel.value(),
                        distance_score=self.route_distance.value(),
                    )
                )
                self._after_change("บันทึกการแก้ไขเส้นทางแล้ว")
                return

            origin = self.route_origin.currentData()
            dest = self.route_dest.currentData()
            if not origin or not dest:
                QMessageBox.information(self, "เส้นทาง", "เลือกต้นทางและปลายทาง")
                return
            self.logistics_service.create_route_segment(
                CreateRouteSegmentRequest(
                    scenario_id=self._scenario_id,
                    origin_entity_type=origin[0],
                    origin_entity_id=origin[1],
                    destination_entity_type=dest[0],
                    destination_entity_id=dest[1],
                    origin_lat=origin[2],
                    origin_lng=origin[3],
                    destination_lat=dest[2],
                    destination_lng=dest[3],
                    route_friction_score=self.route_friction.value(),
                    fuel_stop_score=self.route_fuel.value(),
                    distance_score=self.route_distance.value(),
                )
            )
            self._clear_route_form()
            self._after_change("เพิ่มเส้นทางแล้ว")
        except ValueError as exc:
            self._guardrail_error(exc)

    def _delete_route(self) -> None:
        route_id = self.route_page.selected_id()
        if not route_id or not self._confirm_delete("เส้นทาง"):
            return
        self.logistics_service.delete_route_segment(route_id)
        self._clear_route_form()
        self._after_change("ลบเส้นทางแล้ว")

    def _calculate_logistics(self) -> None:
        if not self._scenario_id:
            return
        routes = self.logistics_service.list_route_segments(self._scenario_id)
        route_id = routes[-1].id if routes else None
        result = self.logistics_service.calculate_logistics_feasibility(
            CalculateLogisticsRequest(
                scenario_id=self._scenario_id,
                route_segment_id=route_id,
            )
        )
        warning_text = (
            "\n".join(f"• {warning}" for warning in result.warnings)
            if result.warnings
            else "ไม่มีคำเตือน"
        )
        self.status_label.setText(
            f"คะแนนโลจิสติกส์: {result.score}/100 — {result.rationale} | {warning_text}"
        )
        self.logistics_calculated.emit()


def _fmt_coord(value: float | None) -> str:
    return f"{value:.5f}" if value is not None else "-"
