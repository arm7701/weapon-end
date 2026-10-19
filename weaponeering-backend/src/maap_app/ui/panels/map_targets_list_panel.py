from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.detection.persistence_service import TargetDetectionService
from maap_app.modules.target.service import TargetService

PriorityTier = Literal["high", "medium", "low"]
SortMode = Literal["last_detected", "priority", "label"]

_TIER_LABELS = {"high": "High", "medium": "Medium", "low": "Low"}
_TIER_COLORS = {
    "high": ("#ef4444", "#7f1d1d"),
    "medium": ("#f59e0b", "#78350f"),
    "low": ("#22c55e", "#14532d"),
}


@dataclass(frozen=True)
class MapTargetListEntry:
    target_id: str
    coordinate_id: str | None
    title: str
    coordinates_text: str
    target_type: str
    priority_tier: PriorityTier
    detected_at: str | None

    @property
    def key(self) -> str:
        return f"{self.target_id}:{self.coordinate_id or ''}"


def priority_tier_from_score(score: int) -> PriorityTier:
    if score >= 4:
        return "high"
    if score == 3:
        return "medium"
    return "low"


def format_detected_ago(timestamp: str | None) -> str:
    if not timestamp:
        return "Not yet"
    try:
        normalized = timestamp.replace("Z", "+00:00")
        detected = datetime.fromisoformat(normalized)
    except ValueError:
        return timestamp
    if detected.tzinfo is not None:
        detected = detected.replace(tzinfo=None)
    delta = datetime.now() - detected
    seconds = max(int(delta.total_seconds()), 0)
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86_400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86_400}d ago"


def format_target_type(target_type: str) -> str:
    text = target_type.replace("_", " ").strip().title()
    return text or "Building"


class _TargetListCard(QFrame):
    clicked = Signal()
    double_clicked = Signal()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


class MapTargetsListPanel(QWidget):
    entry_selected = Signal(str, str)
    view_all_requested = Signal()
    open_in_target_stack = Signal(str)

    def __init__(
        self,
        target_service: TargetService,
        detection_service: TargetDetectionService,
    ) -> None:
        super().__init__()
        self._target_service = target_service
        self._detection_service = detection_service
        self._scenario_id: str | None = None
        self._entries: list[MapTargetListEntry] = []
        self._card_widgets: dict[str, QWidget] = {}
        self._selected_key: str | None = None
        self._priority_filter: PriorityTier | None = None
        self._sort_mode: SortMode = "last_detected"
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("MapTargetSearch")
        self.search_input.setPlaceholderText("Search targets...")
        self.search_input.textChanged.connect(self._apply_filters)
        search_row.addWidget(self.search_input, stretch=1)

        self.filter_btn = QToolButton()
        self.filter_btn.setObjectName("MapTargetIconButton")
        self.filter_btn.setText("⛃")
        self.filter_btn.setToolTip("กรองตามระดับความสำคัญ")
        self.filter_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        filter_menu = QMenu(self.filter_btn)
        filter_menu.setObjectName("MapToolbarMenu")
        filter_group = QActionGroup(self)
        filter_group.setExclusive(True)
        self._filter_actions: dict[str | None, QAction] = {}
        for label, tier in (
            ("All priorities", None),
            ("High only", "high"),
            ("Medium only", "medium"),
            ("Low only", "low"),
        ):
            action = QAction(label, filter_menu)
            action.setCheckable(True)
            action.setChecked(tier is None)
            filter_group.addAction(action)
            action.triggered.connect(
                lambda _checked=False, value=tier: self._set_priority_filter(value)
            )
            self._filter_actions[tier] = action
            filter_menu.addAction(action)
        self.filter_btn.setMenu(filter_menu)
        search_row.addWidget(self.filter_btn)
        root.addLayout(search_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(6)
        self._stat_labels: dict[str, QLabel] = {}
        for tier, title in (
            ("total", "Total"),
            ("high", "High"),
            ("medium", "Medium"),
            ("low", "Low"),
        ):
            stat = self._build_stat_card(title, tier)
            stats_row.addWidget(stat)
        root.addLayout(stats_row)

        sort_row = QHBoxLayout()
        sort_row.setSpacing(6)
        sort_label = QLabel("Sort:")
        sort_label.setObjectName("MapTargetMutedLabel")
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("MapTargetSortCombo")
        self.sort_combo.addItem("Last Detected", "last_detected")
        self.sort_combo.addItem("Priority", "priority")
        self.sort_combo.addItem("Label", "label")
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        sort_row.addWidget(sort_label)
        sort_row.addWidget(self.sort_combo, stretch=1)
        root.addLayout(sort_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setObjectName("MapTargetScroll")
        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.empty_label = QLabel("ยังไม่มี Target ใน scenario นี้")
        self.empty_label.setObjectName("MapTargetMutedLabel")
        self.empty_label.setWordWrap(True)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_layout.addWidget(self.empty_label)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.list_host)
        root.addWidget(self.scroll, stretch=1)

        footer_btn = QPushButton("View All Targets  ›")
        footer_btn.setObjectName("MapTargetFooterButton")
        footer_btn.clicked.connect(self.view_all_requested.emit)
        root.addWidget(footer_btn)

    def _build_stat_card(self, title: str, tier: str) -> QWidget:
        card = QWidget()
        card.setObjectName("MapTargetStatCard")
        card.setProperty("tier", tier)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        label = QLabel(title)
        label.setObjectName("MapTargetStatTitle")
        label.setProperty("tier", tier)
        value = QLabel("0")
        value.setObjectName("MapTargetStatValue")
        value.setProperty("tier", tier)
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addWidget(value)
        self._stat_labels[tier] = value
        return card

    def set_scenario(self, scenario_id: str | None) -> None:
        self._scenario_id = scenario_id
        self._selected_key = None
        self.refresh()

    def refresh(self) -> None:
        self._entries = self._load_entries()
        self._update_stats()
        self._apply_filters()

    def select_entry(
        self,
        target_id: str,
        coordinate_id: str | None = None,
    ) -> None:
        self._selected_key = f"{target_id}:{coordinate_id or ''}"
        self._update_card_selection()

    def clear_selection(self) -> None:
        self._selected_key = None
        self._update_card_selection()

    def _load_entries(self) -> list[MapTargetListEntry]:
        if not self._scenario_id:
            return []

        detection_index: dict[tuple[str, str], str | None] = {}
        for run in self._detection_service.repository.list_runs_for_scenario(
            self._scenario_id
        ):
            key = (run.target_card_id, run.target_coordinate_id)
            existing = detection_index.get(key)
            if existing is None or (run.updated_at or "") > (existing or ""):
                detection_index[key] = run.updated_at

        entries: list[MapTargetListEntry] = []
        for item in self._target_service.list_target_cards(self._scenario_id):
            detail = self._target_service.get_target_detail(item.card.id)
            if detail is None:
                continue
            tier = priority_tier_from_score(item.card.priority_score)
            target_type = format_target_type(detail.card.target_type)

            if detail.coordinates:
                for index, coord in enumerate(detail.coordinates):
                    point_label = coord.label.strip() or f"P{index + 1}"
                    if len(detail.coordinates) == 1:
                        title = detail.card.label
                    else:
                        title = f"{point_label}-{coord.map_lat:.5f},{coord.map_lng:.5f}"
                    detected_at = detection_index.get((detail.card.id, coord.id))
                    entries.append(
                        MapTargetListEntry(
                            target_id=detail.card.id,
                            coordinate_id=coord.id,
                            title=title,
                            coordinates_text=f"{coord.map_lat:.5f}, {coord.map_lng:.5f}",
                            target_type=target_type,
                            priority_tier=tier,
                            detected_at=detected_at,
                        )
                    )
                continue

            if detail.map_lat is None or detail.map_lng is None:
                continue
            legacy_id = f"legacy-{detail.card.id}"
            detected_at = detection_index.get((detail.card.id, legacy_id))
            entries.append(
                MapTargetListEntry(
                    target_id=detail.card.id,
                    coordinate_id=legacy_id,
                    title=detail.card.label,
                    coordinates_text=f"{detail.map_lat:.5f}, {detail.map_lng:.5f}",
                    target_type=target_type,
                    priority_tier=tier,
                    detected_at=detected_at,
                )
            )
        return entries

    def _update_stats(self) -> None:
        total = len(self._entries)
        counts = {"high": 0, "medium": 0, "low": 0}
        for entry in self._entries:
            counts[entry.priority_tier] += 1
        self._stat_labels["total"].setText(str(total))
        self._stat_labels["high"].setText(str(counts["high"]))
        self._stat_labels["medium"].setText(str(counts["medium"]))
        self._stat_labels["low"].setText(str(counts["low"]))

    def _set_priority_filter(self, tier: PriorityTier | None) -> None:
        self._priority_filter = tier
        for key, action in self._filter_actions.items():
            action.setChecked(key == tier)
        self._apply_filters()

    def _on_sort_changed(self) -> None:
        self._sort_mode = str(self.sort_combo.currentData() or "last_detected")  # type: ignore[assignment]
        self._apply_filters()

    def _apply_filters(self) -> None:
        needle = self.search_input.text().strip().lower()
        visible = [
            entry
            for entry in self._entries
            if self._priority_filter is None or entry.priority_tier == self._priority_filter
            if not needle
            or needle in entry.title.lower()
            or needle in entry.coordinates_text.lower()
            or needle in entry.target_type.lower()
        ]
        visible = self._sort_entries(visible)
        self._render_cards(visible)

    def _sort_entries(self, entries: list[MapTargetListEntry]) -> list[MapTargetListEntry]:
        if self._sort_mode == "label":
            return sorted(entries, key=lambda item: item.title.lower())
        if self._sort_mode == "priority":
            order = {"high": 0, "medium": 1, "low": 2}
            return sorted(
                entries,
                key=lambda item: (order[item.priority_tier], item.title.lower()),
            )
        return sorted(
            entries,
            key=lambda item: (item.detected_at or "", item.title.lower()),
            reverse=True,
        )

    def _render_cards(self, entries: list[MapTargetListEntry]) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._card_widgets.clear()

        if not entries:
            self.empty_label = QLabel(
                "ไม่พบ Target ตามเงื่อนไข"
                if self._entries
                else "ยังไม่มี Target ใน scenario นี้"
            )
            self.empty_label.setObjectName("MapTargetMutedLabel")
            self.empty_label.setWordWrap(True)
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(self.empty_label)
            self.list_layout.addStretch(1)
            return

        self.empty_label = QLabel()
        for entry in entries:
            card = self._build_entry_card(entry)
            self.list_layout.addWidget(card)
            self._card_widgets[entry.key] = card
        self.list_layout.addStretch(1)
        self._update_card_selection()

    def _build_entry_card(self, entry: MapTargetListEntry) -> QWidget:
        accent, _ = _TIER_COLORS[entry.priority_tier]
        card = _TargetListCard()
        card.setObjectName("MapTargetListCard")
        card.setProperty("selected", "false")
        card.setProperty("tier", entry.priority_tier)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(
            f"QFrame#MapTargetListCard {{ border-left: 4px solid {accent}; }}"
        )
        card.clicked.connect(lambda item=entry: self._select_entry(item))
        card.double_clicked.connect(
            lambda target_id=entry.target_id: self.open_in_target_stack.emit(target_id)
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(6)
        title = QLabel(entry.title)
        title.setObjectName("MapTargetCardTitle")
        title.setWordWrap(True)
        badge = QLabel(_TIER_LABELS[entry.priority_tier])
        badge.setObjectName("MapTargetPriorityBadge")
        badge.setProperty("tier", entry.priority_tier)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(title, stretch=1)
        top.addWidget(badge)
        layout.addLayout(top)

        coords = QLabel(entry.coordinates_text)
        coords.setObjectName("MapTargetMutedLabel")
        layout.addWidget(coords)

        layout.addWidget(self._meta_row("Type", entry.target_type))
        layout.addWidget(
            self._meta_row("Detected", format_detected_ago(entry.detected_at))
        )
        return card

    @staticmethod
    def _meta_row(label: str, value: str) -> QWidget:
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

    def _select_entry(self, entry: MapTargetListEntry) -> None:
        self._selected_key = entry.key
        self._update_card_selection()
        coordinate_id = entry.coordinate_id or ""
        self.entry_selected.emit(entry.target_id, coordinate_id)

    def _update_card_selection(self) -> None:
        for key, widget in self._card_widgets.items():
            widget.setProperty("selected", "true" if key == self._selected_key else "false")
            widget.style().unpolish(widget)
            widget.style().polish(widget)
