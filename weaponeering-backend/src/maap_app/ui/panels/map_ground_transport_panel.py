from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.ground_transport.routing import (
    format_distance_m,
    format_duration_min,
)
from maap_app.modules.ground_transport.service import (
    GroundTransportService,
    route_mode_label,
)
from maap_app.modules.wing_data.service import WingDataService


class _TransportListCard(QFrame):
    clicked = Signal()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MapGroundTransportPanel(QWidget):
    transport_selected = Signal(str)

    def __init__(
        self,
        transport_service: GroundTransportService,
        wing_data_service: WingDataService,
    ) -> None:
        super().__init__()
        self._transport_service = transport_service
        self._wing_data_service = wing_data_service
        self._scenario_id: str | None = None
        self._selected_id: str | None = None
        self._card_widgets: dict[str, QWidget] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        title = QLabel("รายการขนส่งทางบก")
        title.setObjectName("MapTargetCardTitle")
        root.addWidget(title)

        hint = QLabel(
            "กดรายการเพื่อดูเส้นทางบนแผนที่\n"
            "เพิ่ม/แก้ไขข้อมูลได้ที่หน้า ฐานข้อมูล → ข้อมูลขนส่งทางบก"
        )
        hint.setObjectName("MapTargetMutedLabel")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setObjectName("MapTargetScroll")
        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.empty_label = QLabel("ยังไม่มีรายการขนส่ง")
        self.empty_label.setObjectName("MapTargetMutedLabel")
        self.empty_label.setWordWrap(True)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_layout.addWidget(self.empty_label)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.list_host)
        root.addWidget(self.scroll, stretch=1)

    def set_scenario(self, scenario_id: str | None) -> None:
        self._scenario_id = scenario_id
        self._selected_id = None
        self.refresh()

    def refresh(self) -> None:
        self._render_transports()

    def select_transport(self, transport_id: str | None) -> None:
        self._selected_id = transport_id
        self._update_card_selection()

    def clear_selection(self) -> None:
        self._selected_id = None
        self._update_card_selection()

    def _render_transports(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._card_widgets.clear()

        if not self._scenario_id:
            self.empty_label = QLabel("ยังไม่มี scenario ที่ใช้งาน")
            self.empty_label.setObjectName("MapTargetMutedLabel")
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(self.empty_label)
            self.list_layout.addStretch(1)
            return

        transports = self._transport_service.list_transports(self._scenario_id)
        wings = {
            wing.id: wing.wing_name
            for wing in self._wing_data_service.list_wings(self._scenario_id)
        }
        products = {
            product.id: product.product_name
            for product in self._wing_data_service.list_products(self._scenario_id)
        }

        if not transports:
            self.empty_label = QLabel(
                "ยังไม่มีรายการขนส่ง\n"
                "เพิ่มได้ที่หน้า ฐานข้อมูล → ข้อมูลขนส่งทางบก"
            )
            self.empty_label.setObjectName("MapTargetMutedLabel")
            self.empty_label.setWordWrap(True)
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(self.empty_label)
            self.list_layout.addStretch(1)
            return

        for transport in transports:
            origin_name = wings.get(transport.origin_wing_id, "—")
            dest_name = wings.get(transport.destination_wing_id, "—")
            product_name = products.get(transport.product_id or "", "")
            card = self._build_transport_card(
                transport_id=transport.id,
                title=transport.label or f"{origin_name} → {dest_name}",
                origin_name=origin_name,
                dest_name=dest_name,
                product_name=product_name,
                quantity=transport.quantity,
                distance_m=transport.distance_m,
                duration_min=transport.duration_min,
                route_mode=transport.route_mode,
            )
            self.list_layout.addWidget(card)
            self._card_widgets[transport.id] = card
        self.list_layout.addStretch(1)
        self._update_card_selection()

    def _build_transport_card(
        self,
        *,
        transport_id: str,
        title: str,
        origin_name: str,
        dest_name: str,
        product_name: str,
        quantity: int,
        distance_m: float,
        duration_min: float,
        route_mode: str,
    ) -> QWidget:
        card = _TransportListCard()
        card.setObjectName("MapGroundTransportCard")
        card.setProperty("selected", "false")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.clicked.connect(lambda tid=transport_id: self._select_transport(tid))

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("MapTargetCardTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        layout.addWidget(self._static_meta_row("จาก", origin_name))
        layout.addWidget(self._static_meta_row("ถึง", dest_name))
        if product_name:
            layout.addWidget(
                self._static_meta_row("สินค้า", f"{product_name} × {quantity}")
            )
        layout.addWidget(self._static_meta_row("ระยะทาง", format_distance_m(distance_m)))
        layout.addWidget(
            self._static_meta_row("เวลา", format_duration_min(duration_min))
        )
        layout.addWidget(
            self._static_meta_row("เส้นทาง", route_mode_label(route_mode))
        )
        return card

    @staticmethod
    def _static_meta_row(label: str, value: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        name = QLabel(label)
        name.setObjectName("MapTargetMetaLabel")
        text = QLabel(value)
        text.setObjectName("MapTargetMetaValue")
        text.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(name)
        layout.addWidget(text, stretch=1)
        return row

    def _select_transport(self, transport_id: str) -> None:
        if self._selected_id == transport_id:
            self._selected_id = None
            self._update_card_selection()
            self.transport_selected.emit("")
            return
        self._selected_id = transport_id
        self._update_card_selection()
        self.transport_selected.emit(transport_id)

    def _update_card_selection(self) -> None:
        for transport_id, widget in self._card_widgets.items():
            widget.setProperty(
                "selected",
                "true" if transport_id == self._selected_id else "false",
            )
            widget.style().unpolish(widget)
            widget.style().polish(widget)
