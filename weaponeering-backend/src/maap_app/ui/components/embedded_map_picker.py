from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget

_PICKER_HTML = Path(__file__).resolve().parents[1] / "map" / "assets" / "cesium_picker.html"


class _EmbeddedPickerBridge(QObject):
    coordinate_picked = Signal(float, float)

    @Slot(float, float)
    def pickCoord(self, lat: float, lng: float) -> None:
        self.coordinate_picked.emit(lat, lng)


class EmbeddedMapPickerWidget(QWidget):
    """Small Cesium map for picking coordinates inside the target form."""

    coordinate_picked = Signal(float, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("EmbeddedMapPicker")
        self._ready = False
        self._loaded = False
        self._pending_view: tuple[float, float, int] | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._view = QWebEngineView(self)
        self._view.setMinimumHeight(300)
        self._view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self._view)

        settings = self._view.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,
            True,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled,
            True,
        )

        self._bridge = _EmbeddedPickerBridge()
        self._bridge.coordinate_picked.connect(self.coordinate_picked.emit)
        channel = QWebChannel(self)
        channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(channel)
        self._view.page().setBackgroundColor(QColor("#0a1018"))
        self._view.loadFinished.connect(self._on_load_finished)
        self._view.page().titleChanged.connect(self._on_title_changed)

    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        self._view.load(QUrl.fromLocalFile(str(_PICKER_HTML)))

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            return
        self._ready = True
        if self._pending_view is not None:
            lat, lng, zoom = self._pending_view
            self._pending_view = None
            self.center_on(lat, lng, zoom=zoom)
        self.refresh_layout()

    def _on_title_changed(self, title: str) -> None:
        if not title.startswith("MAP_PICK|"):
            return
        parts = title.split("|")
        if len(parts) < 3:
            return
        try:
            lat = float(parts[1])
            lng = float(parts[2])
        except ValueError:
            return
        self.coordinate_picked.emit(lat, lng)

    def _run_js(self, script: str) -> None:
        if not self._ready:
            return
        self._view.page().runJavaScript(script)

    def center_on(self, lat: float, lng: float, *, zoom: int = 10) -> None:
        if not self._ready:
            self._pending_view = (lat, lng, zoom)
            return
        self._run_js(f"window.maapPicker.setView({lat}, {lng}, {zoom});")

    def refresh_layout(self) -> None:
        if not self._ready:
            return
        self._run_js("window.maapPicker.invalidateSize();")

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.ensure_loaded()
        QTimer.singleShot(0, self.refresh_layout)
        QTimer.singleShot(200, self.refresh_layout)
