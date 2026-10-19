from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.ai.service import AiAssistantService
from maap_app.modules.target.schemas import (
    CreateTargetCardRequest,
    LinkTargetMapNodeRequest,
    TargetFilterParams,
)
from maap_app.modules.target.service import TargetService
from maap_app.ui.dialogs.target_dialogs import CreateTargetCardDialog


def _tag(text: str, style: str) -> QLabel:
    tag = QLabel(text)
    tag.setObjectName(style)
    return tag


_CATEGORY_ACCENT = "#3b82f6"


class LeftTargetPanel(QWidget):
    target_selected = Signal(str)
    targets_changed = Signal()
    ai_summary_ready = Signal(str, str)

    def __init__(
        self,
        target_service: TargetService,
        ai_service: AiAssistantService | None = None,
    ) -> None:
        super().__init__()
        self.target_service = target_service
        self.ai_service = ai_service
        self._scenario_id: str | None = None
        self._selected_target_id: str | None = None
        self._filters = TargetFilterParams()
        self._card_widgets: dict[str, QWidget] = {}

        self.setObjectName("SidePanel")
        self.setMinimumWidth(260)
        self.setMaximumWidth(340)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)

        header_row = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet("color: #4ade80; font-size: 10px;")
        section = QLabel("TARGET STACK")
        section.setObjectName("SectionTitle")
        self.count_label = QLabel("0 targets")
        self.count_label.setStyleSheet("color: #5f7389; font-size: 10px;")
        header_row.addWidget(dot)
        header_row.addWidget(section)
        header_row.addStretch(1)
        header_row.addWidget(self.count_label)
        outer.addLayout(header_row)

        self.subtitle = QLabel("Synthetic scenario objects")
        self.subtitle.setObjectName("SectionSubtitle")
        outer.addWidget(self.subtitle)

        self.review_filter = QComboBox()
        self.review_filter.hide()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stack = QWidget()
        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        self.stack_layout.setSpacing(8)
        self.empty_label = QLabel("No Target Cards in this scenario.\nUse + Add Target Object to begin.")
        self.empty_label.setStyleSheet("color: #6b7f96; font-size: 11px; padding: 12px;")
        self.empty_label.setWordWrap(True)
        self.stack_layout.addWidget(self.empty_label)
        self.stack_layout.addStretch(1)
        self.scroll.setWidget(self.stack)
        outer.addWidget(self.scroll, stretch=1)

        add_btn = QPushButton("+ Add Target Object")
        add_btn.setObjectName("GhostButton")
        add_btn.clicked.connect(self._on_add_target)
        outer.addWidget(add_btn)

    def set_scenario(self, scenario_id: str | None, scenario_name: str = "") -> None:
        self._scenario_id = scenario_id
        self._selected_target_id = None
        if scenario_id:
            self.subtitle.setText(
                f"Synthetic scenario objects | {scenario_name or scenario_id}"
            )
        else:
            self.subtitle.setText("No active scenario selected")
        self.refresh()

    def set_search_text(self, text: str) -> None:
        self._filters.search_text = text.strip()
        self.refresh()

    def select_target(self, target_id: str) -> None:
        self._selected_target_id = target_id
        self._update_card_selection()
        self.target_selected.emit(target_id)

    def refresh(self) -> None:
        self._clear_cards()
        if not self._scenario_id:
            self.empty_label.setText("No active scenario.\nCreate or open a scenario first.")
            self.empty_label.show()
            self.count_label.setText("0 targets")
            return

        items = self.target_service.list_target_cards(self._scenario_id, self._filters)
        self.count_label.setText(f"{len(items)} target{'s' if len(items) != 1 else ''}")

        if not items:
            self.empty_label.setText(
                "No Target Cards match the current filters.\n"
                "Use + Add Target Object or clear filters."
            )
            self.empty_label.show()
            return

        self.empty_label.hide()
        for index, item in enumerate(items):
            card = item.card
            accent = _CATEGORY_ACCENT
            tags: list[tuple[str, str]] = []
            if card.review_status == "draft":
                tags.append(("DRAFT", "TagPlaceholder"))
            elif card.review_status == "requires_review":
                tags.append(("REVIEW", "TagSupport"))

            lines = [
                f"Priority: {card.priority_score}/5 | Complexity: {card.complexity_score}/5",
            ]
            if item.recognition_confidence is not None:
                lines.append(f"Confidence: {item.recognition_confidence}/100")
            if item.warning_count:
                lines.append(f"Warnings: {item.warning_count}")

            widget = self._build_card_widget(
                card.id,
                card.label,
                tags,
                lines,
                card.created_at or "Just now",
                accent,
                card.id == self._selected_target_id,
            )
            self.stack_layout.insertWidget(index, widget)
            self._card_widgets[card.id] = widget

    def _build_card_widget(
        self,
        target_id: str,
        title: str,
        tags: list[tuple[str, str]],
        lines: list[str],
        timestamp: str,
        accent: str,
        selected: bool,
    ) -> QWidget:
        card = QWidget()
        card.setObjectName("TargetCard")
        card.setProperty("selected", "true" if selected else "false")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(
            f"QWidget#TargetCard {{ border-left: 3px solid {accent}; }}"
            + ("QWidget#TargetCard { background: #101c2b; }" if selected else "")
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        for text, style in tags:
            title_row.addWidget(_tag(text, style))
        layout.addLayout(title_row)

        for line in lines:
            line_label = QLabel(line)
            line_label.setStyleSheet("color: #7b8fa3; font-size: 11px;")
            layout.addWidget(line_label)

        time_label = QLabel(f"Created: {timestamp}")
        time_label.setStyleSheet("color: #5f7389; font-size: 10px;")
        layout.addWidget(time_label)

        card.mousePressEvent = lambda _e, tid=target_id: self.select_target(tid)  # type: ignore[method-assign]
        return card

    def _clear_cards(self) -> None:
        for widget in self._card_widgets.values():
            self.stack_layout.removeWidget(widget)
            widget.deleteLater()
        self._card_widgets.clear()

    def _update_card_selection(self) -> None:
        for tid, widget in self._card_widgets.items():
            selected = tid == self._selected_target_id
            widget.setProperty("selected", "true" if selected else "false")
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _on_add_target(self) -> None:
        if not self._scenario_id:
            QMessageBox.warning(self, "No scenario", "Select or create a scenario first.")
            return
        dialog = CreateTargetCardDialog(self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if not values["label"]:
            QMessageBox.warning(self, "Validation", "Target label is required.")
            return
        try:
            target_id = self.target_service.create_target_card(
                CreateTargetCardRequest(
                    scenario_id=self._scenario_id,
                    label=values["label"],
                    priority_score=values["priority_score"],
                    complexity_score=values["complexity_score"],
                )
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Guardrail", str(exc))
            return
        self.select_target(target_id)
        self.refresh()
        self.targets_changed.emit()

    def complete_map_link(self, target_id: str, lat: float, lng: float) -> None:
        if not self._scenario_id:
            return
        try:
            self.target_service.link_target_to_map(
                LinkTargetMapNodeRequest(
                    target_card_id=target_id,
                    scenario_id=self._scenario_id,
                    map_lat=lat,
                    map_lng=lng,
                )
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Link failed", str(exc))
            return
        self.select_target(target_id)
        self.refresh()
        self.targets_changed.emit()
