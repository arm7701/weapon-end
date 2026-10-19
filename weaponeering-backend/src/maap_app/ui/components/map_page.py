from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QSplitter, QSizePolicy, QVBoxLayout, QWidget

from maap_app.ui.components.map_workspace import MapWorkspace
from maap_app.ui.panels.map_detail_sidebar import MapDetailSidebar


class MapPageWidget(QWidget):
    """Map view with a collapsible targets list sidebar."""

    EXPANDED_DETAIL_WIDTH = 320

    def __init__(
        self,
        detail_sidebar: MapDetailSidebar,
        map_workspace: MapWorkspace,
    ) -> None:
        super().__init__()
        self.detail_sidebar = detail_sidebar
        self.map_workspace = map_workspace

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(4)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(detail_sidebar)
        self.splitter.addWidget(map_workspace)

        detail_sidebar.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding,
        )
        map_workspace.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self._apply_splitter_sizes(detail_sidebar.is_expanded())

        layout.addWidget(self.splitter)

        detail_sidebar.expanded_changed.connect(self._on_detail_expanded)

    def resizeEvent(self, event: QResizeEvent) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_splitter_sizes(self.detail_sidebar.is_expanded())

    def _on_detail_expanded(self, expanded: bool) -> None:
        self._apply_splitter_sizes(expanded)

    def _apply_splitter_sizes(self, expanded: bool) -> None:
        total = max(self.splitter.width(), 900)
        if expanded:
            detail_w = self.EXPANDED_DETAIL_WIDTH
        else:
            detail_w = MapDetailSidebar.COLLAPSED_WIDTH
        self.splitter.setSizes([detail_w, max(total - detail_w, 400)])
