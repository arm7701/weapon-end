from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QStackedWidget, QSizePolicy, QVBoxLayout, QWidget


class WorkspaceStack(QWidget):
    """Switches between Database, Map, AI Review, AAR & Export, and Settings views."""

    def __init__(
        self,
        map_page: QWidget,
        target_page: QWidget,
        database_page: QWidget,
        intelligence_page: QWidget,
        reports_page: QWidget,
        settings_page: QWidget,
    ) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.stack.addWidget(map_page)
        self.stack.addWidget(target_page)
        self.stack.addWidget(database_page)
        self.stack.addWidget(intelligence_page)
        self.stack.addWidget(reports_page)
        self.stack.addWidget(settings_page)
        layout.addWidget(self.stack, stretch=1)

    def show_tab(self, tab_id: str) -> None:
        tabs = {
            "map": 0,
            "target": 1,
            "database": 2,
            "workspace": 2,
            "intelligence": 3,
            "reports": 4,
            "settings": 5,
        }
        self.stack.setCurrentIndex(tabs.get(tab_id, 0))


def build_split_page(
    left: QWidget | None,
    center: QWidget | None,
    right: QWidget | None,
) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setHandleWidth(6)
    splitter.setChildrenCollapsible(False)

    widgets: list[QWidget] = []
    if left is not None:
        left.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        splitter.addWidget(left)
        widgets.append(left)
    if center is not None:
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter.addWidget(center)
        widgets.append(center)
    if right is not None:
        right.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        splitter.addWidget(right)
        widgets.append(right)

    count = len(widgets)
    if count == 3:
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)
    elif count == 2:
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
    elif count == 1:
        splitter.setStretchFactor(0, 1)

    layout.addWidget(splitter)
    return page
