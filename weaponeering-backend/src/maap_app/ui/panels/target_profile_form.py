from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.target.constants import (
    DATA_SOURCE_OPTIONS,
    DESIRED_MODEL_RESULTS,
    MATERIAL_CLASS_OPTIONS,
    TARGET_TYPES,
    subtypes_for_target_type,
)
from maap_app.modules.target.models import TargetCard, TargetCardDetail, TargetCoordinate
from maap_app.modules.target.profile_fields import TargetProfileFields
from maap_app.modules.target.random_generator import RandomTargetSuggestion
from maap_app.modules.target.schemas import TargetCoordinateInput
from maap_app.ui.panels.target_coordinates_widget import TargetCoordinatesWidget
from maap_app.ui.panels.wing_form_widgets import (
    _FloatLineEdit,
    _float_spin,
    _form_card,
    _stacked_field,
)


def _optional_float_spin(maximum: float = 999999.0) -> _FloatLineEdit:
    spin = _float_spin(0.0, maximum)
    spin.setSpecialValueText("—")
    spin.setValue(0.0)
    return spin


def _text_field(placeholder: str = "") -> QLineEdit:
    field = QLineEdit()
    if placeholder:
        field.setPlaceholderText(placeholder)
    return field


def _coord_field() -> QLineEdit:
    field = QLineEdit()
    field.setPlaceholderText("—")
    return field


def _hint_note(text: str) -> QLabel:
    note = QLabel(text)
    note.setObjectName("FormSectionSubtitle")
    note.setWordWrap(True)
    note.setStyleSheet("color: #d4a017; font-size: 10px;")
    return note


class TargetProfileFormWidget(QWidget):
    map_search_requested = Signal(float, float)

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        basic_card, basic_layout = _form_card(
            "ข้อมูลพื้นฐาน",
            "ชื่อเป้าหมาย ลำดับความสำคัญ และระดับความซับซ้อน",
        )
        self.label_input = _text_field("TGT-001")
        self.priority_input = QSpinBox()
        self.priority_input.setRange(1, 5)
        self.priority_input.setValue(3)
        self.complexity_input = QSpinBox()
        self.complexity_input.setRange(1, 5)
        self.complexity_input.setValue(3)
        basic_layout.addWidget(_stacked_field("ชื่อเป้าหมาย", self.label_input))
        score_row = QWidget()
        score_layout = QHBoxLayout(score_row)
        score_layout.setContentsMargins(0, 0, 0, 0)
        score_layout.setSpacing(8)
        score_layout.addWidget(_stacked_field("Priority (1-5)", self.priority_input), 1)
        score_layout.addWidget(_stacked_field("Complexity (1-5)", self.complexity_input), 1)
        basic_layout.addWidget(score_row)
        root.addWidget(basic_card)

        type_card, type_layout = _form_card(
            "ประเภทและรายละเอียดเป้าหมาย",
            "วัตถุหลัก · ประเภทย่อย · วัสดุ · บันทึกเพิ่มเติม",
        )
        self.target_type = QComboBox()
        self.target_type.addItems(list(TARGET_TYPES))
        self.target_type.currentTextChanged.connect(self._on_target_type_changed)
        self.target_subtype = QComboBox()
        self.material_class = QComboBox()
        self.material_class.addItems(list(MATERIAL_CLASS_OPTIONS))
        self.target_description = QTextEdit()
        self.target_description.setPlaceholderText(
            "หมายเหตุ สมมติฐาน แหล่งอ้างอิง หรือจุดที่ต้องตรวจสอบเชิงโครงสร้าง"
        )
        self.target_description.setMaximumHeight(72)
        type_layout.addWidget(_stacked_field("ประเภทเป้าหมาย (วัตถุหลัก)", self.target_type))
        type_layout.addWidget(_stacked_field("ประเภทย่อย", self.target_subtype))
        type_layout.addWidget(_stacked_field("วัสดุหลัก", self.material_class))
        type_layout.addWidget(_stacked_field("รายละเอียดเป้าหมาย", self.target_description))
        self._populate_subtypes(self.target_type.currentText())
        root.addWidget(type_card)

        size_card, size_layout = _form_card(
            "ขนาดโดยประมาณ",
            "มิติและจำนวนชั้นของเป้าหมาย (เว้นว่างได้)",
        )
        self.floor_count = _text_field("UNK")
        self.width_m = _optional_float_spin()
        self.length_m = _optional_float_spin()
        self.height_m = _optional_float_spin()
        size_layout.addWidget(_stacked_field("จำนวนชั้น", self.floor_count))
        dim_row = QWidget()
        dim_grid = QGridLayout(dim_row)
        dim_grid.setContentsMargins(0, 0, 0, 0)
        dim_grid.setHorizontalSpacing(8)
        dim_grid.setVerticalSpacing(0)
        dim_grid.addWidget(_stacked_field("Width (m)", self.width_m), 0, 0)
        dim_grid.addWidget(_stacked_field("Length (m)", self.length_m), 0, 1)
        dim_grid.addWidget(_stacked_field("Height (m)", self.height_m), 1, 0, 1, 2)
        size_layout.addWidget(dim_row)
        root.addWidget(size_card)

        model_card, model_layout = _form_card(
            "ผลที่ต้องการจากแบบจำลอง",
            "กำหนดผลลัพธ์ที่ต้องการจาก reference model",
        )
        self.desired_model_result = QComboBox()
        self.desired_model_result.addItems(list(DESIRED_MODEL_RESULTS))
        model_layout.addWidget(_stacked_field("ผลลัพธ์", self.desired_model_result))
        model_layout.addWidget(
            _hint_note(
                "1) กรอกค่า Pk เป้าหมายเพื่อให้ระบบเลือกรายการตัวเลือก "
                "2) เลือกรายการตัวเลือกเพื่อให้ระบบคำนวณและแสดงค่า Pk"
            )
        )
        root.addWidget(model_card)

        coord_card, coord_layout = _form_card(
            "พิกัดเป้าหมาย",
            "กด「พิกัด」เพื่อเปิดแผนที่ใน Dialog · คลิกเพื่อใส่ Lat/Lng",
        )
        self.coordinates_widget = TargetCoordinatesWidget()
        self.coordinates_widget.map_search_requested.connect(self.map_search_requested.emit)
        coord_layout.addWidget(self.coordinates_widget)
        self.err_input = _optional_float_spin(50000.0)
        self.err_input.setDecimals(1)
        coord_layout.addWidget(_stacked_field("ความคลาดเคลื่อน (m)", self.err_input))
        root.addWidget(coord_card)

        source_card, source_layout = _form_card(
            "แหล่งที่มาของข้อมูล",
            "ระบุแหล่งข้อมูลที่ใช้ในการพัฒนาเป้าหมาย",
        )
        self.data_source = QComboBox()
        for label, value in DATA_SOURCE_OPTIONS:
            self.data_source.addItem(label, value)
        source_layout.addWidget(_stacked_field("แหล่งข้อมูล", self.data_source))
        root.addWidget(source_card)

        ref_card, ref_layout = _form_card(
            "ค่าพารามิเตอร์อ้างอิง",
            "CEP, Pk, resistance และ metadata ของ reference model",
        )
        self.cep = _optional_float_spin()
        self.target_pk = _optional_float_spin()
        self.reference_pk = _optional_float_spin()
        self.resistance = _text_field("Resistance")
        self.capacity = _text_field("Capacity")
        self.damage_fit = _text_field("Damage Fit")
        self.model_version = _text_field("Model version")
        self.cep.setToolTip("CEP")
        self.target_pk.setToolTip("Pk เป้าหมาย")
        self.reference_pk.setToolTip("Pk อ้างอิง")
        pk_row = QWidget()
        pk_layout = QHBoxLayout(pk_row)
        pk_layout.setContentsMargins(0, 0, 0, 0)
        pk_layout.setSpacing(8)
        pk_layout.addWidget(_stacked_field("CEP", self.cep), 1)
        pk_layout.addWidget(_stacked_field("Pk เป้าหมาย", self.target_pk), 1)
        ref_layout.addWidget(pk_row)
        ref_layout.addWidget(_stacked_field("Pk อ้างอิง", self.reference_pk))
        ref_layout.addWidget(_stacked_field("Resistance", self.resistance))
        ref_layout.addWidget(_stacked_field("Capacity", self.capacity))
        ref_layout.addWidget(_stacked_field("Damage Fit", self.damage_fit))
        ref_layout.addWidget(_stacked_field("Model version", self.model_version))
        root.addWidget(ref_card)

        root.addStretch(1)

    def load_detail(self, detail: TargetCardDetail) -> None:
        self.load_card(
            detail.card,
            detail.map_lat,
            detail.map_lng,
            detail.coordinates,
        )

    def load_card(
        self,
        card: TargetCard,
        map_lat: float | None = None,
        map_lng: float | None = None,
        coordinates: list[TargetCoordinate] | None = None,
    ) -> None:
        self.label_input.setText(card.label)
        self.priority_input.setValue(card.priority_score)
        self.complexity_input.setValue(card.complexity_score)
        self._set_combo_text(self.target_type, card.target_type)
        self._populate_subtypes(card.target_type, preserve=card.target_subtype)
        self._set_combo_text(self.material_class, card.material_class)
        self.target_description.setPlainText(card.target_description or "")
        self.floor_count.setText(card.floor_count or "UNK")
        self._set_optional_spin(self.width_m, card.width_m)
        self._set_optional_spin(self.length_m, card.length_m)
        self._set_optional_spin(self.height_m, card.height_m)
        self._set_combo_text(self.desired_model_result, card.desired_model_result)
        if coordinates:
            self.coordinates_widget.set_coordinates(coordinates)
        elif map_lat is not None and map_lng is not None:
            self.coordinates_widget.set_coordinates(
                [
                    TargetCoordinate(
                        id="form-primary",
                        target_card_id=card.id,
                        label="P1",
                        map_lat=map_lat,
                        map_lng=map_lng,
                        sort_order=0,
                        is_primary=True,
                    )
                ]
            )
        else:
            self.coordinates_widget.clear_rows()
        self._set_optional_spin(self.err_input, card.coordinate_error_m)
        self._set_combo_data(self.data_source, card.data_source)
        self._set_optional_spin(self.cep, card.cep)
        self._set_optional_spin(self.target_pk, card.target_pk)
        self._set_optional_spin(self.reference_pk, card.reference_pk)
        self.resistance.setText(card.resistance)
        self.capacity.setText(card.capacity)
        self.damage_fit.setText(card.damage_fit)
        self.model_version.setText(card.model_version)

    def clear_form(self) -> None:
        self.label_input.clear()
        self.priority_input.setValue(3)
        self.complexity_input.setValue(3)
        self.target_type.setCurrentIndex(0)
        self._populate_subtypes(self.target_type.currentText())
        self.material_class.setCurrentIndex(0)
        self.target_description.clear()
        self.floor_count.setText("UNK")
        for spin in (
            self.width_m,
            self.length_m,
            self.height_m,
            self.err_input,
            self.cep,
            self.target_pk,
            self.reference_pk,
        ):
            spin.setValue(0.0)
        self.desired_model_result.setCurrentIndex(0)
        self.coordinates_widget.clear_rows()
        self.coordinates_widget.hide_embedded_map()
        self.data_source.setCurrentIndex(0)
        for field in (self.resistance, self.capacity, self.damage_fit, self.model_version):
            field.clear()

    def apply_random_suggestion(self, suggestion: RandomTargetSuggestion) -> None:
        self.label_input.setText(suggestion.label)
        self.priority_input.setValue(suggestion.priority_score)
        self.complexity_input.setValue(suggestion.complexity_score)
        profile = suggestion.profile
        self._set_combo_text(self.target_type, profile.target_type)
        self._populate_subtypes(profile.target_type, preserve=profile.target_subtype)
        self._set_combo_text(self.material_class, profile.material_class)
        self.target_description.setPlainText(profile.target_description)
        self.floor_count.setText(profile.floor_count)
        self._set_optional_spin(self.width_m, profile.width_m)
        self._set_optional_spin(self.length_m, profile.length_m)
        self._set_optional_spin(self.height_m, profile.height_m)
        self._set_combo_text(self.desired_model_result, profile.desired_model_result)
        self.coordinates_widget.apply_map_coordinate(suggestion.map_lat, suggestion.map_lng)

    def values(
        self,
    ) -> tuple[str, int, int, TargetProfileFields, list[TargetCoordinateInput]]:
        return (
            self.label_input.text().strip(),
            self.priority_input.value(),
            self.complexity_input.value(),
            TargetProfileFields(
                target_type=self.target_type.currentText(),
                target_subtype=self.target_subtype.currentText(),
                material_class=self.material_class.currentText(),
                target_description=self.target_description.toPlainText().strip(),
                floor_count=self.floor_count.text().strip(),
                width_m=self._optional_value(self.width_m),
                length_m=self._optional_value(self.length_m),
                height_m=self._optional_value(self.height_m),
                desired_model_result=self.desired_model_result.currentText(),
                coordinate_error_m=self._optional_value(self.err_input),
                data_source=self.data_source.currentData(),
                cep=self._optional_value(self.cep),
                target_pk=self._optional_value(self.target_pk),
                reference_pk=self._optional_value(self.reference_pk),
                resistance=self.resistance.text().strip(),
                capacity=self.capacity.text().strip(),
                damage_fit=self.damage_fit.text().strip(),
                model_version=self.model_version.text().strip(),
            ),
            self.coordinates_widget.get_coordinates(),
        )

    def set_coordinates(self, lat: float, lng: float) -> None:
        self.coordinates_widget.apply_map_coordinate(lat, lng)

    def primary_coordinate(self) -> tuple[float, float] | None:
        return self.coordinates_widget.primary_coordinate()

    def _on_target_type_changed(self, target_type: str) -> None:
        self._populate_subtypes(target_type)

    def _populate_subtypes(
        self,
        target_type: str,
        *,
        preserve: str | None = None,
    ) -> None:
        self.target_subtype.blockSignals(True)
        self.target_subtype.clear()
        options = subtypes_for_target_type(target_type)
        self.target_subtype.addItems(options)
        selected = preserve or options[0]
        index = self.target_subtype.findText(selected)
        if index < 0 and preserve:
            self.target_subtype.insertItem(0, preserve)
            index = 0
        self.target_subtype.setCurrentIndex(index if index >= 0 else 0)
        self.target_subtype.blockSignals(False)

    @staticmethod
    def _set_combo_text(combo: QComboBox, value: str) -> None:
        idx = combo.findText(value)
        combo.setCurrentIndex(idx if idx >= 0 else 0)

    @staticmethod
    def _set_combo_data(combo: QComboBox, value: str) -> None:
        idx = combo.findData(value)
        combo.setCurrentIndex(idx if idx >= 0 else 0)

    @staticmethod
    def _optional_value(spin: _FloatLineEdit) -> float | None:
        return None if spin.value() == 0.0 else spin.value()

    @staticmethod
    def _set_optional_spin(spin: _FloatLineEdit, value: float | None) -> None:
        spin.setValue(0.0 if value is None else value)

    @staticmethod
    def _coord_value(field: QLineEdit) -> float | None:
        text = field.text().strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def _set_coord(field: QLineEdit, value: float | None) -> None:
        field.setText("" if value is None else f"{value:.5f}")
