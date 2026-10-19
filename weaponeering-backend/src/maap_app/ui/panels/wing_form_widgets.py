from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

_INVALID_STYLE = "border: 1px solid #ef4444;"
_VALID_STYLE = ""


class _FloatLineEdit(QLineEdit):
    """QLineEdit that behaves like QDoubleSpinBox — supports copy/paste, exposes .value()/.setValue()."""

    def __init__(self, value: float, minimum: float, maximum: float, decimals: int) -> None:
        super().__init__()
        self._minimum = minimum
        self._maximum = maximum
        self._decimals = decimals
        self._special_value_text: str = ""
        self.setValue(value)
        self.textChanged.connect(self._on_text_changed)

    def setSpecialValueText(self, text: str) -> None:
        """Show this text when value equals the minimum (mirrors QAbstractSpinBox API)."""
        self._special_value_text = text
        if self.value() == self._minimum:
            self.setText(text)

    def setDecimals(self, decimals: int) -> None:  # noqa: N802 — matches Qt API
        self._decimals = decimals
        self.setValue(self.value())

    def setSuffix(self, suffix: str) -> None:  # noqa: N802 — matches Qt API
        pass

    def _on_text_changed(self) -> None:
        text = self.text().strip()
        if self._special_value_text and text == self._special_value_text:
            self.setStyleSheet(_VALID_STYLE)
            return
        if not text or text in ("-", "."):
            self.setStyleSheet(_VALID_STYLE)
            return
        try:
            v = float(text)
            self.setStyleSheet(_VALID_STYLE if self._minimum <= v <= self._maximum else _INVALID_STYLE)
        except ValueError:
            self.setStyleSheet(_INVALID_STYLE)

    def value(self) -> float:
        text = self.text().strip()
        if self._special_value_text and text == self._special_value_text:
            return float(self._minimum)
        try:
            v = float(text)
            return max(self._minimum, min(self._maximum, v))
        except ValueError:
            return float(self._minimum)

    def setValue(self, v: float) -> None:
        clamped = max(self._minimum, min(self._maximum, v))
        if self._special_value_text and clamped == self._minimum:
            self.setText(self._special_value_text)
        else:
            self.setText(f"{clamped:.{self._decimals}f}")


class _IntLineEdit(QLineEdit):
    """QLineEdit that behaves like QSpinBox — supports copy/paste, exposes .value()/.setValue()."""

    def __init__(self, value: int, minimum: int, maximum: int) -> None:
        super().__init__()
        self._minimum = minimum
        self._maximum = maximum
        self._special_value_text: str = ""
        self.setValue(value)
        self.textChanged.connect(self._on_text_changed)

    def setSpecialValueText(self, text: str) -> None:
        """Show this text when value equals the minimum (mirrors QAbstractSpinBox API)."""
        self._special_value_text = text
        if self.value() == self._minimum:
            self.setText(text)

    def setSuffix(self, suffix: str) -> None:  # noqa: N802 — matches Qt API
        pass

    def _on_text_changed(self) -> None:
        text = self.text().strip()
        if self._special_value_text and text == self._special_value_text:
            self.setStyleSheet(_VALID_STYLE)
            return
        if not text:
            self.setStyleSheet(_VALID_STYLE)
            return
        try:
            v = int(text)
            self.setStyleSheet(_VALID_STYLE if self._minimum <= v <= self._maximum else _INVALID_STYLE)
        except ValueError:
            self.setStyleSheet(_INVALID_STYLE)

    def value(self) -> int:
        text = self.text().strip()
        if self._special_value_text and text == self._special_value_text:
            return self._minimum
        try:
            v = int(text)
            return max(self._minimum, min(self._maximum, v))
        except ValueError:
            return self._minimum

    def setValue(self, v: int) -> None:
        clamped = max(self._minimum, min(self._maximum, int(round(v))))
        if self._special_value_text and clamped == self._minimum:
            self.setText(self._special_value_text)
        else:
            self.setText(str(clamped))


def _ready_combo() -> QComboBox:
    combo = QComboBox()
    combo.addItem("พร้อมปฏิบัติภารกิจ", "ready")
    combo.addItem("ไม่พร้อมปฏิบัติภารกิจ", "not_ready")
    return combo


def _set_ready(combo: QComboBox, status: str) -> None:
    index = combo.findData(status)
    combo.setCurrentIndex(index if index >= 0 else 1)


def _coord_spin(value: float = 0.0) -> _FloatLineEdit:
    return _FloatLineEdit(value, minimum=-180.0, maximum=180.0, decimals=5)


def _float_spin(value: float = 0.0, maximum: float = 999999.0) -> _FloatLineEdit:
    return _FloatLineEdit(value, minimum=0.0, maximum=maximum, decimals=2)


def _int_spin(value: int = 0, maximum: int = 999999) -> _IntLineEdit:
    return _IntLineEdit(value, minimum=0, maximum=maximum)


def _section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("FormSectionTitle")
    return label


def _form_card(title: str, subtitle: str = "") -> tuple[QWidget, QVBoxLayout]:
    card = QWidget()
    card.setObjectName("FormCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)
    layout.addWidget(_section_title(title))
    if subtitle:
        sub = QLabel(subtitle)
        sub.setObjectName("FormSectionSubtitle")
        sub.setWordWrap(True)
        layout.addWidget(sub)
    return card, layout


def _form_card_form(title: str, subtitle: str = "") -> tuple[QWidget, QFormLayout]:
    card, layout = _form_card(title, subtitle)
    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
    form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
    form.setHorizontalSpacing(12)
    form.setVerticalSpacing(8)
    layout.addLayout(form)
    return card, form


def _stacked_field(label: str, widget: QWidget) -> QWidget:
    row = QWidget()
    row_layout = QVBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(4)
    lbl = QLabel(label)
    lbl.setObjectName("FormFieldLabel")
    row_layout.addWidget(lbl)
    row_layout.addWidget(widget)
    return row


def _field_row(label: str, widget: QWidget) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    lbl = QLabel(label)
    lbl.setObjectName("FormFieldLabel")
    lbl.setFixedWidth(148)
    layout.addWidget(lbl)
    layout.addWidget(widget, 1)
    return row


def _action_row(on_save, on_delete, on_clear) -> QHBoxLayout:
    actions = QHBoxLayout()
    save_btn = QPushButton("บันทึก")
    save_btn.setObjectName("PrimaryButton")
    delete_btn = QPushButton("ลบ")
    delete_btn.setObjectName("SecondaryButton")
    clear_btn = QPushButton("ล้างฟอร์ม")
    clear_btn.setObjectName("GhostButton")
    delete_btn.setEnabled(False)
    save_btn.clicked.connect(on_save)
    delete_btn.clicked.connect(on_delete)
    clear_btn.clicked.connect(on_clear)
    actions.addWidget(save_btn)
    actions.addWidget(delete_btn)
    actions.addWidget(clear_btn)
    actions.addStretch(1)
    actions._delete_btn = delete_btn  # type: ignore[attr-defined]
    return actions


def _table(columns: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(True)
    table.setMinimumHeight(100)
    table.setShowGrid(True)

    # Columns: interactive resize (user can drag), last column fills remaining space
    h = table.horizontalHeader()
    h.setStretchLastSection(True)
    h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    h.setMinimumSectionSize(50)
    h.setDefaultSectionSize(120)

    # Rows: auto-height to content, minimum 28px, no row numbers
    v = table.verticalHeader()
    v.setVisible(False)
    v.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    v.setMinimumSectionSize(28)

    return table
