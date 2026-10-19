from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


_RISK_OPTIONS = (
    ("สูง", "high"),
    ("กลาง", "medium"),
    ("ต่ำ", "low"),
)

_RISK_DISPLAY = {
    "high": "สูง",
    "medium": "กลาง",
    "low": "ต่ำ",
}


class _DetectionObjectRow(QWidget):
    delete_clicked = Signal(str)

    def __init__(
        self,
        *,
        object_id: str,
        label: str,
        risk: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._object_id = object_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(6)

        title = QLabel(label)
        title.setObjectName("MapDetectionObjectLabel")
        layout.addWidget(title, stretch=1)

        risk_text = _RISK_DISPLAY.get(risk, risk or "—")
        risk_label = QLabel(risk_text)
        risk_label.setObjectName("MapDetectionObjectRisk")
        risk_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(risk_label)

        delete_btn = QPushButton("×")
        delete_btn.setObjectName("MapDetectionObjectDeleteButton")
        delete_btn.setFixedSize(22, 22)
        delete_btn.setToolTip("ลบอาคารนี้")
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._object_id))
        layout.addWidget(delete_btn)


class MapBuildingDetectionEditorCard(QWidget):
    """Building detection editor embedded in the map target detail overlay."""

    closed = Signal()
    add_mode_toggled = Signal(bool)
    delete_requested = Signal()
    risk_level_changed = Signal(str)
    object_selected = Signal(str)
    delete_object_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MapBuildingDetectionEditorSection")
        self.setVisible(False)
        self._updating_list = False

        shell = QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        divider = QWidget()
        divider.setObjectName("MapFlightRouteEditorDivider")
        divider.setFixedHeight(1)
        shell.addWidget(divider)

        header = QWidget()
        header.setObjectName("MapFlightRouteEditorHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 8, 8)
        header_layout.setSpacing(6)
        self.title_label = QLabel("จัดการอาคาน Detection")
        self.title_label.setObjectName("MapFlightRouteEditorTitle")
        header_layout.addWidget(self.title_label, stretch=1)
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("MapTargetDetailCloseButton")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setToolTip("ปิดเครื่องมือจัดการอาคาน")
        self.close_btn.clicked.connect(self.closed.emit)
        header_layout.addWidget(self.close_btn)
        shell.addWidget(header)

        body = QWidget()
        body.setObjectName("MapFlightRouteEditorBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 4, 12, 12)
        body_layout.setSpacing(8)

        self.status_label = QLabel("ยังไม่มีอาคาร")
        self.status_label.setObjectName("FormSectionSubtitle")
        self.status_label.setWordWrap(True)
        body_layout.addWidget(self.status_label)

        self.hint_label = QLabel(
            "1. กด「เพิ่มอาคาร」แล้วคลิกบนแผนที่\n"
            "2. คลิกรายการด้านล่างหรือบนแผนที่เพื่อเลือก\n"
            "3. กด × ที่รายการหรือ「ลบอาคาร」· ระบบคำนวณทิศทางเข้า-ออกใหม่ทันที"
        )
        self.hint_label.setObjectName("FormSectionSubtitle")
        self.hint_label.setWordWrap(True)
        body_layout.addWidget(self.hint_label)

        list_title = QLabel("รายการอาคาร")
        list_title.setObjectName("FormFieldLabel")
        body_layout.addWidget(list_title)

        self.object_list = QListWidget()
        self.object_list.setObjectName("MapDetectionObjectList")
        self.object_list.setMaximumHeight(140)
        self.object_list.setSpacing(2)
        self.object_list.currentItemChanged.connect(self._on_list_item_changed)
        body_layout.addWidget(self.object_list)

        self.add_btn = QPushButton("เพิ่มอาคาร")
        self.add_btn.setObjectName("MapTargetIngressViewButton")
        self.add_btn.setCheckable(True)
        self.add_btn.setToolTip("เปิดโหมดคลิกบนแผนที่เพื่อเพิ่มอาคาร")
        self.add_btn.toggled.connect(self.add_mode_toggled.emit)
        body_layout.addWidget(self.add_btn)

        risk_row = QHBoxLayout()
        risk_row.setSpacing(6)
        risk_label = QLabel("ความเสี่ยง")
        risk_label.setObjectName("FormFieldLabel")
        risk_row.addWidget(risk_label)
        self.risk_combo = QComboBox()
        self.risk_combo.setObjectName("MapToolbarCombo")
        for label, value in _RISK_OPTIONS:
            self.risk_combo.addItem(label, value)
        self.risk_combo.setEnabled(False)
        self.risk_combo.currentIndexChanged.connect(self._emit_risk_change)
        risk_row.addWidget(self.risk_combo, stretch=1)
        body_layout.addLayout(risk_row)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.delete_btn = QPushButton("ลบอาคาร")
        self.delete_btn.setObjectName("MapTargetFooterButton")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_requested.emit)
        actions.addWidget(self.delete_btn)
        body_layout.addLayout(actions)

        shell.addWidget(body)

    def _on_list_item_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if self._updating_list or current is None:
            return
        object_id = str(current.data(Qt.ItemDataRole.UserRole) or "")
        if object_id:
            self.object_selected.emit(object_id)

    def _emit_risk_change(self, _index: int = 0) -> None:
        if not self.risk_combo.isEnabled():
            return
        value = str(self.risk_combo.currentData() or "medium")
        self.risk_level_changed.emit(value)

    def show_editor(self, *, target_label: str, coordinate_label: str) -> None:
        self.title_label.setText(f"อาคาร Detection · {target_label}")
        self.status_label.setText(f"พิกัด: {coordinate_label}")
        self.setVisible(True)

    def hide_editor(self) -> None:
        self.setVisible(False)
        self.add_btn.blockSignals(True)
        self.add_btn.setChecked(False)
        self.add_btn.blockSignals(False)
        self.delete_btn.setEnabled(False)
        self.risk_combo.setEnabled(False)
        self._updating_list = True
        self.object_list.clear()
        self._updating_list = False

    def update_state(
        self,
        *,
        object_count: int,
        objects: list[dict[str, Any]] | None = None,
        selected_label: str | None = None,
        selected_risk: str | None = None,
        selected_object_id: str | None = None,
    ) -> None:
        base = f"{object_count} อาคาร"
        if selected_object_id:
            base += f" · เลือก {selected_label or selected_object_id}"
        self.status_label.setText(base)
        self._populate_object_list(objects or [], selected_object_id)
        has_selection = bool(selected_object_id)
        self.delete_btn.setEnabled(has_selection)
        self.risk_combo.blockSignals(True)
        self.risk_combo.setEnabled(has_selection)
        if has_selection and selected_risk:
            index = self.risk_combo.findData(selected_risk)
            if index >= 0:
                self.risk_combo.setCurrentIndex(index)
        self.risk_combo.blockSignals(False)

    def _populate_object_list(
        self,
        objects: list[dict[str, Any]],
        selected_object_id: str | None,
    ) -> None:
        self._updating_list = True
        self.object_list.clear()
        selected_row = -1
        row_index = 0
        for item in objects:
            object_id = str(item.get("id") or "")
            if not object_id:
                continue
            label = str(item.get("label") or "Building")
            risk = str(item.get("risk") or "medium")
            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, object_id)
            row = _DetectionObjectRow(
                object_id=object_id,
                label=label,
                risk=risk,
            )
            row.delete_clicked.connect(self.delete_object_requested.emit)
            list_item.setSizeHint(row.sizeHint())
            self.object_list.addItem(list_item)
            self.object_list.setItemWidget(list_item, row)
            if object_id == selected_object_id:
                selected_row = row_index
            row_index += 1
        if selected_row >= 0:
            self.object_list.setCurrentRow(selected_row)
        elif not objects:
            self.object_list.setCurrentRow(-1)
        self._updating_list = False

    def preferred_height(self) -> int:
        self.adjustSize()
        return self.sizeHint().height()
