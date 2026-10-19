from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.wing_data.models import WingMapDetail
from maap_app.ui.panels.wing_form_widgets import _form_card


def _detail_row(label: str, value: str) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    name = QLabel(label)
    name.setStyleSheet("color: #6b7f96; font-size: 10px; min-width: 52px;")
    text = QLabel(value)
    text.setWordWrap(True)
    text.setStyleSheet("color: #d7dee8; font-size: 10px;")
    text.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(name)
    layout.addWidget(text, stretch=1)
    return row


def _list_line(text: str, *, muted: bool = False) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    color = "#9fb0c2" if muted else "#d7dee8"
    label.setStyleSheet(f"color: {color}; font-size: 10px; padding: 1px 0;")
    return label


def _fmt_ready(status: str) -> str:
    return "พร้อม" if status == "ready" else "ไม่พร้อม"


class MapWingDetailPanel(QWidget):
    open_in_database = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("DetailPanel")
        self._wing_id: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body_host = QWidget()
        body_layout = QVBoxLayout(body_host)
        body_layout.setContentsMargins(8, 8, 8, 8)
        body_layout.setSpacing(8)

        self.empty_label = QLabel("คลิกกองบินบนแผนที่")
        self.empty_label.setWordWrap(True)
        self.empty_label.setStyleSheet("color: #6b7f96; font-size: 11px; padding: 4px 2px;")
        body_layout.addWidget(self.empty_label)

        self.content_host = QWidget()
        content_layout = QVBoxLayout(self.content_host)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        self.content_host.setVisible(False)
        body_layout.addWidget(self.content_host)

        self.summary_card, self.summary_layout = _form_card("กองบิน", "")
        self.aircraft_card, self.aircraft_layout = _form_card(
            "เครื่องบิน",
            "ประเภท · ฝูง · สถานะ",
        )
        self.inventory_card, self.inventory_layout = _form_card(
            "คลังสินค้า",
            "รายการและจำนวนในคลังของกองบิน",
        )
        self.pilot_card, self.pilot_layout = _form_card(
            "นักบิน",
            "ชื่อ · Callsign · ฝูง · CEP",
        )

        self.open_btn = QPushButton("เปิดใน Database")
        self.open_btn.setObjectName("SecondaryButton")
        self.open_btn.clicked.connect(self._emit_open)

        content_layout.addWidget(self.summary_card)
        content_layout.addWidget(self.aircraft_card)
        content_layout.addWidget(self.inventory_card)
        content_layout.addWidget(self.pilot_card)
        content_layout.addWidget(self.open_btn)
        content_layout.addStretch(1)

        body_layout.addStretch(1)
        scroll.setWidget(body_host)
        root.addWidget(scroll, stretch=1)

    def _emit_open(self) -> None:
        if self._wing_id:
            self.open_in_database.emit(self._wing_id)

    def clear(self) -> None:
        self._wing_id = None
        self.empty_label.setVisible(True)
        self.content_host.setVisible(False)

    def show_wing(self, detail: WingMapDetail) -> None:
        self._wing_id = detail.wing.id
        self.empty_label.setVisible(False)
        self.content_host.setVisible(True)

        unit_names = {unit.id: unit.unit_name for unit in detail.flying_units}
        wing = detail.wing
        lat_text = f"{wing.map_lat:.5f}" if wing.map_lat is not None else "—"
        lng_text = f"{wing.map_lng:.5f}" if wing.map_lng is not None else "—"

        self._rebuild_card(self.summary_layout)
        for row in (
            _detail_row("ชื่อ", wing.wing_name),
            _detail_row("พิกัด", f"{lat_text}\n{lng_text}"),
            _detail_row(
                "เครื่องบิน",
                f"{len(detail.aircraft)} ลำ "
                f"(พร้อม {detail.aircraft_ready_count} / "
                f"ไม่พร้อม {detail.aircraft_not_ready_count})",
            ),
            _detail_row("หน่วยบิน", str(len(detail.flying_units))),
            _detail_row("นักบิน", str(len(detail.pilots))),
            _detail_row("รายการคลัง", str(len(detail.inventory))),
        ):
            self.summary_layout.addWidget(row)

        self._rebuild_card(self.aircraft_layout)
        if detail.aircraft:
            for aircraft in detail.aircraft:
                self.aircraft_layout.addWidget(
                    _list_line(
                        f"{aircraft.aircraft_type} · "
                        f"{unit_names.get(aircraft.flying_unit_id or '', '—')} · "
                        f"{_fmt_ready(aircraft.mission_ready)}"
                    )
                )
        else:
            self.aircraft_layout.addWidget(_list_line("ไม่มีข้อมูลเครื่องบิน", muted=True))

        self._rebuild_card(self.inventory_layout)
        if detail.inventory:
            for item in detail.inventory:
                self.inventory_layout.addWidget(
                    _list_line(
                        f"{item.product_name} × {item.quantity} "
                        f"({item.depot_name})"
                    )
                )
        else:
            self.inventory_layout.addWidget(
                _list_line("ไม่มีสินค้าในคลัง", muted=True)
            )

        self._rebuild_card(self.pilot_layout)
        if detail.pilots:
            for pilot in detail.pilots:
                self.pilot_layout.addWidget(
                    _list_line(
                        f"{pilot.pilot_name} · {pilot.callsign} · "
                        f"{unit_names.get(pilot.flying_unit_id or '', '—')} · "
                        f"CEP {pilot.cep_value:.0f} ft"
                    )
                )
        else:
            self.pilot_layout.addWidget(_list_line("ไม่มีข้อมูลนักบิน", muted=True))

    @staticmethod
    def _rebuild_card(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
