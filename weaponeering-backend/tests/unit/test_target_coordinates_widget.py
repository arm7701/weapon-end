from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from maap_app.ui.panels.target_coordinates_widget import TargetCoordinatesWidget


def _app() -> QApplication:
    return QApplication.instance() or QApplication(sys.argv)


def _force_deferred_delete(obj) -> None:
    QCoreApplication.sendPostedEvents(obj, QEvent.Type.DeferredDelete)


def test_apply_map_coordinate_after_row_deletion_does_not_crash() -> None:
    _app()
    widget = TargetCoordinatesWidget()

    widget.apply_map_coordinate(1.0, 2.0)
    stale_row = widget._pending_pick_row
    assert stale_row is not None

    widget.clear_rows()
    _force_deferred_delete(stale_row)

    widget.apply_map_coordinate(3.0, 4.0)

    coords = widget.get_coordinates()
    assert len(coords) == 1
    assert coords[0].map_lat == 3.0
    assert coords[0].map_lng == 4.0


def test_apply_map_coordinate_after_set_coordinates_replaces_row_does_not_crash() -> None:
    _app()
    widget = TargetCoordinatesWidget()

    widget.apply_map_coordinate(1.0, 2.0)
    stale_row = widget._pending_pick_row
    assert stale_row is not None

    widget.set_coordinates([])
    _force_deferred_delete(stale_row)

    widget.apply_map_coordinate(5.0, 6.0)

    coords = widget.get_coordinates()
    assert len(coords) == 1
    assert coords[0].map_lat == 5.0
    assert coords[0].map_lng == 6.0
