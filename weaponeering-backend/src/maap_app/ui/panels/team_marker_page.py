from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.team_marker.constants import UNIT_TYPES
from maap_app.modules.team_marker.service import TeamMarkerService
from maap_app.ui.panels.wing_form_widgets import _form_card, _table


def _fmt_side(side: str) -> str:
    normalized = (side or "").strip().lower()
    if normalized == "blue":
        return "Blue"
    if normalized == "red":
        return "Red"
    return side or "-"


def _fmt_unit_type(unit_type: str) -> str:
    normalized = (unit_type or "generic").strip().lower()
    return UNIT_TYPES.get(normalized, normalized or "-")


def _fmt_coord(value: float) -> str:
    return f"{value:.5f}"


def _fmt_radius(radius_m: float | None) -> str:
    if radius_m is None:
        return "-"
    if radius_m >= 1000:
        return f"{radius_m / 1000:.1f} km"
    return f"{radius_m:.0f} m"


class TeamMarkerPage(QWidget):
    def __init__(
        self,
        team_marker_service: TeamMarkerService,
        get_scenario_id,
        require_scenario,
        confirm_delete,
        on_changed,
    ) -> None:
        super().__init__()
        self._team_marker_service = team_marker_service
        self._get_scenario_id = get_scenario_id
        self._require_scenario = require_scenario
        self._confirm_delete = confirm_delete
        self._on_changed = on_changed
        self._selected_id: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        card, card_layout = _form_card(
            "หน่วย Blue / Red บนแผนที่",
            "รายการหน่วยที่วางด้วยคลิกขวาบนแผนที่ · เลือกแถวแล้วกดลบเพื่อเอาออกจากแผนที่",
        )
        self.table = _table(
            [
                "ฝ่าย",
                "ชื่อ",
                "ประเภท",
                "Lat",
                "Lng",
                "รัศมี",
            ]
        )
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        card_layout.addWidget(self.table)

        actions = QHBoxLayout()
        self.delete_btn = QPushButton("ลบรายการที่เลือก")
        self.delete_btn.setObjectName("SecondaryButton")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_selected)
        self.refresh_btn = QPushButton("รีเฟรช")
        self.refresh_btn.setObjectName("GhostButton")
        self.refresh_btn.clicked.connect(self.refresh)
        actions.addWidget(self.delete_btn)
        actions.addWidget(self.refresh_btn)
        actions.addStretch(1)
        card_layout.addLayout(actions)

        self.summary_label = QLabel("ยังไม่มีหน่วยบนแผนที่")
        self.summary_label.setObjectName("SectionSubtitle")
        card_layout.addWidget(self.summary_label)
        root.addWidget(card)

    def refresh(self) -> None:
        scenario_id = self._get_scenario_id()
        self.table.clearSelection()
        self._selected_id = None
        self.delete_btn.setEnabled(False)

        if not scenario_id:
            self.table.setRowCount(0)
            self.summary_label.setText("ยังไม่มี scenario ที่ใช้งาน")
            return

        markers = sorted(
            self._team_marker_service.list_markers(scenario_id),
            key=lambda marker: (
                0 if marker.side == "blue" else 1,
                marker.label.lower(),
            ),
        )
        self.table.setRowCount(len(markers))
        blue_count = 0
        red_count = 0
        for row, marker in enumerate(markers):
            if marker.side == "blue":
                blue_count += 1
            else:
                red_count += 1
            cells = [
                _fmt_side(marker.side),
                marker.label,
                _fmt_unit_type(marker.unit_type),
                _fmt_coord(marker.map_lat),
                _fmt_coord(marker.map_lng),
                _fmt_radius(marker.radius_m),
            ]
            for col, value in enumerate(cells):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, marker.id)
                    if marker.side == "blue":
                        item.setForeground(Qt.GlobalColor.cyan)
                    else:
                        item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, col, item)

        if not markers:
            self.summary_label.setText(
                "ยังไม่มีหน่วยบนแผนที่ · คลิกขวาบนแผนที่เพื่อเพิ่ม Blue หรือ Red"
            )
        else:
            self.summary_label.setText(
                f"รวม {len(markers)} รายการ · Blue {blue_count} · Red {red_count}"
            )

    def select_marker(self, marker_id: str) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == marker_id:
                self.table.selectRow(row)
                return

    def _on_row_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            self._selected_id = None
            self.delete_btn.setEnabled(False)
            return
        item = self.table.item(row, 0)
        self._selected_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.delete_btn.setEnabled(bool(self._selected_id))

    def _delete_selected(self) -> None:
        if not self._selected_id:
            return
        if not self._confirm_delete("ลบหน่วย Blue/Red ที่เลือกออกจากแผนที่?"):
            return
        try:
            self._team_marker_service.delete_marker(self._selected_id)
        except ValueError as exc:
            QMessageBox.warning(self, "ลบไม่สำเร็จ", str(exc))
            return
        self.refresh()
        self._on_changed("ลบหน่วยบนแผนที่แล้ว")
