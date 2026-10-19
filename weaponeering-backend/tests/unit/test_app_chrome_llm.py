from __future__ import annotations

import sys

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from maap_app.ui.components.app_chrome import CHROME_LLM_MODES, AppChrome


@pytest.fixture
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication(sys.argv)


def test_chrome_llm_combo_exposes_openai_and_gemini(qt_app: QApplication) -> None:
    chrome = AppChrome()
    combo = chrome._llm_combo
    labels = [combo.itemText(index) for index in range(combo.count())]
    modes = [
        combo.itemData(index, Qt.ItemDataRole.UserRole) for index in range(combo.count())
    ]
    assert labels == [label for label, _mode in CHROME_LLM_MODES]
    assert modes == [mode for _label, mode in CHROME_LLM_MODES]
    assert combo.findData("openai", Qt.ItemDataRole.UserRole) >= 0
    assert combo.findData("gemini", Qt.ItemDataRole.UserRole) >= 0


def test_set_llm_mode_keeps_openai_selection(qt_app: QApplication) -> None:
    chrome = AppChrome()
    chrome.set_llm_mode("openai")
    index = chrome._llm_combo.currentIndex()
    mode = chrome._llm_combo.itemData(index, Qt.ItemDataRole.UserRole)
    assert mode == "openai"
