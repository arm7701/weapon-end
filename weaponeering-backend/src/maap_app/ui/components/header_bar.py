from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HeaderBar(QWidget):
    fit_to_scenario_requested = Signal()
    new_scenario_requested = Signal()
    search_changed = Signal(str)
    scenario_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("HeaderBar")
        self.setFixedHeight(58)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        logo = QLabel("⬡")
        logo.setStyleSheet("font-size: 22px; color: #60a5fa; padding-right: 4px;")
        layout.addWidget(logo)

        brand = QWidget()
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(0)
        title = QLabel("MAAP Wargame")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Local Simulation Workspace")
        subtitle.setObjectName("AppSubtitle")
        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        layout.addWidget(brand)

        layout.addSpacing(8)

        new_scenario = QPushButton("+ New Scenario")
        new_scenario.setObjectName("PrimaryButton")
        new_scenario.clicked.connect(self.new_scenario_requested.emit)
        layout.addWidget(new_scenario)

        draw_route = QPushButton("Draw Route")
        draw_route.setObjectName("SecondaryButton")
        draw_route.setEnabled(False)
        layout.addWidget(draw_route)

        fit_btn = QPushButton("Fit to Scenario")
        fit_btn.setObjectName("SecondaryButton")
        fit_btn.clicked.connect(self.fit_to_scenario_requested.emit)
        layout.addWidget(fit_btn)

        layout.addStretch(1)

        scenario_label = QLabel("Scenario")
        scenario_label.setStyleSheet("color: #6b7f96; font-size: 11px; font-weight: 600;")
        layout.addWidget(scenario_label)

        self.scenario_combo = QComboBox()
        self.scenario_combo.setObjectName("ScenarioCombo")
        self.scenario_combo.currentIndexChanged.connect(self._on_scenario_changed)
        layout.addWidget(self.scenario_combo)

        self.search = QLineEdit()
        self.search.setObjectName("SearchInput")
        self.search.setPlaceholderText("Search workspace...")
        self.search.setFixedWidth(220)
        self.search.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search)

        status = QLabel("● All Systems Ready")
        status.setObjectName("StatusPill")
        layout.addWidget(status)

        settings = QPushButton("⚙")
        settings.setObjectName("IconButton")
        settings.setFixedSize(34, 34)
        layout.addWidget(settings)

        avatar = QLabel("OP")
        avatar.setObjectName("AvatarBadge")
        layout.addWidget(avatar)

    def set_scenarios(self, scenarios: list[tuple[str, str]]) -> None:
        self.scenario_combo.blockSignals(True)
        self.scenario_combo.clear()
        for scenario_id, name in scenarios:
            self.scenario_combo.addItem(name, scenario_id)
        self.scenario_combo.blockSignals(False)

    def current_scenario_id(self) -> str | None:
        data = self.scenario_combo.currentData()
        return str(data) if data else None

    def _on_scenario_changed(self) -> None:
        scenario_id = self.current_scenario_id()
        if scenario_id:
            self.scenario_changed.emit(scenario_id)
