from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

CHROME_LLM_MODES: tuple[tuple[str, str], ...] = (
    ("Local", "local_model"),
    ("OpenAI", "openai"),
    ("Gemini", "gemini"),
    ("Rule-based", "rule_based"),
)


class AppChrome(QWidget):
    workspace_tab_changed = Signal(str)
    llm_mode_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("AppChrome")
        self._syncing_llm = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        subnav = QWidget()
        subnav.setObjectName("SubNavBar")
        subnav.setFixedHeight(48)
        sn = QHBoxLayout(subnav)
        sn.setContentsMargins(12, 0, 12, 0)
        sn.setSpacing(8)

        logo = QLabel("⬡")
        logo.setStyleSheet("font-size: 20px; color: #60a5fa;")
        sn.addWidget(logo)

        brand = QWidget()
        bl = QVBoxLayout(brand)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)
        title = QLabel("MAAP Wargame")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Local Simulation Workspace")
        subtitle.setObjectName("AppSubtitle")
        bl.addWidget(title)
        bl.addWidget(subtitle)
        sn.addWidget(brand)

        divider = QWidget()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background: #1a2433;")
        sn.addWidget(divider)

        self._tab_group = QButtonGroup(self)
        self._tab_group.setExclusive(True)
        for index, (tab_id, label) in enumerate(
            (
                ("map", "Map"),
                ("target", "Target"),
                ("database", "Database"),
                ("intelligence", "AI Review"),
                ("settings", "Settings"),
            )
        ):
            btn = QPushButton(label)
            btn.setObjectName("SubNavTab")
            btn.setCheckable(True)
            btn.setProperty("active", tab_id == "map")
            if tab_id == "map":
                btn.setChecked(True)
            btn.clicked.connect(lambda _c=False, tid=tab_id: self._on_tab(tid))
            self._tab_group.addButton(btn, index)
            sn.addWidget(btn)

        sn.addStretch(1)

        llm_label = QLabel("LLM")
        llm_label.setObjectName("SubNavLlmLabel")
        sn.addWidget(llm_label)

        self._llm_combo = QComboBox()
        self._llm_combo.setObjectName("SubNavLlmCombo")
        self._llm_combo.setMaxVisibleItems(len(CHROME_LLM_MODES))
        for label, mode_id in CHROME_LLM_MODES:
            self._llm_combo.addItem(label)
            index = self._llm_combo.count() - 1
            self._llm_combo.setItemData(index, mode_id, Qt.ItemDataRole.UserRole)
        self._llm_combo.activated.connect(self._on_llm_mode_activated)
        sn.addWidget(self._llm_combo)

        settings = QPushButton("⚙")
        settings.setObjectName("IconButton")
        settings.setFixedSize(34, 34)
        settings.clicked.connect(lambda: self._on_tab("settings"))
        sn.addWidget(settings)

        root.addWidget(subnav)

    def set_llm_mode(self, mode: str) -> None:
        index = self._llm_combo.findData(mode, Qt.ItemDataRole.UserRole)
        if index < 0:
            fallback = {
                "sandboxed": "local_model",
                "disabled": "rule_based",
            }.get(mode, "local_model")
            index = self._llm_combo.findData(fallback, Qt.ItemDataRole.UserRole)
        self._syncing_llm = True
        try:
            if index >= 0:
                self._llm_combo.setCurrentIndex(index)
        finally:
            self._syncing_llm = False

    def _on_llm_mode_activated(self, index: int) -> None:
        if self._syncing_llm or index < 0:
            return
        mode = self._llm_combo.itemData(index, Qt.ItemDataRole.UserRole)
        if mode:
            self.llm_mode_changed.emit(str(mode))

    def activate_tab(self, tab_id: str) -> None:
        self._on_tab(tab_id)

    def _on_tab(self, tab_id: str) -> None:
        tab_labels = {
            "database": "Database",
            "map": "Map",
            "target": "Target",
            "intelligence": "AI Review",
            "settings": "Settings",
        }
        target = tab_labels.get(tab_id, "Map")
        for btn in self._tab_group.buttons():
            if btn.text() == "⚙":
                continue
            is_active = btn.text() == target
            btn.setChecked(is_active)
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.workspace_tab_changed.emit(tab_id)
