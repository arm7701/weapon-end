from __future__ import annotations

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget


class LeftWorkspace(QWidget):
    PANEL_TARGETS = 0
    PANEL_WEAPONEERING = 1
    PANEL_REVIEW = 2
    PANEL_EXPORT = 3

    def __init__(self, panels: list[QWidget]) -> None:
        super().__init__()
        self.setMinimumWidth(260)
        self.setMaximumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        for panel in panels:
            self.stack.addWidget(panel)
        layout.addWidget(self.stack)

    def show_panel(self, panel_id: str) -> None:
        mapping = {
            "targets": self.PANEL_TARGETS,
            "weaponeering": self.PANEL_WEAPONEERING,
            "review": self.PANEL_REVIEW,
            "export": self.PANEL_EXPORT,
        }
        index = mapping.get(panel_id, self.PANEL_TARGETS)
        self.stack.setCurrentIndex(index)
