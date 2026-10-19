from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.flight_route.params import MAX_FLIGHT_ALTITUDE_FT


class MapFlightRouteEditorCard(QWidget):
    """Route editor section embedded at the bottom of the target detail overlay."""

    waypoint_labels_visibility_changed = Signal(bool)
    closed = Signal()
    approve_requested = Signal()
    delete_waypoint_requested = Signal()
    waypoint_label_changed = Signal(str)
    waypoint_altitude_changed = Signal(int)
    add_mode_toggled = Signal(bool)
    waypoints_visibility_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MapFlightRouteEditorSection")
        self.setVisible(False)

        shell = QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.divider = QWidget()
        self.divider.setObjectName("MapFlightRouteEditorDivider")
        self.divider.setFixedHeight(1)
        shell.addWidget(self.divider)

        header = QWidget()
        header.setObjectName("MapFlightRouteEditorHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 8, 8)
        header_layout.setSpacing(6)
        self.title_label = QLabel("วางเส้นทางบิน")
        self.title_label.setObjectName("MapFlightRouteEditorTitle")
        header_layout.addWidget(self.title_label, stretch=1)
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("MapTargetDetailCloseButton")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setToolTip("ปิดการวางเส้นทาง")
        self.close_btn.clicked.connect(self.closed.emit)
        header_layout.addWidget(self.close_btn)
        shell.addWidget(header)

        body = QWidget()
        body.setObjectName("MapFlightRouteEditorBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 4, 12, 12)
        body_layout.setSpacing(8)

        self.status_label = QLabel("ยังไม่มีจุด")
        self.status_label.setObjectName("FormSectionSubtitle")
        self.status_label.setWordWrap(True)
        body_layout.addWidget(self.status_label)

        self.hint_label = QLabel(
            "1. กด「เพิ่มจุด」แล้วคลิกบนแผนที่\n"
            "2. ลากจุดเพื่อย้าย · คลิกจุดเพื่อเลือก\n"
            "3. กด「อนุมัติ」เพื่อบันทึกลงแผน"
        )
        self.hint_label.setObjectName("FormSectionSubtitle")
        self.hint_label.setWordWrap(True)
        body_layout.addWidget(self.hint_label)

        self.add_point_btn = QPushButton("เพิ่มจุด")
        self.add_point_btn.setObjectName("MapTargetIngressViewButton")
        self.add_point_btn.setCheckable(True)
        self.add_point_btn.setToolTip("เปิดโหมดคลิกบนแผนที่เพื่อเพิ่ม Waypoint")
        self.add_point_btn.toggled.connect(self.add_mode_toggled.emit)
        body_layout.addWidget(self.add_point_btn)

        self.show_waypoints_chk = QCheckBox("แสดง Waypoint")
        self.show_waypoints_chk.setObjectName("MapFlightRouteEditorCheckbox")
        self.show_waypoints_chk.setChecked(True)
        self.show_waypoints_chk.setToolTip("เปิด/ปิดการแสดงจุด Waypoint บนแผนที่")
        self.show_waypoints_chk.toggled.connect(self.waypoints_visibility_changed.emit)
        body_layout.addWidget(self.show_waypoints_chk)

        self.show_labels_chk = QCheckBox("แสดงชื่อจุด")
        self.show_labels_chk.setObjectName("MapFlightRouteEditorCheckbox")
        self.show_labels_chk.setChecked(False)
        self.show_labels_chk.setToolTip("เปิด/ปิดข้อความชื่อ Waypoint บนแผนที่")
        self.show_labels_chk.toggled.connect(self.waypoint_labels_visibility_changed.emit)
        body_layout.addWidget(self.show_labels_chk)

        label_row = QHBoxLayout()
        label_row.setSpacing(6)
        label_title = QLabel("ชื่อจุด")
        label_title.setObjectName("FormFieldLabel")
        label_row.addWidget(label_title)
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("WP1")
        self.label_edit.setEnabled(False)
        self.label_edit.editingFinished.connect(self._emit_label_change)
        label_row.addWidget(self.label_edit, stretch=1)
        body_layout.addLayout(label_row)

        alt_row = QHBoxLayout()
        alt_row.setSpacing(6)
        alt_title = QLabel("ความสูง (ft)")
        alt_title.setObjectName("FormFieldLabel")
        alt_row.addWidget(alt_title)
        self.altitude_spin = QSpinBox()
        self.altitude_spin.setObjectName("MapToolbarSpin")
        self.altitude_spin.setRange(0, MAX_FLIGHT_ALTITUDE_FT)
        self.altitude_spin.setSpecialValueText("—")
        self.altitude_spin.setEnabled(False)
        self.altitude_spin.valueChanged.connect(self._emit_altitude_change)
        alt_row.addWidget(self.altitude_spin, stretch=1)
        body_layout.addLayout(alt_row)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.delete_btn = QPushButton("ลบจุด")
        self.delete_btn.setObjectName("MapTargetFooterButton")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_waypoint_requested.emit)
        actions.addWidget(self.delete_btn)
        self.approve_btn = QPushButton("อนุมัติ")
        self.approve_btn.setObjectName("MapTargetIngressViewButton")
        self.approve_btn.setEnabled(False)
        self.approve_btn.setToolTip("บันทึกจุดเส้นทางลงแผน Weaponeering")
        self.approve_btn.clicked.connect(self.approve_requested.emit)
        actions.addWidget(self.approve_btn)
        body_layout.addLayout(actions)

        shell.addWidget(body)

    def _emit_label_change(self) -> None:
        label = self.label_edit.text().strip()
        if label:
            self.waypoint_label_changed.emit(label)

    def _emit_altitude_change(self, value: int) -> None:
        if self.altitude_spin.isEnabled() and value > 0:
            self.waypoint_altitude_changed.emit(value)

    def show_editor(self, *, target_label: str, wing_name: str) -> None:
        self.title_label.setText(f"วางเส้นทาง · {target_label}")
        self.status_label.setText(f"จุดเริ่ม: {wing_name}")
        self.setVisible(True)

    def hide_editor(self) -> None:
        self.setVisible(False)
        self.add_point_btn.blockSignals(True)
        self.add_point_btn.setChecked(False)
        self.add_point_btn.blockSignals(False)
        self.show_waypoints_chk.blockSignals(True)
        self.show_waypoints_chk.setChecked(True)
        self.show_waypoints_chk.blockSignals(False)
        self.show_labels_chk.blockSignals(True)
        self.show_labels_chk.setChecked(False)
        self.show_labels_chk.blockSignals(False)
        self.label_edit.clear()
        self.label_edit.setEnabled(False)
        self.altitude_spin.setValue(0)
        self.altitude_spin.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.approve_btn.setEnabled(False)

    def set_waypoints_visible(self, visible: bool) -> None:
        self.show_waypoints_chk.blockSignals(True)
        self.show_waypoints_chk.setChecked(visible)
        self.show_waypoints_chk.blockSignals(False)

    def set_waypoint_labels_visible(self, visible: bool) -> None:
        self.show_labels_chk.blockSignals(True)
        self.show_labels_chk.setChecked(visible)
        self.show_labels_chk.blockSignals(False)

    def update_state(
        self,
        *,
        waypoint_count: int,
        distance_label: str,
        dirty: bool,
        selected_label: str | None = None,
        selected_waypoint_id: str | None = None,
        selected_altitude_ft: int | None = None,
    ) -> None:
        self.status_label.setText(
            f"{waypoint_count} จุด · {distance_label}"
            + (" · แก้ไขแล้ว" if dirty else "")
        )
        self.approve_btn.setEnabled(dirty and waypoint_count > 0)
        has_selection = bool(selected_waypoint_id)
        self.delete_btn.setEnabled(has_selection)
        self.label_edit.setEnabled(has_selection)
        self.altitude_spin.setEnabled(has_selection)
        if has_selection:
            self.label_edit.blockSignals(True)
            self.label_edit.setText(selected_label or "")
            self.label_edit.blockSignals(False)
            self.altitude_spin.blockSignals(True)
            self.altitude_spin.setValue(int(selected_altitude_ft or 0))
            self.altitude_spin.blockSignals(False)
        else:
            self.label_edit.clear()
            self.altitude_spin.setValue(0)

    def preferred_height(self) -> int:
        self.adjustSize()
        return self.sizeHint().height()
