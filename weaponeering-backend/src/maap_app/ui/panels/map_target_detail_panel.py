from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from maap_app.modules.target.models import TargetCardDetail
from maap_app.modules.weaponeering.jmem_calculator import (
    EFFECT_ZONE_COLORS,
    EFFECT_ZONE_LABELS_TH,
    FEET_TO_METERS,
    format_range_m_ft,
)
from maap_app.ui.panels.wing_form_widgets import _form_card
from maap_app.ui.product_images import ProductImageLabel, product_image_path

_STYLE_VALUE = "color: #d7dee8; font-size: 10px;"
_STYLE_ACCENT = "color: #67e8f9; font-size: 10px; font-weight: 700;"
_STYLE_MUTED = "color: #9fb0c2; font-size: 10px;"
_STYLE_HERO = "color: #e8f0f8; font-size: 11px; font-weight: 700;"


def _compact_line(text: str, *, muted: bool = False, accent: bool = False) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    if accent:
        label.setStyleSheet(_STYLE_HERO)
    elif muted:
        label.setStyleSheet(_STYLE_MUTED)
    else:
        label.setStyleSheet(_STYLE_VALUE)
    return label


def _chip(text: str, *, accent: bool = False) -> QLabel:
    label = QLabel(text)
    if accent:
        label.setStyleSheet(
            "color: #67e8f9; font-size: 9px; font-weight: 600; "
            "background: rgba(103,232,249,0.1); border-radius: 4px; padding: 2px 6px;"
        )
    else:
        label.setStyleSheet(
            "color: #9fb0c2; font-size: 9px; font-weight: 600; "
            "background: rgba(159,176,194,0.12); border-radius: 4px; padding: 2px 6px;"
        )
    return label


def _chip_row(*chips: QLabel) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for chip in chips:
        layout.addWidget(chip)
    layout.addStretch(1)
    return row


def _section_divider() -> QWidget:
    line = QWidget()
    line.setFixedHeight(1)
    line.setStyleSheet("background: #1e2d42; margin: 2px 0;")
    return line


def _format_coords(detail: TargetCardDetail) -> str:
    if detail.coordinates and len(detail.coordinates) > 1:
        parts = [
            f"{(coord.label or f'P{index + 1}')} {coord.map_lat:.4f},{coord.map_lng:.4f}"
            + (" ★" if coord.is_primary else "")
            for index, coord in enumerate(detail.coordinates)
        ]
        return " · ".join(parts)
    if detail.map_lat is not None and detail.map_lng is not None:
        return f"{detail.map_lat:.5f}, {detail.map_lng:.5f}"
    return "—"


def _short_readiness(text: str) -> str:
    cleaned = text.replace("Aircraft: ", "").strip()
    if not cleaned:
        return "—"
    return cleaned.replace(" ready", " พร้อม")


def _plan_status_label(status: str) -> str:
    if status == "Plan saved":
        return "มีแผน"
    if status == "No plan":
        return "ยังไม่มีแผน"
    return status


def _populate_summary_block(
    layout: QVBoxLayout,
    *,
    card,
    detail: TargetCardDetail,
    pk_text: str,
) -> None:
    err_m = card.coordinate_error_m
    err_text = f"{err_m:.0f}m" if err_m is not None else "—"
    size_parts: list[str] = []
    if card.width_m is not None:
        size_parts.append(f"W{card.width_m:.0f}m")
    if card.length_m is not None:
        size_parts.append(f"L{card.length_m:.1f}m")
    size_text = " ".join(size_parts)

    chips = [
        _chip(f"{card.target_type}/{card.target_subtype}", accent=True),
        _chip(f"Pk {pk_text}"),
        _chip(f"ERR {err_text}"),
    ]
    if card.material_class and card.material_class != "UNKNOWN":
        chips.insert(1, _chip(card.material_class))
    layout.addWidget(_chip_row(*chips))
    layout.addWidget(_compact_line(_format_coords(detail)))
    if card.target_description:
        layout.addWidget(_compact_line(card.target_description.strip(), muted=True))
    if size_text:
        layout.addWidget(_compact_line(f"ขนาด {size_text}", muted=True))


def _zone_row(zone: str, color: str, radius_ft: float) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 2, 0, 2)
    layout.setSpacing(6)
    swatch = QLabel()
    swatch.setFixedSize(12, 12)
    swatch.setStyleSheet(
        f"background:{color}; border:1px solid rgba(255,255,255,0.35); border-radius:2px;"
    )
    label = QLabel(EFFECT_ZONE_LABELS_TH.get(zone, zone))
    label.setStyleSheet(_STYLE_VALUE)
    radius = QLabel(format_range_m_ft(radius_ft))
    radius.setStyleSheet(_STYLE_MUTED)
    radius.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(swatch)
    layout.addWidget(label)
    layout.addStretch(1)
    layout.addWidget(radius)
    return row


def _border_crossing_text(prefix: str, crossing: dict[str, object] | None) -> str | None:
    if not crossing:
        return None
    distance_nm = crossing.get("distanceNm")
    bearing = crossing.get("bearingDeg")
    dist = f"{float(distance_nm):.1f}NM" if distance_nm is not None else "—"
    bear = f"{float(bearing):.0f}°" if bearing is not None else ""
    return f"{prefix} {dist} {bear}".strip()


def _border_option_block(
    option: dict[str, object],
    *,
    coordinate_id: str | None,
    is_active: bool,
    on_view: Callable[[str | None, int], None],
) -> QWidget:
    block = QWidget()
    layout = QVBoxLayout(block)
    layout.setContentsMargins(0, 4, 0, 6)
    layout.setSpacing(2)

    rank = int(option.get("rank") or 0)
    bearing = float(option.get("bearingDeg") or 0)
    compass = str(option.get("compassLabel") or "")
    ingress = option.get("ingressBearingDeg")
    risk_score = float(option.get("riskScore") or 0)
    header_row = QWidget()
    header_layout = QHBoxLayout(header_row)
    header_layout.setContentsMargins(0, 0, 0, 0)
    header_layout.setSpacing(6)
    if ingress is not None:
        header_text = f"#{rank} {bearing:.0f}°{compass} → เข้า {float(ingress):.0f}° · {risk_score:.1f}"
    else:
        header_text = f"#{rank} {bearing:.0f}°{compass} · {risk_score:.1f}"
    header = QLabel(header_text)
    header.setStyleSheet(_STYLE_ACCENT)
    view_btn = QPushButton("กำลังดู" if is_active else "ดู")
    view_btn.setObjectName("MapTargetIngressViewButton")
    view_btn.setProperty("active", is_active)
    view_btn.setToolTip("แสดงเส้นเข้า-ออกประเทศของตัวเลือกนี้บนแผนที่")
    view_btn.clicked.connect(
        lambda _checked=False, coord_id=coordinate_id, option_rank=rank: on_view(
            coord_id,
            option_rank,
        )
    )
    header_layout.addWidget(header, stretch=1)
    header_layout.addWidget(view_btn)
    layout.addWidget(header_row)

    border_route = option.get("borderRoute") or {}
    if border_route.get("available"):
        route_parts: list[str] = []
        nearest = border_route.get("nearestBorder")
        if isinstance(nearest, dict):
            route_parts.append(
                f"ขอบ {float(nearest.get('distanceNm', 0)):.1f}NM "
                f"{float(nearest.get('bearingDeg', 0)):.0f}°"
            )
        entry = border_route.get("entry")
        exit_point = border_route.get("exit")
        entry_text = _border_crossing_text("เข้า", entry if isinstance(entry, dict) else None)
        exit_text = _border_crossing_text("ออก", exit_point if isinstance(exit_point, dict) else None)
        if entry_text:
            route_parts.append(entry_text)
        if exit_text:
            route_parts.append(exit_text)
        total_nm = border_route.get("totalCorridorNm")
        if total_nm is not None:
            route_parts.append(f"รวม {float(total_nm):.1f}NM")
        if route_parts:
            layout.addWidget(_compact_line(" · ".join(route_parts), muted=True))
        message = border_route.get("message")
        if message and not route_parts:
            layout.addWidget(_recommendation_label(str(message)))
    elif border_route.get("message"):
        layout.addWidget(_recommendation_label(str(border_route.get("message"))))
    return block


def _point_header(label: str, *, is_primary: bool) -> QLabel:
    primary_text = " ★" if is_primary else ""
    header = QLabel(f"{label}{primary_text}")
    header.setStyleSheet(_STYLE_ACCENT)
    return header


def _marker_for_coordinate(
    markers: list[dict[str, Any]],
    *,
    coordinate_id: str | None,
    lat: float,
    lng: float,
) -> dict[str, Any] | None:
    if coordinate_id:
        for marker in markers:
            if marker.get("coordinateId") == coordinate_id:
                return marker
    for marker in markers:
        if (
            abs(float(marker.get("lat", 0)) - lat) < 1e-5
            and abs(float(marker.get("lng", 0)) - lng) < 1e-5
        ):
            return marker
    return markers[0] if len(markers) == 1 else None


def _populate_risk_direction_block(
    layout: QVBoxLayout,
    risk_direction: dict[str, Any],
    *,
    coordinate_id: str | None,
    ingress_focus: tuple[str | None, int | None],
    on_ingress_view: Callable[[str | None, int], None],
) -> None:
    if risk_direction.get("available"):
        recommended = risk_direction.get("recommendedOptions") or []
        if recommended:
            for item in recommended[:3]:
                rank = int(item.get("rank") or 0)
                layout.addWidget(
                    _border_option_block(
                        item,
                        coordinate_id=coordinate_id,
                        is_active=ingress_focus == (coordinate_id, rank),
                        on_view=on_ingress_view,
                    )
                )
        else:
            bearing = risk_direction.get("bearingDeg")
            compass = str(risk_direction.get("compassLabel") or "")
            risk_score = risk_direction.get("riskScore")
            if bearing is not None:
                score_text = f" · {float(risk_score):.1f}" if risk_score is not None else ""
                layout.addWidget(
                    _compact_line(f"แนะนำ {float(bearing):.0f}°{compass}{score_text}")
                )

        avoid_bearing = risk_direction.get("avoidBearingDeg")
        avoid_compass = str(risk_direction.get("avoidCompassLabel") or "")
        if avoid_bearing is not None:
            avoid_score = risk_direction.get("avoidRiskScore")
            avoid_text = f"หลีกเลี่ยง {float(avoid_bearing):.0f}°{avoid_compass}"
            if avoid_score is not None:
                avoid_text += f" · {float(avoid_score):.1f}"
            layout.addWidget(_compact_line(avoid_text, muted=True))
        for line in risk_direction.get("recommendations") or []:
            text = str(line)
            if text.startswith(("ตัวเลือกที่แนะนำ", "#")):
                continue
            if any(keyword in text for keyword in ("เข้า", "ออก", "ขอบ", "NM", "°")):
                continue
            layout.addWidget(_recommendation_label(text))
    else:
        for line in risk_direction.get("recommendations") or (
            "รัน Detection เพื่อประเมินทิศทาง",
        ):
            layout.addWidget(_recommendation_label(str(line)))


def _product_rank_row(rank: int, product_name: str, pd_base: float, n_required: object) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 1, 0, 1)
    layout.setSpacing(6)
    rank_label = QLabel(f"#{rank}")
    rank_label.setFixedWidth(18)
    rank_label.setStyleSheet(_STYLE_ACCENT)
    name = QLabel(product_name)
    name.setStyleSheet(_STYLE_VALUE)
    stats = QLabel(f"Pd{pd_base:.2f} · N{n_required}")
    stats.setStyleSheet(_STYLE_MUTED)
    stats.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(rank_label)
    layout.addWidget(name, stretch=1)
    layout.addWidget(stats)
    return row


def _product_image_row(product_name: str | None, *, max_size: int = 80) -> QWidget | None:
    if not product_name or product_image_path(product_name) is None:
        return None
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    image = ProductImageLabel(max_size=max_size)
    image.set_product(product_name)
    layout.addWidget(image)
    layout.addStretch(1)
    return row


def _product_selector_row(
    product_catalog: list[dict[str, str]],
    selected_product_id: str | None,
    on_change: Callable[[str | None], None],
) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    label = QLabel("เลือกสินค้า")
    label.setStyleSheet("color: #9fb0c2; font-size: 10px;")
    combo = QComboBox()
    combo.blockSignals(True)
    combo.addItem("อัตโนมัติ (JMEM)", None)
    for item in product_catalog:
        combo.addItem(str(item.get("name") or "—"), item.get("id"))
    if selected_product_id:
        index = combo.findData(selected_product_id)
        combo.setCurrentIndex(index if index >= 0 else 0)
    combo.blockSignals(False)

    def _emit() -> None:
        if combo.signalsBlocked():
            return
        value = combo.currentData()
        on_change(str(value) if value else None)

    combo.currentIndexChanged.connect(_emit)
    layout.addWidget(label)
    layout.addWidget(combo, stretch=1)
    row._product_combo = combo  # type: ignore[attr-defined]
    return row


def _populate_weaponeering_block(
    layout: QVBoxLayout,
    *,
    marker_product: str | None,
    weaponeering: dict[str, object] | None,
    include_products: bool = True,
) -> None:
    payload = weaponeering or {}
    products = payload.get("products") or []
    plan = payload.get("plan") or {}
    plan_fields = payload.get("planFields") or {}
    nearest_wing = payload.get("nearestWing") or {}
    has_saved_plan = bool(payload.get("hasSavedPlan"))

    if include_products:
        primary_product = marker_product or (
            str(products[0].get("productName")) if products else "อ้างอิง 500 lb"
        )
        layout.addWidget(_compact_line(primary_product, accent=True))

        image_product = marker_product or (
            str(products[0].get("productName")) if products else None
        )
        image_row = _product_image_row(image_product)
        if image_row is not None:
            layout.addWidget(image_row)

        if products:
            for item in products[:5]:
                layout.addWidget(
                    _product_rank_row(
                        int(item.get("rank") or 0),
                        str(item.get("productName") or "—"),
                        float(item.get("pdBase") or 0.0),
                        item.get("nRequired", "—"),
                    )
                )
        else:
            layout.addWidget(_compact_line("ไม่มี Product Ranking", muted=True))

        layout.addWidget(_section_divider())

    plan_status = _plan_status_label(str(plan.get("status") or "No plan"))
    plan_detail = str(plan.get("detail") or "ยังไม่ได้บันทึกแผน")
    layout.addWidget(_chip_row(_chip(plan_status, accent=has_saved_plan)))
    layout.addWidget(_compact_line(plan_detail, muted=True))

    aircraft = str(plan.get("aircraft") or "").replace("Aircraft: ", "")
    if aircraft:
        layout.addWidget(_compact_line(aircraft, muted=True))

    if has_saved_plan and plan_fields:
        route_bits: list[str] = []
        takeoff = plan_fields.get("takeoff")
        if takeoff and takeoff != "—":
            route_bits.append(f"↑ {takeoff}")
        ingress = plan_fields.get("ingress")
        if ingress and ingress != "—":
            route_bits.append(f"↗ {ingress}")
        if route_bits:
            layout.addWidget(_compact_line(" · ".join(route_bits), muted=True))

        alt_bits: list[str] = []
        cruise_alt = plan_fields.get("cruiseAltFt")
        ingress_alt = plan_fields.get("ingressAltFt")
        target_alt = plan_fields.get("targetAltFt")
        if cruise_alt is not None:
            alt_bits.append(f"C{int(cruise_alt) // 1000}k")
        if ingress_alt is not None:
            alt_bits.append(f"I{int(ingress_alt) // 1000}k")
        if target_alt is not None:
            alt_bits.append(f"T{int(target_alt) // 1000}k")
        meta_bits = list(alt_bits)
        waypoint_count = plan_fields.get("waypointCount")
        if waypoint_count is not None:
            meta_bits.append(f"WP{waypoint_count}")
        if plan_fields.get("returnEnabled"):
            meta_bits.append("RTB")
        if meta_bits:
            layout.addWidget(_compact_line(" · ".join(meta_bits), muted=True))
    else:
        route = str(plan.get("route") or "")
        if route:
            layout.addWidget(_compact_line(route, muted=True))

    wing_name = str(nearest_wing.get("name") or "—")
    wing_distance = str(nearest_wing.get("distance") or "—")
    wing_ready = _short_readiness(str(nearest_wing.get("readiness") or ""))
    layout.addWidget(
        _compact_line(f"กองบิน {wing_name} · {wing_distance} · {wing_ready}", muted=True)
    )


def _recommendation_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("color: #9fb0c2; font-size: 10px; padding: 1px 0;")
    return label


class MapTargetDetailPanel(QWidget):
    open_in_target_stack = Signal(str)
    ingress_corridor_view_requested = Signal(str, object, int)
    detection_editor_requested = Signal()
    coordinate_product_changed = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("DetailPanel")
        self._target_id: str | None = None
        self._ingress_focus: tuple[str | None, int | None] = (None, None)
        self._last_marker_list: list[dict[str, Any]] = []
        self._last_coordinate_points: list[Any] = []

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
        body_layout.setSpacing(6)

        self.empty_label = QLabel("คลิก Target บนแผนที่")
        self.empty_label.setWordWrap(True)
        self.empty_label.setStyleSheet("color: #6b7f96; font-size: 11px; padding: 4px 2px;")
        body_layout.addWidget(self.empty_label)

        self.content_host = QWidget()
        content_layout = QVBoxLayout(self.content_host)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)
        self.content_host.setVisible(False)
        body_layout.addWidget(self.content_host)

        self.summary_card, self.summary_layout = _form_card("เป้าหมาย")
        self.weapon_card, self.weapon_layout = _form_card("Weaponeering")
        self.zones_card, self.zones_layout = _form_card(
            "วงผลกระทบ",
            "แดง·ส้ม·เหลืองเข้ม·เหลือง",
        )
        self.risk_direction_card, self.risk_direction_layout = _form_card(
            "ทิศทางความเสี่ยงต่ำ",
            "กด ดู แสดงเส้นทางบนแผนที่",
        )
        self.detection_manage_btn = QPushButton("จัดการอาคาน Detection")
        self.detection_manage_btn.setObjectName("MapTargetIngressViewButton")
        self.detection_manage_btn.setToolTip(
            "เปิดเครื่องมือเพิ่ม/ลบอาคาน · คำนวณทิศทางเข้า-ออกใหม่อัตโนมัติ"
        )
        self.detection_manage_btn.clicked.connect(self.detection_editor_requested.emit)
        self.flight_route_card, self.flight_route_layout = _form_card("Flight Route")
        self.flight_route_card.setVisible(False)

        self.open_btn = QPushButton("Target Stack")
        self.open_btn.setObjectName("SecondaryButton")
        self.open_btn.clicked.connect(self._emit_open)

        content_layout.addWidget(self.summary_card)
        content_layout.addWidget(self.weapon_card)
        content_layout.addWidget(self.zones_card)
        content_layout.addWidget(self.risk_direction_card)
        content_layout.addWidget(self.detection_manage_btn)
        content_layout.addWidget(self.flight_route_card)
        content_layout.addWidget(self.open_btn)
        content_layout.addStretch(1)

        body_layout.addStretch(1)
        scroll.setWidget(body_host)
        root.addWidget(scroll, stretch=1)

    def clear_ingress_focus(self) -> None:
        if self._ingress_focus == (None, None):
            return
        self._ingress_focus = (None, None)
        if self.content_host.isVisible():
            self._rebuild_ingress_section()

    def _emit_open(self) -> None:
        if self._target_id:
            self.open_in_target_stack.emit(self._target_id)

    def clear(self) -> None:
        self._target_id = None
        self._ingress_focus = (None, None)
        self.empty_label.setVisible(True)
        self.content_host.setVisible(False)
        self.flight_route_card.setVisible(False)

    def _on_ingress_view_clicked(
        self,
        coordinate_id: str | None,
        rank: int,
    ) -> None:
        if not self._target_id:
            return
        focus_key = (coordinate_id, rank)
        if self._ingress_focus == focus_key:
            self._ingress_focus = (None, None)
            self.ingress_corridor_view_requested.emit(self._target_id, coordinate_id, 0)
        else:
            self._ingress_focus = focus_key
            self.ingress_corridor_view_requested.emit(self._target_id, coordinate_id, rank)
        self._rebuild_ingress_section()

    def _rebuild_ingress_section(self) -> None:
        self._rebuild_card(self.risk_direction_layout)
        coordinate_points = self._last_coordinate_points
        marker_list = self._last_marker_list
        if coordinate_points and marker_list:
            for index, coord in enumerate(coordinate_points):
                point_marker = _marker_for_coordinate(
                    marker_list,
                    coordinate_id=coord.id,
                    lat=coord.map_lat,
                    lng=coord.map_lng,
                )
                self.risk_direction_layout.addWidget(
                    _point_header(
                        coord.label or f"P{index + 1}",
                        is_primary=coord.is_primary,
                    )
                )
                risk_direction = (point_marker or {}).get("lowestRiskDirection") or {}
                _populate_risk_direction_block(
                    self.risk_direction_layout,
                    risk_direction,
                    coordinate_id=coord.id,
                    ingress_focus=self._ingress_focus,
                    on_ingress_view=self._on_ingress_view_clicked,
                )
            return
        primary_marker = next(
            (item for item in marker_list if item.get("isPrimary")),
            marker_list[0] if marker_list else None,
        )
        risk_direction = (primary_marker or {}).get("lowestRiskDirection") or {}
        coordinate_id = str(
            (primary_marker or {}).get("coordinateId") or f"legacy-{self._target_id or ''}"
        )
        _populate_risk_direction_block(
            self.risk_direction_layout,
            risk_direction,
            coordinate_id=coordinate_id,
            ingress_focus=self._ingress_focus,
            on_ingress_view=self._on_ingress_view_clicked,
        )

    def show_target(
        self,
        detail: TargetCardDetail,
        markers: dict[str, Any] | list[dict[str, Any]] | None = None,
        *,
        corridor_flight_summary: str | None = None,
        weaponeering: dict[str, object] | None = None,
    ) -> None:
        marker_list: list[dict[str, Any]]
        if isinstance(markers, list):
            marker_list = markers
        elif isinstance(markers, dict):
            marker_list = [markers]
        else:
            marker_list = []
        if self._target_id != detail.card.id:
            self._ingress_focus = (None, None)
        self._target_id = detail.card.id
        self._last_marker_list = marker_list
        self._last_coordinate_points = detail.coordinates or []
        self.empty_label.setVisible(False)
        self.content_host.setVisible(True)

        self._rebuild_card(self.summary_layout)
        card = detail.card
        _populate_summary_block(
            self.summary_layout,
            card=card,
            detail=detail,
            pk_text=self._fmt_pk(card.target_pk or card.reference_pk),
        )

        primary_marker = next(
            (item for item in marker_list if item.get("isPrimary")),
            marker_list[0] if marker_list else None,
        )
        marker_product = (primary_marker or {}).get("effectProduct")
        if marker_product is not None:
            marker_product = str(marker_product)

        self._rebuild_card(self.weapon_layout)
        payload = weaponeering or {}
        product_catalog = payload.get("productCatalog") or []
        coordinate_products = payload.get("coordinateProducts") or []
        if coordinate_products:
            for item in coordinate_products:
                coordinate_id = str(item.get("coordinateId") or "")
                if not coordinate_id:
                    continue
                self.weapon_layout.addWidget(
                    _point_header(
                        str(item.get("label") or "P"),
                        is_primary=bool(item.get("isPrimary")),
                    )
                )
                effect_product = item.get("effectProduct")
                if effect_product:
                    self.weapon_layout.addWidget(
                        _compact_line(str(effect_product), accent=True)
                    )
                image_row = _product_image_row(
                    str(effect_product) if effect_product else None
                )
                if image_row is not None:
                    self.weapon_layout.addWidget(image_row)

                selected_id = item.get("selectedProductId")
                selected_id = str(selected_id) if selected_id else None

                def _make_handler(coord_id: str) -> Callable[[str | None], None]:
                    def _handler(product_id: str | None) -> None:
                        self.coordinate_product_changed.emit(coord_id, product_id)

                    return _handler

                self.weapon_layout.addWidget(
                    _product_selector_row(
                        product_catalog,
                        selected_id,
                        _make_handler(coordinate_id),
                    )
                )
                products = item.get("products") or []
                if products:
                    for rank_item in products[:5]:
                        self.weapon_layout.addWidget(
                            _product_rank_row(
                                int(rank_item.get("rank") or 0),
                                str(rank_item.get("productName") or "—"),
                                float(rank_item.get("pdBase") or 0.0),
                                rank_item.get("nRequired", "—"),
                            )
                        )
                else:
                    self.weapon_layout.addWidget(
                        _compact_line("ไม่มี Product Ranking", muted=True)
                    )
            self.weapon_layout.addWidget(_section_divider())
            _populate_weaponeering_block(
                self.weapon_layout,
                marker_product=None,
                weaponeering=payload,
                include_products=False,
            )
        else:
            _populate_weaponeering_block(
                self.weapon_layout,
                marker_product=marker_product,
                weaponeering=weaponeering,
            )

        self._rebuild_card(self.zones_layout)
        coordinate_points = detail.coordinates or []
        if coordinate_points and marker_list:
            for index, coord in enumerate(coordinate_points):
                point_marker = _marker_for_coordinate(
                    marker_list,
                    coordinate_id=coord.id,
                    lat=coord.map_lat,
                    lng=coord.map_lng,
                )
                effect_radii = (point_marker or {}).get("effectRadii") or []
                self.zones_layout.addWidget(
                    _point_header(
                        coord.label or f"P{index + 1}",
                        is_primary=coord.is_primary,
                    )
                )
                if effect_radii:
                    for item in effect_radii:
                        zone = str(item.get("zone", ""))
                        color = str(item.get("color") or EFFECT_ZONE_COLORS.get(zone, "#888"))
                        radius_ft = float(
                            item.get("radiusFt")
                            or (float(item.get("radiusM", 0)) / FEET_TO_METERS)
                        )
                        self.zones_layout.addWidget(_zone_row(zone, color, radius_ft))
                else:
                    self.zones_layout.addWidget(_compact_line("ยังไม่มีวงผลกระทบ", muted=True))
        else:
            primary_marker = next(
                (item for item in marker_list if item.get("isPrimary")),
                marker_list[0] if marker_list else None,
            )
            effect_radii = (primary_marker or {}).get("effectRadii") or []
            if effect_radii:
                for item in effect_radii:
                    zone = str(item.get("zone", ""))
                    color = str(item.get("color") or EFFECT_ZONE_COLORS.get(zone, "#888"))
                    radius_ft = float(
                        item.get("radiusFt")
                        or (float(item.get("radiusM", 0)) / FEET_TO_METERS)
                    )
                    self.zones_layout.addWidget(_zone_row(zone, color, radius_ft))
            else:
                self.zones_layout.addWidget(_compact_line("ยังไม่มีวงผลกระทบ", muted=True))

        self._rebuild_card(self.risk_direction_layout)
        if coordinate_points and marker_list:
            for index, coord in enumerate(coordinate_points):
                point_marker = _marker_for_coordinate(
                    marker_list,
                    coordinate_id=coord.id,
                    lat=coord.map_lat,
                    lng=coord.map_lng,
                )
                self.risk_direction_layout.addWidget(
                    _point_header(
                        coord.label or f"P{index + 1}",
                        is_primary=coord.is_primary,
                    )
                )
                risk_direction = (point_marker or {}).get("lowestRiskDirection") or {}
                _populate_risk_direction_block(
                    self.risk_direction_layout,
                    risk_direction,
                    coordinate_id=coord.id,
                    ingress_focus=self._ingress_focus,
                    on_ingress_view=self._on_ingress_view_clicked,
                )
        else:
            primary_marker = next(
                (item for item in marker_list if item.get("isPrimary")),
                marker_list[0] if marker_list else None,
            )
            risk_direction = (primary_marker or {}).get("lowestRiskDirection") or {}
            coordinate_id = str(
                (primary_marker or {}).get("coordinateId") or f"legacy-{detail.card.id}"
            )
            _populate_risk_direction_block(
                self.risk_direction_layout,
                risk_direction,
                coordinate_id=coordinate_id,
                ingress_focus=self._ingress_focus,
                on_ingress_view=self._on_ingress_view_clicked,
            )

        self._rebuild_card(self.flight_route_layout)
        if corridor_flight_summary:
            self.flight_route_card.setVisible(True)
            self.flight_route_layout.addWidget(
                _compact_line(corridor_flight_summary, muted=True)
            )
        else:
            self.flight_route_card.setVisible(False)

    @staticmethod
    def _fmt_pk(value: float | None) -> str:
        if value is None:
            return "—"
        return f"{value:.2f}"

    @staticmethod
    def _rebuild_card(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
