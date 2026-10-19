from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.ai.service import AiAssistantService
from maap_app.modules.target.profile_fields import TargetProfileFields
from maap_app.modules.target.schemas import (
    SaveTargetCoordinatesRequest,
    TargetCoordinateInput,
    TargetFilterParams,
)
from maap_app.modules.target.models import TargetCardDetail
from maap_app.modules.target.service import TargetService
from maap_app.ui.panels.target_form_panel import TargetFormPanel


_REVIEW_LABELS = {
    "draft": "ร่าง",
    "requires_review": "รอตรวจ",
    "approved": "อนุมัติ",
    "rejected": "ปฏิเสธ",
}

_CARD_ACCENT = "#3b82f6"


@dataclass(frozen=True)
class TargetCalculationSnapshot:
    profile: TargetProfileFields
    map_lat: float | None
    map_lng: float | None
    coordinates: tuple[TargetCoordinateInput, ...] = ()


def _tag(text: str, style: str) -> QLabel:
    tag = QLabel(text)
    tag.setObjectName(style)
    return tag


def _workspace_section(title: str, subtitle: str, panel: QWidget) -> QWidget:
    host = QWidget()
    host.setObjectName("MapWorkspace")
    layout = QVBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    header = QWidget()
    header.setObjectName("MapWorkspaceHeader")
    header.setFixedHeight(42)
    hl = QHBoxLayout(header)
    hl.setContentsMargins(12, 0, 12, 0)
    tb = QVBoxLayout()
    tb.setSpacing(0)
    t = QLabel(title)
    t.setObjectName("MapWorkspaceTitle")
    sub = QLabel(subtitle)
    sub.setObjectName("SectionSubtitle")
    tb.addWidget(t)
    tb.addWidget(sub)
    hl.addLayout(tb)
    hl.addStretch(1)
    layout.addWidget(header)

    body = QWidget()
    bl = QVBoxLayout(body)
    bl.setContentsMargins(0, 0, 0, 0)
    bl.addWidget(panel, stretch=1)
    layout.addWidget(body, stretch=1)
    return host


class TargetSidebar(QWidget):
    target_selected = Signal(str)
    targets_changed = Signal()
    create_target_requested = Signal()
    generate_random_target_requested = Signal()

    def __init__(
        self,
        target_service: TargetService,
        ai_service: AiAssistantService | None = None,
    ) -> None:
        super().__init__()
        self.target_service = target_service
        self.ai_service = ai_service
        self._scenario_id: str | None = None
        self._selected_id: str | None = None
        self._filters = TargetFilterParams()
        self._card_widgets: dict[str, QWidget] = {}
        self.setObjectName("SidePanel")
        self.setMinimumWidth(260)
        self.setMaximumWidth(320)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        header_row = QHBoxLayout()
        title = QLabel("TARGET STACK")
        title.setObjectName("SectionTitle")
        self.count_label = QLabel("0 targets")
        self.count_label.setStyleSheet("color: #5f7389; font-size: 10px;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        header_row.addWidget(self.count_label)
        outer.addLayout(header_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stack = QWidget()
        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        self.stack_layout.setSpacing(6)
        self.empty_label = QLabel("ยังไม่มี Target Card\nกด + เพิ่มเป้าหมาย เพื่อเริ่มต้น")
        self.empty_label.setStyleSheet("color: #6b7f96; font-size: 11px; padding: 8px;")
        self.empty_label.setWordWrap(True)
        self.stack_layout.addWidget(self.empty_label)
        self.stack_layout.addStretch(1)
        self.scroll.setWidget(self.stack)
        outer.addWidget(self.scroll, stretch=1)

        footer = QVBoxLayout()
        footer.setSpacing(6)
        top_row = QHBoxLayout()
        self.add_btn = QPushButton("+ เพิ่มเป้าหมาย")
        self.add_btn.setObjectName("GhostButton")
        self.add_btn.clicked.connect(self._on_add_target)
        self.random_btn = QPushButton("🎲 สุ่มเป้าหมาย")
        self.random_btn.setObjectName("GhostButton")
        self.random_btn.clicked.connect(self._on_generate_random)
        top_row.addWidget(self.add_btn, stretch=1)
        top_row.addWidget(self.random_btn, stretch=1)
        footer.addLayout(top_row)
        self.delete_btn = QPushButton("ลบเป้าหมาย")
        self.delete_btn.setObjectName("DangerButton")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete_target)
        footer.addWidget(self.delete_btn)
        outer.addLayout(footer)

    def _on_add_target(self) -> None:
        self._selected_id = None
        self._update_card_selection()
        self.create_target_requested.emit()

    def _on_generate_random(self) -> None:
        self._selected_id = None
        self._update_card_selection()
        self.generate_random_target_requested.emit()

    def _on_delete_target(self) -> None:
        if not self._selected_id or not self._scenario_id:
            return
        answer = QMessageBox.question(
            self,
            "ลบเป้าหมาย",
            "ลบ Target นี้ถาวร?\n"
            "ข้อมูลทั้งหมด (พิกัด, อาวุธ, การตรวจจับ, ประวัติ AI)\n"
            "จะถูกลบและไม่สามารถกู้คืนได้",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        target_id = self._selected_id
        deleted_label = target_id
        try:
            detail = self.target_service.get_target_detail(target_id)
            if detail:
                deleted_label = detail.card.label
        except Exception:
            pass
        try:
            self.target_service.delete_target_card(target_id)
        except ValueError as exc:
            QMessageBox.warning(self, "ลบไม่สำเร็จ", str(exc))
            return
        if self.ai_service:
            self.ai_service.clear_chat_memory(self._scenario_id, target_id)
            self.ai_service.record_target_deleted_event(self._scenario_id, deleted_label)
        self._selected_id = None
        self.delete_btn.setEnabled(False)
        self.refresh()
        self.targets_changed.emit()

    def set_scenario(self, scenario_id: str | None) -> None:
        self._scenario_id = scenario_id
        self._selected_id = None
        self.delete_btn.setEnabled(False)
        self.refresh()

    def refresh(self) -> None:
        self._clear_cards()
        if not self._scenario_id:
            self.count_label.setText("0 targets")
            self.empty_label.setText("ยังไม่มี scenario ที่ใช้งาน")
            self.empty_label.show()
            return

        items = self.target_service.list_target_cards(self._scenario_id, self._filters)
        self.count_label.setText(f"{len(items)} target{'s' if len(items) != 1 else ''}")

        if not items:
            self.empty_label.setText("ยังไม่มี Target Card\nกด + เพิ่มเป้าหมาย เพื่อเริ่มต้น")
            self.empty_label.show()
            if self._selected_id:
                self._selected_id = None
            return

        self.empty_label.hide()
        for index, item in enumerate(items):
            card = item.card
            tags: list[tuple[str, str]] = [(card.target_type, "TagTraining")]
            if card.target_subtype:
                tags.append((card.target_subtype, "TagPlaceholder"))
            status = _REVIEW_LABELS.get(card.review_status, card.review_status)
            tags.append((status, "TagPlaceholder"))
            lines = [
                f"P{card.priority_score}/5 · C{card.complexity_score}/5",
            ]
            if card.material_class and card.material_class != "UNKNOWN":
                lines.append(card.material_class)
            if item.recognition_confidence is not None:
                lines.append(f"Conf {item.recognition_confidence}/100")

            widget = self._build_card_widget(
                card.id,
                card.label,
                tags,
                lines,
                card.id == self._selected_id,
            )
            self.stack_layout.insertWidget(index, widget)
            self._card_widgets[card.id] = widget

        if self._selected_id and self._selected_id not in self._card_widgets:
            self._selected_id = None

    def select_target(self, target_id: str) -> None:
        if target_id not in self._card_widgets:
            self.refresh()
        self._selected_id = target_id
        self._update_card_selection()
        self.delete_btn.setEnabled(True)
        self.target_selected.emit(target_id)

    def selected_target_id(self) -> str | None:
        return self._selected_id

    def complete_map_link(self, target_id: str, lat: float, lng: float) -> None:
        if not self._scenario_id:
            return
        try:
            self.target_service.save_target_coordinates(
                SaveTargetCoordinatesRequest(
                    target_card_id=target_id,
                    scenario_id=self._scenario_id,
                    coordinates=[
                        TargetCoordinateInput(
                            label="P1",
                            map_lat=lat,
                            map_lng=lng,
                            is_primary=True,
                        )
                    ],
                )
            )
        except ValueError as exc:
            QMessageBox.warning(self, "เชื่อมแผนที่ไม่สำเร็จ", str(exc))
            return
        self.select_target(target_id)
        self.targets_changed.emit()

    def _build_card_widget(
        self,
        target_id: str,
        title: str,
        tags: list[tuple[str, str]],
        lines: list[str],
        selected: bool,
    ) -> QWidget:
        card = QWidget()
        card.setObjectName("TargetCard")
        card.setProperty("selected", "true" if selected else "false")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(
            f"QWidget#TargetCard {{ border-left: 3px solid {_CARD_ACCENT}; }}"
            + ("QWidget#TargetCard { background: #101c2b; }" if selected else "")
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        title_label.setWordWrap(True)
        title_row.addWidget(title_label, stretch=1)
        layout.addLayout(title_row)

        tag_row = QHBoxLayout()
        for text, style in tags[:2]:
            tag_row.addWidget(_tag(text[:14], style))
        tag_row.addStretch(1)
        layout.addLayout(tag_row)

        for line in lines:
            line_label = QLabel(line)
            line_label.setStyleSheet("color: #7b8fa3; font-size: 10px;")
            layout.addWidget(line_label)

        card.mousePressEvent = lambda _e, tid=target_id: self.select_target(tid)  # type: ignore[method-assign]
        return card

    def _clear_cards(self) -> None:
        for widget in self._card_widgets.values():
            self.stack_layout.removeWidget(widget)
            widget.deleteLater()
        self._card_widgets.clear()

    def _update_card_selection(self) -> None:
        for tid, widget in self._card_widgets.items():
            selected = tid == self._selected_id
            widget.setProperty("selected", "true" if selected else "false")
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.setStyleSheet(
                f"QWidget#TargetCard {{ border-left: 3px solid {_CARD_ACCENT}; }}"
                + ("QWidget#TargetCard { background: #101c2b; }" if selected else "")
            )


class TargetPanel(QWidget):
    target_selected = Signal(str)
    targets_changed = Signal()
    map_search_requested = Signal(float, float)

    def __init__(
        self,
        target_service: TargetService,
        ai_service: AiAssistantService | None,
        weaponeering_panel: QWidget,
    ) -> None:
        super().__init__()
        self.target_service = target_service
        self.ai_service = ai_service
        self.weaponeering_panel = weaponeering_panel
        self._scenario_id: str | None = None

        self.setObjectName("MapWorkspace")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setObjectName("MapWorkspaceHeader")
        header.setFixedHeight(48)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 14, 0)
        title_block = QVBoxLayout()
        title_block.setSpacing(0)
        title = QLabel("ข้อมูลเป้าหมาย")
        title.setObjectName("MapWorkspaceTitle")
        self.subtitle = QLabel("Target Stack · Target Form · Weaponeering")
        self.subtitle.setObjectName("SectionSubtitle")
        title_block.addWidget(title)
        title_block.addWidget(self.subtitle)
        hl.addLayout(title_block)
        hl.addStretch(1)
        root.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(8, 8, 8, 8)

        grid = QSplitter(Qt.Orientation.Horizontal)
        grid.setHandleWidth(6)
        grid.setChildrenCollapsible(False)

        self.sidebar = TargetSidebar(target_service, ai_service)
        self.form_panel = TargetFormPanel(target_service)
        form_section = _workspace_section(
            "TARGET FORM",
            "แก้ไขข้อมูลเป้าหมาย สนามพิกัด และคุณลักษณะ",
            self.form_panel,
        )
        weaponeering_section = _workspace_section(
            "WEAPONEERING",
            "JMEM Pd ranking, range zones และคำนวณจาก Target Stack",
            weaponeering_panel,
        )

        grid.addWidget(self.sidebar)
        grid.addWidget(form_section)
        grid.addWidget(weaponeering_section)
        grid.setStretchFactor(0, 1)
        grid.setStretchFactor(1, 2)
        grid.setStretchFactor(2, 2)
        grid.setSizes([280, 420, 420])

        body.addWidget(grid, stretch=1)
        self.status_label = QLabel(
            "เลือก Target จากรายการด้านซ้าย · แก้ไขในฟอร์มกลาง · กดบันทึกเพื่อยืนยัน"
        )
        self.status_label.setStyleSheet("color: #6b7f96; font-size: 11px;")
        body.addWidget(self.status_label)

        body_widget = QWidget()
        body_widget.setLayout(body)
        root.addWidget(body_widget, stretch=1)

        self.sidebar.target_selected.connect(self._on_sidebar_target_selected)
        self.sidebar.create_target_requested.connect(self.form_panel.begin_create)
        self.sidebar.generate_random_target_requested.connect(self.form_panel.begin_create_random)
        self.sidebar.targets_changed.connect(self.targets_changed.emit)
        self.form_panel.target_saved.connect(self._on_form_target_saved)
        self.form_panel.target_archived.connect(self._on_target_archived)
        self.form_panel.targets_changed.connect(self._on_form_targets_changed)
        self.form_panel.map_search_requested.connect(self.map_search_requested.emit)

    def _on_sidebar_target_selected(self, target_id: str) -> None:
        self.form_panel.load_target(target_id)
        self.target_selected.emit(target_id)

    def _on_form_target_saved(self, _target_id: str) -> None:
        self.sidebar.refresh()
        current_id = self.form_panel._target_id
        if current_id:
            self.sidebar.select_target(current_id)

    def _on_target_archived(self, target_id: str) -> None:
        if self.ai_service and self._scenario_id:
            self.ai_service.clear_chat_memory(self._scenario_id, target_id)

    def _on_form_targets_changed(self) -> None:
        self.sidebar.refresh()
        self.targets_changed.emit()

    def set_scenario(self, scenario_id: str | None, scenario_name: str = "") -> None:
        self._scenario_id = scenario_id
        if scenario_id:
            self.subtitle.setText(
                f"Target Stack · Target Form · Weaponeering | {scenario_name or scenario_id}"
            )
        else:
            self.subtitle.setText("Target Stack · Target Form · Weaponeering")
        self.sidebar.set_scenario(scenario_id)
        self.form_panel.set_scenario(scenario_id)

    def refresh(self) -> None:
        self.sidebar.refresh()

    def select_target(self, target_id: str) -> None:
        self.sidebar.select_target(target_id)
        self.form_panel.load_target(target_id)

    def get_calculation_snapshot(
        self,
        target_id: str,
    ) -> TargetCalculationSnapshot | None:
        if self.form_panel._target_id != target_id:
            return None
        _, _, _, profile, coordinates = self.form_panel.profile_form.values()
        primary = self.form_panel.profile_form.primary_coordinate()
        map_lat, map_lng = (primary if primary else (None, None))
        detail = self.target_service.get_target_detail(target_id)
        saved_by_key: dict[tuple[str, float, float], object] = {}
        if detail is not None:
            for coord in detail.coordinates:
                saved_by_key[
                    (
                        coord.label.strip(),
                        round(coord.map_lat, 5),
                        round(coord.map_lng, 5),
                    )
                ] = coord
        enriched: list[TargetCoordinateInput] = []
        for coord in coordinates:
            saved = saved_by_key.get(
                (
                    coord.label.strip(),
                    round(coord.map_lat, 5),
                    round(coord.map_lng, 5),
                )
            )
            enriched.append(
                TargetCoordinateInput(
                    label=coord.label,
                    map_lat=coord.map_lat,
                    map_lng=coord.map_lng,
                    is_primary=coord.is_primary,
                    id=coord.id or (saved.id if saved is not None else None),
                    selected_product_id=(
                        coord.selected_product_id
                        if coord.selected_product_id is not None
                        else (
                            saved.selected_product_id
                            if saved is not None
                            else None
                        )
                    ),
                )
            )
        return TargetCalculationSnapshot(
            profile=profile,
            map_lat=map_lat,
            map_lng=map_lng,
            coordinates=tuple(enriched),
        )

    def get_detection_coordinates(self, target_id: str) -> list[dict[str, object]]:
        detail = self.target_service.get_target_detail(target_id)
        saved = self._saved_detection_coordinates(target_id, detail)
        if self.form_panel._target_id == target_id:
            values = self.form_panel.profile_form.coordinates_widget.get_coordinates()
            if values and not self._form_matches_saved_coordinates(values, saved):
                return [
                    {
                        "id": f"draft-{index}",
                        "label": coord.label.strip() or f"P{index + 1}",
                        "lat": coord.map_lat,
                        "lng": coord.map_lng,
                        "isPrimary": coord.is_primary,
                    }
                    for index, coord in enumerate(values)
                ]
        return saved

    @staticmethod
    def _coord_label(label: str, index: int) -> str:
        text = label.strip()
        return text or f"P{index + 1}"

    def _saved_detection_coordinates(
        self,
        target_id: str,
        detail: TargetCardDetail | None,
    ) -> list[dict[str, object]]:
        if detail is None:
            return []
        if detail.coordinates:
            return [
                {
                    "id": coord.id,
                    "label": self._coord_label(coord.label, index),
                    "lat": coord.map_lat,
                    "lng": coord.map_lng,
                    "isPrimary": coord.is_primary,
                }
                for index, coord in enumerate(detail.coordinates)
            ]
        if detail.map_lat is not None and detail.map_lng is not None:
            return [
                {
                    "id": f"legacy-{target_id}",
                    "label": "P1",
                    "lat": detail.map_lat,
                    "lng": detail.map_lng,
                    "isPrimary": True,
                }
            ]
        return []

    @staticmethod
    def _form_matches_saved_coordinates(
        form_values: list[TargetCoordinateInput],
        saved: list[dict[str, object]],
    ) -> bool:
        if len(form_values) != len(saved):
            return False
        for index, (form, saved_item) in enumerate(zip(form_values, saved)):
            if TargetPanel._coord_label(form.label, index) != str(
                saved_item.get("label") or ""
            ).strip():
                return False
            if abs(form.map_lat - float(saved_item.get("lat") or 0.0)) > 1e-4:
                return False
            if abs(form.map_lng - float(saved_item.get("lng") or 0.0)) > 1e-4:
                return False
            if form.is_primary != bool(saved_item.get("isPrimary")):
                return False
        return True

    def complete_map_link(self, target_id: str, lat: float, lng: float) -> None:
        self.sidebar.complete_map_link(target_id, lat, lng)
        if self.form_panel._target_id == target_id:
            self.form_panel.set_coordinates(lat, lng)

    def set_coordinates(self, lat: float, lng: float) -> None:
        self.form_panel.set_coordinates(lat, lng)
