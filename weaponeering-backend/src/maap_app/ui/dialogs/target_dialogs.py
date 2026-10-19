from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from maap_app.modules.target.constants import TARGET_TYPES


class QuickCreateTargetDialog(QDialog):
    def __init__(
        self,
        *,
        lat: float,
        lng: float,
        default_label: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("สร้างเป้าหมายจากแผนที่")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.coords_label = QLabel(f"{lat:.5f}, {lng:.5f}")
        self.coords_label.setStyleSheet("color: #94a3b8;")
        form.addRow("พิกัด", self.coords_label)

        self.label_input = QLineEdit(default_label)
        self.label_input.setPlaceholderText("TGT-001")
        form.addRow("ชื่อเป้าหมาย", self.label_input)

        self.target_type = QComboBox()
        self.target_type.addItems(list(TARGET_TYPES))
        form.addRow("ประเภทเป้าหมาย", self.target_type)

        self.priority_input = QSpinBox()
        self.priority_input.setRange(1, 5)
        self.priority_input.setValue(3)
        form.addRow("ลำดับความสำคัญ (1-5)", self.priority_input)

        layout.addLayout(form)
        hint = QLabel("กรอกข้อมูลพื้นฐานเท่านั้น · แก้ไขรายละเอียดเพิ่มเติมได้ในหน้า Target")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #6b7f96; font-size: 11px;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {
            "label": self.label_input.text().strip(),
            "target_type": self.target_type.currentText(),
            "priority_score": self.priority_input.value(),
        }


class CreateTargetCardDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Target Object")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("TGT-001")
        form.addRow("Label", self.label_input)

        self.priority_input = QSpinBox()
        self.priority_input.setRange(1, 5)
        self.priority_input.setValue(3)
        form.addRow("Priority (1-5)", self.priority_input)

        self.complexity_input = QSpinBox()
        self.complexity_input.setRange(1, 5)
        self.complexity_input.setValue(3)
        form.addRow("Complexity (1-5)", self.complexity_input)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {
            "label": self.label_input.text().strip(),
            "priority_score": self.priority_input.value(),
            "complexity_score": self.complexity_input.value(),
        }


class CreateRecognitionDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Recognition Result")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.source_input = QComboBox()
        self.source_input.addItems(["manual", "import", "ai"])
        form.addRow("Source type", self.source_input)

        self.summary_input = QTextEdit()
        self.summary_input.setPlaceholderText("Synthetic recognition summary...")
        self.summary_input.setMaximumHeight(100)
        form.addRow("Summary", self.summary_input)

        self.confidence_input = QSpinBox()
        self.confidence_input.setRange(1, 100)
        self.confidence_input.setValue(65)
        form.addRow("Confidence (1-100)", self.confidence_input)

        self.missing_input = QTextEdit()
        self.missing_input.setPlaceholderText("One missing-data note per line")
        self.missing_input.setMaximumHeight(80)
        form.addRow("Missing data", self.missing_input)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        missing = [
            line.strip()
            for line in self.missing_input.toPlainText().splitlines()
            if line.strip()
        ]
        return {
            "source_type": self.source_input.currentText(),
            "recognition_summary": self.summary_input.toPlainText().strip(),
            "recognition_confidence_score": self.confidence_input.value(),
            "missing_data_notes": missing,
        }
