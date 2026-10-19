from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.weaponeering.product_catalog import KNOWN_PRODUCTS
from maap_app.modules.wing_data.schemas import (
    CreateWingProductRequest,
    TransferDepotInventoryRequest,
    UpdateWingProductRequest,
    UpsertDepotInventoryRequest,
)
from maap_app.modules.wing_data.service import WingDataService
from maap_app.ui.panels.wing_form_widgets import (
    _float_spin,
    _form_card,
    _int_spin,
    _table,
)


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setObjectName("Divider")
    return line


class _SupplyPageBase(QWidget):
    def __init__(
        self,
        service: WingDataService,
        get_scenario_id,
        require_scenario,
        confirm_delete,
        on_changed,
    ) -> None:
        super().__init__()
        self.service = service
        self._get_scenario_id = get_scenario_id
        self._require_scenario = require_scenario
        self._confirm_delete = confirm_delete
        self._on_changed = on_changed

    def _set_combo(self, combo: QComboBox, value: str) -> None:
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _populate_depot_combo(self, combo: QComboBox, depots) -> None:
        prev = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("(เลือกคลัง)", "")
        for depot in depots:
            combo.addItem(depot.depot_name, depot.id)
        if prev:
            idx = combo.findData(prev)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _populate_product_combo(self, combo: QComboBox, products) -> None:
        prev = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("(เลือกสินค้า)", "")
        for product in products:
            combo.addItem(product.product_name, product.id)
        if prev:
            idx = combo.findData(prev)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _make_table_host(self, table_widget, on_add) -> QWidget:
        """Wrap a table with a top-bar (search + add button)."""
        host = QWidget()
        vl = QVBoxLayout(host)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        top_bar = QWidget()
        top_bar.setObjectName("TableTopBar")
        tb = QHBoxLayout(top_bar)
        tb.setContentsMargins(10, 8, 10, 8)
        tb.setSpacing(8)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("ค้นหา...")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setObjectName("TableSearchBox")
        self.search_box.textChanged.connect(lambda t: self._filter(table_widget, t))

        self.add_btn = QPushButton("+ เพิ่ม")
        self.add_btn.setObjectName("PrimaryButton")
        self.add_btn.clicked.connect(on_add)

        tb.addWidget(self.search_box, 1)
        tb.addWidget(self.add_btn)
        vl.addWidget(top_bar)
        vl.addWidget(_divider())
        vl.addWidget(table_widget)
        host.setMinimumWidth(300)
        return host

    @staticmethod
    def _filter(table, text: str) -> None:
        text = text.lower().strip()
        for row in range(table.rowCount()):
            if not text:
                table.setRowHidden(row, False)
                continue
            match = any(
                item is not None and text in item.text().lower()
                for item in (table.item(row, col) for col in range(table.columnCount()))
            )
            table.setRowHidden(row, not match)

    def _make_form_scroll(self, form_card: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(260)
        scroll.setMaximumWidth(380)
        scroll.setWidget(form_card)
        return scroll


class ProductCatalogPage(_SupplyPageBase):
    def __init__(self, *args, **kwargs) -> None:
        self._selected_product_id: str | None = None
        super().__init__(*args, **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)

        self.catalog_table = _table(["ชื่อสินค้า", "ปอนด์", "ต้นทุน"])
        self.catalog_table.itemSelectionChanged.connect(self._on_catalog_selected)
        splitter.addWidget(self._make_table_host(self.catalog_table, self._clear_product))

        form_card, form_layout = _form_card(
            "ข้อมูลสินค้า",
            "กำหนดชื่อสินค้า น้ำหนัก (ปอนด์) ต้นทุนต่อหน่วย และรายละเอียด",
        )
        self.editing_label = QLabel()
        self.editing_label.setStyleSheet("color: #60a5fa; font-size: 11px; font-style: italic;")
        self.editing_label.setVisible(False)
        form_layout.addWidget(self.editing_label)

        self.catalog_combo = QComboBox()
        self.catalog_combo.addItem("— กรอกเอง / เลือกคลังมาตรฐาน —", "")
        current_category = None
        for item in KNOWN_PRODUCTS:
            if item.category_label != current_category:
                current_category = item.category_label
                self.catalog_combo.addItem(f"— {current_category} —", "")
                last = self.catalog_combo.model().item(self.catalog_combo.count() - 1)
                if last is not None:
                    last.setEnabled(False)
            self.catalog_combo.addItem(item.product_name, item.key)
        self.catalog_combo.currentIndexChanged.connect(self._apply_catalog_preset)
        form_layout.addWidget(self.catalog_combo)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        self.product_name = QLineEdit("MK-82")
        self.product_pounds = _float_spin(500.0, 9999999)
        self.product_cost = _float_spin(0.0, 999999999)
        self.product_cost.setDecimals(2)
        self.product_description = QPlainTextEdit()
        self.product_description.setPlaceholderText("รายละเอียดสินค้า")
        self.product_description.setMaximumHeight(90)
        grid.addWidget(QLabel("ชื่อสินค้า"), 0, 0)
        grid.addWidget(self.product_name, 0, 1)
        grid.addWidget(QLabel("ปอนด์"), 1, 0)
        grid.addWidget(self.product_pounds, 1, 1)
        grid.addWidget(QLabel("ต้นทุน"), 2, 0)
        grid.addWidget(self.product_cost, 2, 1)
        grid.addWidget(QLabel("รายละเอียด"), 3, 0)
        grid.addWidget(self.product_description, 3, 1)
        form_layout.addLayout(grid)
        form_layout.addStretch(1)
        form_layout.addWidget(_divider())

        self.save_btn = QPushButton("บันทึก")
        self.save_btn.setObjectName("PrimaryButton")
        self.delete_btn = QPushButton("ลบ")
        self.delete_btn.setObjectName("SecondaryButton")
        self.clear_btn = QPushButton("ล้างฟอร์ม")
        self.clear_btn.setObjectName("GhostButton")
        self.delete_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_product)
        self.delete_btn.clicked.connect(self._delete_product)
        self.clear_btn.clicked.connect(self._clear_product)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.addWidget(self.save_btn, 1)
        btn_row.addWidget(self.delete_btn, 1)
        form_layout.addLayout(btn_row)
        form_layout.addWidget(self.clear_btn)

        splitter.addWidget(self._make_form_scroll(form_card))
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        QVBoxLayout(self).addWidget(splitter)

    def refresh(self) -> None:
        scenario_id = self._get_scenario_id()
        if not scenario_id:
            self.catalog_table.setRowCount(0)
            return
        products = self.service.list_products(scenario_id)
        self.catalog_table.setSortingEnabled(False)
        self.catalog_table.setRowCount(len(products))
        for ri, product in enumerate(products):
            cells = [
                product.product_name,
                f"{product.weight_pounds:.0f}",
                f"{product.unit_cost:,.2f}",
            ]
            for ci, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if ci == 0:
                    item.setData(Qt.ItemDataRole.UserRole, product.id)
                self.catalog_table.setItem(ri, ci, item)
        self.catalog_table.setSortingEnabled(True)

    def populate_data(self, data: dict) -> None:
        """Apply pre-fetched data — no DB queries."""
        products = data.get("products", [])
        self.catalog_table.setSortingEnabled(False)
        self.catalog_table.setRowCount(len(products))
        for ri, product in enumerate(products):
            cells = [product.product_name, f"{product.weight_pounds:.0f}", f"{product.unit_cost:,.2f}"]
            for ci, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if ci == 0:
                    item.setData(Qt.ItemDataRole.UserRole, product.id)
                self.catalog_table.setItem(ri, ci, item)
        self.catalog_table.setSortingEnabled(True)

    def _on_catalog_selected(self) -> None:
        row = self.catalog_table.currentRow()
        if row < 0:
            self._selected_product_id = None
            self.delete_btn.setEnabled(False)
            self.editing_label.setVisible(False)
            return
        item = self.catalog_table.item(row, 0)
        self._selected_product_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.delete_btn.setEnabled(bool(self._selected_product_id))
        if self._selected_product_id:
            self.editing_label.setText(f"กำลังแก้ไข: {item.text() if item else ''}")
            self.editing_label.setVisible(True)
            self._load_product(self._selected_product_id)

    def _load_product(self, product_id: str) -> None:
        product = self.service.get_product(product_id)
        if not product:
            return
        self.product_name.setText(product.product_name)
        self.product_pounds.setValue(product.weight_pounds)
        self.product_cost.setValue(product.unit_cost)
        self.product_description.setPlainText(product.description or "")

    def _clear_product(self) -> None:
        self.catalog_table.clearSelection()
        self._selected_product_id = None
        self.delete_btn.setEnabled(False)
        self.editing_label.setVisible(False)
        self.product_name.setText("MK-82")
        self.product_pounds.setValue(500.0)
        self.product_cost.setValue(0.0)
        self.product_description.setPlainText("")
        self.catalog_combo.blockSignals(True)
        self.catalog_combo.setCurrentIndex(0)
        self.catalog_combo.blockSignals(False)

    def _apply_catalog_preset(self) -> None:
        key = self.catalog_combo.currentData()
        if not key:
            return
        item = next((row for row in KNOWN_PRODUCTS if row.key == key), None)
        if item is None:
            return
        self.product_name.setText(item.product_name)
        self.product_pounds.setValue(item.weight_pounds)
        self.product_cost.setValue(item.unit_cost)
        self.product_description.setPlainText(item.description)

    def _save_product(self) -> None:
        if not self._require_scenario():
            return
        scenario_id = self._get_scenario_id()
        data = dict(
            product_name=self.product_name.text().strip(),
            weight_pounds=self.product_pounds.value(),
            unit_cost=self.product_cost.value(),
            description=self.product_description.toPlainText().strip(),
        )
        try:
            if self._selected_product_id:
                self.service.update_product(
                    UpdateWingProductRequest(product_id=self._selected_product_id, **data)
                )
                self._on_changed("บันทึกข้อมูลสินค้าแล้ว")
            else:
                self.service.create_product(
                    CreateWingProductRequest(scenario_id=scenario_id, **data)
                )
                self._clear_product()
                self._on_changed("เพิ่มสินค้าแล้ว")
            self.refresh()
        except ValueError as exc:
            QMessageBox.warning(self, "ไม่สามารถบันทึก", str(exc))

    def _delete_product(self) -> None:
        if not self._selected_product_id or not self._confirm_delete("สินค้า"):
            return
        self.service.delete_product(self._selected_product_id)
        self._clear_product()
        self._on_changed("ลบสินค้าแล้ว")
        self.refresh()


class StockInventoryPage(_SupplyPageBase):
    def __init__(self, *args, **kwargs) -> None:
        self._selected_inventory_id: str | None = None
        super().__init__(*args, **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)

        self.inventory_table = _table(["คลัง", "สินค้า", "จำนวน"])
        self.inventory_table.itemSelectionChanged.connect(self._on_inventory_selected)
        splitter.addWidget(self._make_table_host(self.inventory_table, self._clear_stock))

        form_card, form_layout = _form_card(
            "ข้อมูลสต็อก",
            "ระบุว่าคลังใดมีสินค้าอะไร จำนวนเท่าไหร่",
        )
        self.editing_label = QLabel()
        self.editing_label.setStyleSheet("color: #60a5fa; font-size: 11px; font-style: italic;")
        self.editing_label.setVisible(False)
        form_layout.addWidget(self.editing_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        self.stock_depot = QComboBox()
        self.stock_product = QComboBox()
        self.stock_qty = _int_spin(10)
        grid.addWidget(QLabel("คลัง"), 0, 0)
        grid.addWidget(self.stock_depot, 0, 1)
        grid.addWidget(QLabel("สินค้า"), 1, 0)
        grid.addWidget(self.stock_product, 1, 1)
        grid.addWidget(QLabel("จำนวน"), 2, 0)
        grid.addWidget(self.stock_qty, 2, 1)
        form_layout.addLayout(grid)
        form_layout.addStretch(1)
        form_layout.addWidget(_divider())

        self.save_btn = QPushButton("บันทึก")
        self.save_btn.setObjectName("PrimaryButton")
        self.delete_btn = QPushButton("ลบ")
        self.delete_btn.setObjectName("SecondaryButton")
        self.clear_btn = QPushButton("ล้างฟอร์ม")
        self.clear_btn.setObjectName("GhostButton")
        self.delete_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_stock)
        self.delete_btn.clicked.connect(self._delete_stock)
        self.clear_btn.clicked.connect(self._clear_stock)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.addWidget(self.save_btn, 1)
        btn_row.addWidget(self.delete_btn, 1)
        form_layout.addLayout(btn_row)
        form_layout.addWidget(self.clear_btn)

        splitter.addWidget(self._make_form_scroll(form_card))
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        QVBoxLayout(self).addWidget(splitter)

    def refresh(self) -> None:
        scenario_id = self._get_scenario_id()
        if not scenario_id:
            self.inventory_table.setRowCount(0)
            self._populate_depot_combo(self.stock_depot, [])
            self._populate_product_combo(self.stock_product, [])
            return
        inventory = self.service.list_inventory(scenario_id)
        self.inventory_table.setSortingEnabled(False)
        self.inventory_table.setRowCount(len(inventory))
        for ri, row in enumerate(inventory):
            cells = [row.depot_name, row.product_name, str(row.quantity)]
            for ci, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if ci == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row.id)
                self.inventory_table.setItem(ri, ci, item)
        self.inventory_table.setSortingEnabled(True)
        depots = self.service.list_depots(scenario_id)
        products = self.service.list_products(scenario_id)
        self._populate_depot_combo(self.stock_depot, depots)
        self._populate_product_combo(self.stock_product, products)

    def populate_data(self, data: dict) -> None:
        """Apply pre-fetched data — no DB queries."""
        inventory = data.get("inventory", [])
        depots = data.get("depots", [])
        products = data.get("products", [])
        self.inventory_table.setSortingEnabled(False)
        self.inventory_table.setRowCount(len(inventory))
        for ri, row in enumerate(inventory):
            cells = [row.depot_name, row.product_name, str(row.quantity)]
            for ci, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if ci == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row.id)
                self.inventory_table.setItem(ri, ci, item)
        self.inventory_table.setSortingEnabled(True)
        self._populate_depot_combo(self.stock_depot, depots)
        self._populate_product_combo(self.stock_product, products)

    def _on_inventory_selected(self) -> None:
        row = self.inventory_table.currentRow()
        if row < 0:
            self._selected_inventory_id = None
            self.delete_btn.setEnabled(False)
            self.editing_label.setVisible(False)
            return
        item = self.inventory_table.item(row, 0)
        self._selected_inventory_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.delete_btn.setEnabled(bool(self._selected_inventory_id))
        if not self._selected_inventory_id:
            return
        name = item.text() if item else ""
        self.editing_label.setText(f"กำลังแก้ไข: {name}")
        self.editing_label.setVisible(True)
        scenario_id = self._get_scenario_id()
        if not scenario_id:
            return
        for inv in self.service.list_inventory(scenario_id):
            if inv.id != self._selected_inventory_id:
                continue
            self._set_combo(self.stock_depot, inv.depot_id)
            self._set_combo(self.stock_product, inv.product_id)
            self.stock_qty.setValue(inv.quantity)
            break

    def _clear_stock(self) -> None:
        self.inventory_table.clearSelection()
        self._selected_inventory_id = None
        self.stock_depot.setCurrentIndex(0)
        self.stock_product.setCurrentIndex(0)
        self.stock_qty.setValue(10)
        self.delete_btn.setEnabled(False)
        self.editing_label.setVisible(False)

    def _save_stock(self) -> None:
        if not self._require_scenario():
            return
        scenario_id = self._get_scenario_id()
        depot_id = self.stock_depot.currentData()
        product_id = self.stock_product.currentData()
        if not depot_id or not product_id:
            QMessageBox.information(self, "กรุณาเลือก", "ต้องเลือกคลังและสินค้าก่อนบันทึก")
            return
        try:
            self.service.upsert_inventory(
                UpsertDepotInventoryRequest(
                    scenario_id=scenario_id,
                    depot_id=str(depot_id),
                    product_id=str(product_id),
                    quantity=self.stock_qty.value(),
                )
            )
            self._clear_stock()
            self._on_changed("บันทึกสต็อกในคลังแล้ว")
            self.refresh()
        except ValueError as exc:
            QMessageBox.warning(self, "ไม่สามารถบันทึก", str(exc))

    def _delete_stock(self) -> None:
        if not self._selected_inventory_id or not self._confirm_delete("สต็อกในคลัง"):
            return
        self.service.delete_inventory(self._selected_inventory_id)
        self._clear_stock()
        self._on_changed("ลบสต็อกในคลังแล้ว")
        self.refresh()


class TransferInventoryPage(_SupplyPageBase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)

        self.transfer_table = _table(["จากคลัง", "ไปคลัง", "สินค้า", "จำนวน", "วันที่"])
        splitter.addWidget(self._make_table_host(self.transfer_table, self._clear_transfer))

        form_card, form_layout = _form_card(
            "ย้ายสินค้าระหว่างคลัง",
            "โอนจำนวนสินค้าจากคลังต้นทางไปคลังปลายทาง",
        )
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        self.transfer_from = QComboBox()
        self.transfer_to = QComboBox()
        self.transfer_product = QComboBox()
        self.transfer_qty = _int_spin(1)
        grid.addWidget(QLabel("จากคลัง"), 0, 0)
        grid.addWidget(self.transfer_from, 0, 1)
        grid.addWidget(QLabel("ไปคลัง"), 1, 0)
        grid.addWidget(self.transfer_to, 1, 1)
        grid.addWidget(QLabel("สินค้า"), 2, 0)
        grid.addWidget(self.transfer_product, 2, 1)
        grid.addWidget(QLabel("จำนวนที่ย้าย"), 3, 0)
        grid.addWidget(self.transfer_qty, 3, 1)
        form_layout.addLayout(grid)
        form_layout.addStretch(1)
        form_layout.addWidget(_divider())

        self.transfer_btn = QPushButton("ย้ายสินค้า")
        self.transfer_btn.setObjectName("PrimaryButton")
        self.clear_btn = QPushButton("ล้างฟอร์ม")
        self.clear_btn.setObjectName("GhostButton")
        self.transfer_btn.clicked.connect(self._transfer_stock)
        self.clear_btn.clicked.connect(self._clear_transfer)
        form_layout.addWidget(self.transfer_btn)
        form_layout.addWidget(self.clear_btn)

        splitter.addWidget(self._make_form_scroll(form_card))
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        QVBoxLayout(self).addWidget(splitter)

    def refresh(self) -> None:
        scenario_id = self._get_scenario_id()
        if not scenario_id:
            self.transfer_table.setRowCount(0)
            self._populate_depot_combo(self.transfer_from, [])
            self._populate_depot_combo(self.transfer_to, [])
            self._populate_product_combo(self.transfer_product, [])
            return
        transfers = self.service.list_transfers(scenario_id)
        self.transfer_table.setSortingEnabled(False)
        self.transfer_table.setRowCount(len(transfers))
        for ri, row in enumerate(transfers):
            created = row.created_at or "-"
            if len(created) > 19:
                created = created[:19].replace("T", " ")
            cells = [row.from_depot_name, row.to_depot_name, row.product_name, str(row.quantity), created]
            for ci, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if ci == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row.id)
                self.transfer_table.setItem(ri, ci, item)
        self.transfer_table.setSortingEnabled(True)
        depots = self.service.list_depots(scenario_id)
        products = self.service.list_products(scenario_id)
        self._populate_depot_combo(self.transfer_from, depots)
        self._populate_depot_combo(self.transfer_to, depots)
        self._populate_product_combo(self.transfer_product, products)

    def populate_data(self, data: dict) -> None:
        """Apply pre-fetched data — no DB queries."""
        transfers = data.get("transfers", [])
        depots = data.get("depots", [])
        products = data.get("products", [])
        self.transfer_table.setSortingEnabled(False)
        self.transfer_table.setRowCount(len(transfers))
        for ri, row in enumerate(transfers):
            created = row.created_at or "-"
            if len(created) > 19:
                created = created[:19].replace("T", " ")
            cells = [row.from_depot_name, row.to_depot_name, row.product_name, str(row.quantity), created]
            for ci, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if ci == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row.id)
                self.transfer_table.setItem(ri, ci, item)
        self.transfer_table.setSortingEnabled(True)
        self._populate_depot_combo(self.transfer_from, depots)
        self._populate_depot_combo(self.transfer_to, depots)
        self._populate_product_combo(self.transfer_product, products)

    def _clear_transfer(self) -> None:
        self.transfer_from.setCurrentIndex(0)
        self.transfer_to.setCurrentIndex(0)
        self.transfer_product.setCurrentIndex(0)
        self.transfer_qty.setValue(1)

    def _transfer_stock(self) -> None:
        if not self._require_scenario():
            return
        scenario_id = self._get_scenario_id()
        from_id = self.transfer_from.currentData()
        to_id = self.transfer_to.currentData()
        product_id = self.transfer_product.currentData()
        if not from_id or not to_id or not product_id:
            QMessageBox.information(self, "กรุณาเลือก", "ต้องเลือกคลังต้นทาง ปลายทาง และสินค้า")
            return
        try:
            self.service.transfer_inventory(
                TransferDepotInventoryRequest(
                    scenario_id=scenario_id,
                    from_depot_id=str(from_id),
                    to_depot_id=str(to_id),
                    product_id=str(product_id),
                    quantity=self.transfer_qty.value(),
                )
            )
            self._clear_transfer()
            self._on_changed("ย้ายสินค้าระหว่างคลังแล้ว")
            self.refresh()
        except ValueError as exc:
            QMessageBox.warning(self, "ไม่สามารถย้าย", str(exc))
