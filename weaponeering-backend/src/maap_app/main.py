from __future__ import annotations

import logging
import os
import sys

from PySide6.QtWidgets import QApplication

from maap_app.app import create_app_context
from maap_app.ui.styles import APP_STYLESHEET
from maap_app.ui.main_window import MainWindow


def _stabilize_webengine_gpu_process() -> None:
    """Reduce QtWebEngine GPU-process crashes on WebGL-heavy pages.

    Under Wayland, Chromium's GPU process (used by the Cesium WebGL map) can
    crash during heavy re-renders (e.g. the camera flyTo triggered by Run
    Detection), taking the whole app down. Disabling the GPU sandbox avoids
    this without disabling GPU acceleration entirely.
    """
    if "QTWEBENGINE_CHROMIUM_FLAGS" not in os.environ:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu-sandbox"


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    _stabilize_webengine_gpu_process()
    app = QApplication(sys.argv)
    app.setApplicationName("MAAP Wargame Training Simulation")
    app.setStyleSheet(APP_STYLESHEET)

    context = create_app_context()
    window = MainWindow(context)
    window.show()

    return app.exec()
