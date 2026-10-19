from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.ground_transport.routing import (
    format_distance_m,
    format_duration_min,
)
from maap_app.modules.ground_transport.schemas import CreateGroundTransportRequest
from maap_app.modules.ground_transport.service import (
    GroundTransportService,
    route_mode_label,
)
from maap_app.modules.wing_data.service import WingDataService
from maap_app.ui.panels.wing_form_widgets import _field_row, _form_card, _table


class GroundTransportPage(QWidget):
    def __init__(
        self,
        transport_service: GroundTransportService,
        wing_data_service: WingDataService,
        get_scenario_id,
        require_scenario,
        confirm_delete,
        on_changed,
    ) -> None:
        super().__init__()
        self._transport_service = transport_service
        self._wing_data_service = wing_data_service
        self._get_scenario_id = get_scenario_id
        self._require_scenario = require_scenario
        self._confirm_delete = confirm_delete
        self._on_changed = on_changed
        self._selected_id: str | None = None
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(450)
        self._preview_timer.timeout.connect(self._run_preview_update)
        self._build_ui()

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        table_host = QWidget()
        table_layout = QVBoxLayout(table_host)
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.table = _table(
            [
                "ชื่อเส้นทาง",
                "จาก",
                "ถึง",
                "สินค้า",
                "จำนวน",
                "ระยะทาง",
                "เวลา",
                "ประเภทเส้นทาง",
            ]
        )
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        table_layout.addWidget(self.table)
        splitter.addWidget(table_host)

        form_card, form_layout = _form_card(
            "เพิ่มเส้นทางขนส่งทางบก",
            "เลือกกองบินต้นทางและปลายทาง ระบบจะคำนวณเส้นทางถนนอัตโนมัติ",
        )
        self.origin_combo = QComboBox()
        self.destination_combo = QComboBox()
        self.product_combo = QComboBox()
        self.vehicle_combo = QComboBox()
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 9999)
        self.quantity_spin.setValue(1)
        self.preview_distance = QLabel("—")
        self.preview_distance.setObjectName("MapTargetMetaValue")
        self.preview_duration = QLabel("—")
        self.preview_duration.setObjectName("MapTargetMetaValue")
        self.preview_mode = QLabel("—")
        self.preview_mode.setObjectName("MapTargetMutedLabel")

        form_layout.addWidget(_field_row("กองบินต้นทาง", self.origin_combo))
        form_layout.addWidget(_field_row("กองบินปลายทาง", self.destination_combo))
        form_layout.addWidget(_field_row("สินค้า", self.product_combo))
        form_layout.addWidget(_field_row("รถขนส่ง", self.vehicle_combo))
        form_layout.addWidget(_field_row("จำนวน", self.quantity_spin))
        form_layout.addWidget(_field_row("ระยะทาง (คาดการณ์)", self.preview_distance))
        form_layout.addWidget(_field_row("เวลา (คาดการณ์)", self.preview_duration))
        form_layout.addWidget(self.preview_mode)

        actions = QHBoxLayout()
        self.save_btn = QPushButton("บันทึกเส้นทางขนส่ง")
        self.save_btn.setObjectName("PrimaryButton")
        self.delete_btn = QPushButton("ลบ")
        self.delete_btn.setObjectName("SecondaryButton")
        self.clear_btn = QPushButton("ล้างฟอร์ม")
        self.clear_btn.setObjectName("GhostButton")
        self.delete_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_transport)
        self.delete_btn.clicked.connect(self._delete_transport)
        self.clear_btn.clicked.connect(self._clear_form)
        actions.addWidget(self.save_btn)
        actions.addWidget(self.delete_btn)
        actions.addWidget(self.clear_btn)
        actions.addStretch(1)
        form_layout.addLayout(actions)
        splitter.addWidget(form_card)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        root = QVBoxLayout(self)
        root.addWidget(splitter)

        self.origin_combo.currentIndexChanged.connect(self._schedule_preview)
        self.destination_combo.currentIndexChanged.connect(self._schedule_preview)

    def refresh(self) -> None:
        self._populate_combos()
        scenario_id = self._get_scenario_id()
        if not scenario_id:
            self.table.setRowCount(0)
            self._clear_form()
            return

        wings = {
            wing.id: wing.wing_name
            for wing in self._wing_data_service.list_wings(scenario_id)
        }
        products = {
            product.id: product.product_name
            for product in self._wing_data_service.list_products(scenario_id)
        }
        transports = self._transport_service.list_transports(scenario_id)
        self.table.setRowCount(len(transports))
        for row, transport in enumerate(transports):
            origin_name = wings.get(transport.origin_wing_id, "—")
            dest_name = wings.get(transport.destination_wing_id, "—")
            product_name = products.get(transport.product_id or "", "—")
            cells = [
                transport.label or f"{origin_name} → {dest_name}",
                origin_name,
                dest_name,
                product_name,
                str(transport.quantity),
                format_distance_m(transport.distance_m),
                format_duration_min(transport.duration_min),
                route_mode_label(transport.route_mode),
            ]
            for col, value in enumerate(cells):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, transport.id)
                self.table.setItem(row, col, item)

    def select_transport(self, transport_id: str) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == transport_id:
                self.table.selectRow(row)
                return

    def _populate_combos(self) -> None:
        for combo in (
            self.origin_combo,
            self.destination_combo,
            self.product_combo,
            self.vehicle_combo,
        ):
            combo.blockSignals(True)
            combo.clear()
            combo.blockSignals(False)

        scenario_id = self._get_scenario_id()
        if not scenario_id:
            return

        wings = self._wing_data_service.list_wings(scenario_id)
        for combo, placeholder in (
            (self.origin_combo, "(เลือกกองบินต้นทาง)"),
            (self.destination_combo, "(เลือกกองบินปลายทาง)"),
        ):
            combo.addItem(placeholder, "")
            for wing in wings:
                combo.addItem(wing.wing_name, wing.id)

        self.product_combo.addItem("(ไม่ระบุสินค้า)", "")
        for product in self._wing_data_service.list_products(scenario_id):
            self.product_combo.addItem(product.product_name, product.id)

        self.vehicle_combo.addItem("(ไม่ระบุรถ)", "")
        for vehicle in self._wing_data_service.list_vehicles(scenario_id):
            wing = self._wing_data_service.get_wing(vehicle.wing_id)
            wing_name = wing.wing_name if wing else "กองบิน"
            self.vehicle_combo.addItem(
                f"{vehicle.vehicle_name} · {wing_name}",
                vehicle.id,
            )

    def _schedule_preview(self) -> None:
        if self._selected_id:
            return
        self.preview_distance.setText("…")
        self.preview_duration.setText("…")
        self.preview_mode.setText("กำลังคำนวณเส้นทางถนน…")
        self._preview_timer.start()

    def _run_preview_update(self) -> None:
        if self._selected_id:
            return
        origin_id = str(self.origin_combo.currentData() or "")
        destination_id = str(self.destination_combo.currentData() or "")
        preview = self._transport_service.preview_route(
            origin_wing_id=origin_id,
            destination_wing_id=destination_id,
        )
        if preview is None:
            self.preview_distance.setText("—")
            self.preview_duration.setText("—")
            self.preview_mode.setText("—")
            return
        self.preview_distance.setText(format_distance_m(preview.distance_m))
        self.preview_duration.setText(format_duration_min(preview.duration_min))
        self.preview_mode.setText(route_mode_label(preview.route_mode))

    def _on_row_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            self._selected_id = None
            self.delete_btn.setEnabled(False)
            self._set_form_enabled(True)
            self._clear_form()
            return
        item = self.table.item(row, 0)
        transport_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not transport_id:
            return
        transport = self._transport_service.get_transport(str(transport_id))
        if transport is None:
            return
        self._selected_id = transport.id
        self.delete_btn.setEnabled(True)
        self._set_form_enabled(False)
        self._set_combo(self.origin_combo, transport.origin_wing_id)
        self._set_combo(self.destination_combo, transport.destination_wing_id)
        self._set_combo(self.product_combo, transport.product_id or "")
        self._set_combo(self.vehicle_combo, transport.vehicle_id or "")
        self.quantity_spin.setValue(transport.quantity)
        self.preview_distance.setText(format_distance_m(transport.distance_m))
        self.preview_duration.setText(format_duration_min(transport.duration_min))
        self.preview_mode.setText(route_mode_label(transport.route_mode))

    def _set_combo(self, combo: QComboBox, value: str) -> None:
        if not value:
            combo.setCurrentIndex(0)
            return
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _set_form_enabled(self, enabled: bool) -> None:
        for widget in (
            self.origin_combo,
            self.destination_combo,
            self.product_combo,
            self.vehicle_combo,
            self.quantity_spin,
        ):
            widget.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)

    def _clear_form(self) -> None:
        self.table.clearSelection()
        self._selected_id = None
        self.delete_btn.setEnabled(False)
        self._set_form_enabled(True)
        for combo in (
            self.origin_combo,
            self.destination_combo,
            self.product_combo,
            self.vehicle_combo,
        ):
            combo.setCurrentIndex(0)
        self.quantity_spin.setValue(1)
        self.preview_distance.setText("—")
        self.preview_duration.setText("—")
        self.preview_mode.setText("—")

    def _save_transport(self) -> None:
        if not self._require_scenario():
            return
        scenario_id = self._get_scenario_id()
        if not scenario_id:
            return
        origin_id = str(self.origin_combo.currentData() or "")
        destination_id = str(self.destination_combo.currentData() or "")
        if not origin_id or not destination_id:
            QMessageBox.information(self, "ขนส่งทางบก", "เลือกกองบินต้นทางและปลายทาง")
            return
        product_id = str(self.product_combo.currentData() or "") or None
        vehicle_id = str(self.vehicle_combo.currentData() or "") or None
        self.save_btn.setEnabled(False)
        self.save_btn.setText("กำลังคำนวณเส้นทางถนน…")
        try:
            self._transport_service.create_transport(
                CreateGroundTransportRequest(
                    scenario_id=scenario_id,
                    origin_wing_id=origin_id,
                    destination_wing_id=destination_id,
                    product_id=product_id,
                    vehicle_id=vehicle_id,
                    quantity=self.quantity_spin.value(),
                )
            )
        except ValueError as exc:
            QMessageBox.warning(self, "บันทึกไม่สำเร็จ", str(exc))
            return
        finally:
            self.save_btn.setEnabled(True)
            self.save_btn.setText("บันทึกเส้นทางขนส่ง")
        self._clear_form()
        self.refresh()
        self._on_changed("บันทึกเส้นทางขนส่งแล้ว")

    def _delete_transport(self) -> None:
        if not self._selected_id:
            return
        if not self._confirm_delete("ลบเส้นทางขนส่งที่เลือก?"):
            return
        try:
            self._transport_service.delete_transport(self._selected_id)
        except ValueError as exc:
            QMessageBox.warning(self, "ลบไม่สำเร็จ", str(exc))
            return
        self._clear_form()
        self.refresh()
        self._on_changed("ลบเส้นทางขนส่งแล้ว")
