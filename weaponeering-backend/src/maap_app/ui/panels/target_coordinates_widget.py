from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.target.models import TargetCoordinate
from maap_app.modules.target.schemas import TargetCoordinateInput
from maap_app.ui.components.embedded_map_picker import EmbeddedMapPickerWidget


def _coord_field() -> QLineEdit:
    field = QLineEdit()
    field.setPlaceholderText("—")
    return field


class _TargetCoordinateRow(QWidget):
    primary_toggled = Signal(object)

    def __init__(self, *, default_label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.label_input = QLineEdit(default_label)
        self.lat_input = _coord_field()
        self.lng_input = _coord_field()
        self.primary_radio = QRadioButton("หลัก")
        self.primary_radio.toggled.connect(self._emit_primary_toggled)
        self.remove_btn = QPushButton("ลบ")
        self.remove_btn.setObjectName("GhostButton")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.label_input, stretch=1)
        layout.addWidget(self.lat_input, stretch=1)
        layout.addWidget(self.lng_input, stretch=1)
        layout.addWidget(self.primary_radio)
        layout.addWidget(self.remove_btn)

    def _emit_primary_toggled(self, checked: bool) -> None:
        if checked:
            self.primary_toggled.emit(self)

    def set_primary(self, is_primary: bool) -> None:
        self.primary_radio.blockSignals(True)
        self.primary_radio.setChecked(is_primary)
        self.primary_radio.blockSignals(False)

    def values(self) -> TargetCoordinateInput | None:
        lat = self._coord_value(self.lat_input)
        lng = self._coord_value(self.lng_input)
        if lat is None or lng is None:
            return None
        return TargetCoordinateInput(
            label=self.label_input.text().strip(),
            map_lat=lat,
            map_lng=lng,
            is_primary=self.primary_radio.isChecked(),
        )

    def set_values(
        self,
        *,
        label: str,
        lat: float,
        lng: float,
        is_primary: bool,
    ) -> None:
        self.label_input.setText(label)
        self.lat_input.setText(f"{lat:.5f}")
        self.lng_input.setText(f"{lng:.5f}")
        self.set_primary(is_primary)

    @staticmethod
    def _coord_value(field: QLineEdit) -> float | None:
        text = field.text().strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None


class TargetCoordinatesWidget(QWidget):
    map_search_requested = Signal(float, float)
    map_picker_visibility_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[_TargetCoordinateRow] = []
        self._pending_pick_row: _TargetCoordinateRow | None = None
        self._embedded_map: EmbeddedMapPickerWidget | None = None
        self._build_ui()
        self.add_row()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        header = QLabel("รายการพิกัด (เพิ่มได้หลายจุดต่อเป้าหมาย) · คลิกขวาบนแผนที่หลักเพื่อสร้างเป้าหมายใหม่")
        header.setStyleSheet("color: #6b7f96; font-size: 10px;")
        root.addWidget(header)

        columns = QWidget()
        columns_layout = QHBoxLayout(columns)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(6)
        columns_layout.addWidget(QLabel("ชื่อจุด"), stretch=1)
        columns_layout.addWidget(QLabel("LAT"), stretch=1)
        columns_layout.addWidget(QLabel("LNG"), stretch=1)
        columns_layout.addWidget(QLabel(""))
        columns_layout.addWidget(QLabel(""))
        root.addWidget(columns)

        self.rows_host = QVBoxLayout()
        self.rows_host.setContentsMargins(0, 0, 0, 0)
        self.rows_host.setSpacing(4)
        root.addLayout(self.rows_host)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.add_row_btn = QPushButton("+ เพิ่มพิกัด")
        self.add_row_btn.setObjectName("SecondaryButton")
        self.add_row_btn.clicked.connect(self.add_row)
        self.pick_map_btn = QPushButton("พิกัด")
        self.pick_map_btn.setObjectName("PrimaryButton")
        self.pick_map_btn.setCheckable(True)
        self.pick_map_btn.setToolTip(
            "เปิด/ปิดแผนที่ Cesium เลือกพิกัด (มีเส้นแบ่งเขตประเทศไทย)"
        )
        self.pick_map_btn.toggled.connect(self._toggle_embedded_map)
        self.search_btn = QPushButton("ดูบนแผนที่หลัก")
        self.search_btn.setObjectName("SecondaryButton")
        self.search_btn.setToolTip("ไปยังแผนที่หลักของระบบ")
        self.search_btn.clicked.connect(self._on_search)
        actions.addWidget(self.add_row_btn)
        actions.addWidget(self.pick_map_btn)
        actions.addWidget(self.search_btn)
        root.addLayout(actions)

    def _get_embedded_map(self) -> EmbeddedMapPickerWidget:
        if self._embedded_map is None:
            self._embedded_map = EmbeddedMapPickerWidget()
            self._embedded_map.coordinate_picked.connect(self._on_embedded_map_pick)
        return self._embedded_map

    def take_map_picker(self) -> EmbeddedMapPickerWidget:
        return self._get_embedded_map()

    def detach_map_picker(self) -> None:
        if self._embedded_map is not None:
            self._embedded_map.setParent(None)
            self._embedded_map.hide()

    def is_map_picker_visible(self) -> bool:
        return self.pick_map_btn.isChecked()

    def set_pending_pick_row(self, row: _TargetCoordinateRow) -> None:
        self._pending_pick_row = row

    def refresh_map_picker(self) -> None:
        picker = self._get_embedded_map()
        center = self.primary_coordinate()
        if center is not None:
            picker.center_on(center[0], center[1], zoom=11)
        else:
            picker.center_on(15.0, 101.0, zoom=6)
        picker.refresh_layout()

    def add_row(self) -> _TargetCoordinateRow:
        index = len(self._rows) + 1
        row = _TargetCoordinateRow(default_label=f"P{index}")
        row.remove_btn.clicked.connect(lambda _checked=False, item=row: self._remove_row(item))
        row.primary_toggled.connect(self._on_primary_toggled)
        row.lat_input.installEventFilter(self)
        row.lng_input.installEventFilter(self)
        self._rows.append(row)
        self.rows_host.addWidget(row)
        if len(self._rows) == 1:
            row.set_primary(True)
        return row

    def clear_rows(self) -> None:
        while self._rows:
            self._remove_row(self._rows[0], ensure_minimum=False)
        self.add_row()

    def set_coordinates(self, coordinates: list[TargetCoordinate]) -> None:
        while self._rows:
            self._remove_row(self._rows[0], ensure_minimum=False)
        if not coordinates:
            self.add_row()
            return
        for index, coord in enumerate(coordinates):
            row = self.add_row()
            row.set_values(
                label=coord.label or f"P{index + 1}",
                lat=coord.map_lat,
                lng=coord.map_lng,
                is_primary=coord.is_primary,
            )

    def get_coordinates(self) -> list[TargetCoordinateInput]:
        values = [row.values() for row in self._rows]
        return [value for value in values if value is not None]

    def primary_coordinate(self) -> tuple[float, float] | None:
        for row in self._rows:
            values = row.values()
            if values is not None and values.is_primary:
                return values.map_lat, values.map_lng
        for row in self._rows:
            values = row.values()
            if values is not None:
                return values.map_lat, values.map_lng
        return None

    def apply_map_coordinate(self, lat: float, lng: float) -> None:
        row = self._pending_pick_row
        if row is None:
            row = next(
                (item for item in self._rows if item.values() is None),
                None,
            )
        if row is None:
            row = self.add_row()
        row.set_values(
            label=row.label_input.text().strip() or f"P{self._rows.index(row) + 1}",
            lat=lat,
            lng=lng,
            is_primary=row.primary_radio.isChecked() or len(self.get_coordinates()) == 0,
        )
        if len(self.get_coordinates()) == 1:
            row.set_primary(True)
        self._pending_pick_row = row

    def hide_embedded_map(self) -> None:
        if self.pick_map_btn.isChecked():
            self.pick_map_btn.blockSignals(True)
            self.pick_map_btn.setChecked(False)
            self.pick_map_btn.blockSignals(False)
            self.map_picker_visibility_changed.emit(False)
        if self._embedded_map is not None:
            self._embedded_map.hide()

    def _toggle_embedded_map(self, checked: bool) -> None:
        self.map_picker_visibility_changed.emit(checked)
        if not checked:
            if self._embedded_map is not None:
                self._embedded_map.hide()
            return
        self._pending_pick_row = next(
            (row for row in self._rows if row.values() is None),
            self._rows[-1] if self._rows else None,
        )
        picker = self._get_embedded_map()
        picker.setVisible(True)
        picker.ensure_loaded()
        self.refresh_map_picker()

    def _on_embedded_map_pick(self, lat: float, lng: float) -> None:
        self.apply_map_coordinate(lat, lng)

    def eventFilter(self, obj, event) -> bool:  # type: ignore[override]
        if event.type() == QEvent.Type.MouseButtonPress:
            for row in self._rows:
                if obj is row.lat_input or obj is row.lng_input:
                    self._pending_pick_row = row
                    break
        return super().eventFilter(obj, event)

    def _remove_row(self, row: _TargetCoordinateRow, *, ensure_minimum: bool = True) -> None:
        if row not in self._rows:
            return
        if ensure_minimum and len(self._rows) <= 1:
            row.label_input.clear()
            row.lat_input.clear()
            row.lng_input.clear()
            row.set_primary(True)
            return
        was_primary = row.primary_radio.isChecked()
        self._rows.remove(row)
        self.rows_host.removeWidget(row)
        if self._pending_pick_row is row:
            self._pending_pick_row = None
        row.deleteLater()
        if was_primary and self._rows:
            self._rows[0].set_primary(True)

    def _on_primary_toggled(self, row: _TargetCoordinateRow) -> None:
        for item in self._rows:
            if item is not row:
                item.set_primary(False)

    def _on_search(self) -> None:
        primary = self.primary_coordinate()
        if primary is None:
            for row in self._rows:
                values = row.values()
                if values is not None:
                    primary = (values.map_lat, values.map_lng)
                    break
        if primary is None:
            return
        self.map_search_requested.emit(primary[0], primary[1])
