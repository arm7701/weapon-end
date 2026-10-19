from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.target.schemas import (
    CreateTargetCardRequest,
    SaveTargetCoordinatesRequest,
    UpdateTargetCardRequest,
)
from maap_app.modules.target.random_generator import generate_random_target
from maap_app.modules.target.service import TargetService
from maap_app.ui.panels.target_profile_form import TargetProfileFormWidget


class TargetFormPanel(QWidget):
    """Inline target profile editor (replaces Object Detection column + dialog)."""

    map_search_requested = Signal(float, float)
    target_saved = Signal(str)
    target_archived = Signal(str)
    targets_changed = Signal()

    def __init__(self, target_service: TargetService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.target_service = target_service
        self._scenario_id: str | None = None
        self._target_id: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.mode_label = QLabel("เลือก Target จากรายการ หรือกด + เพิ่มเป้าหมาย")
        self.mode_label.setObjectName("FormSectionSubtitle")
        self.mode_label.setWordWrap(True)
        root.addWidget(self.mode_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.profile_form = TargetProfileFormWidget()
        self.profile_form.map_search_requested.connect(self.map_search_requested.emit)
        scroll.setWidget(self.profile_form)
        root.addWidget(scroll, stretch=1)

        self._map_picker_host = QWidget()
        self._map_picker_host.setObjectName("EmbeddedMapPickerHost")
        self._map_picker_host.setVisible(False)
        map_host_layout = QVBoxLayout(self._map_picker_host)
        map_host_layout.setContentsMargins(0, 0, 0, 0)
        map_host_layout.setSpacing(0)
        root.addWidget(self._map_picker_host)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.save_btn = QPushButton("บันทึก")
        self.save_btn.setObjectName("PrimaryButton")
        self.save_btn.clicked.connect(self._on_save)
        self.delete_btn = QPushButton("ลบ")
        self.delete_btn.setObjectName("SecondaryButton")
        self.delete_btn.setVisible(False)
        self.delete_btn.clicked.connect(self._on_delete)
        self.reset_btn = QPushButton("รีเซ็ต")
        self.reset_btn.setObjectName("GhostButton")
        self.reset_btn.clicked.connect(self._on_reset)
        actions.addWidget(self.save_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch(1)
        actions.addWidget(self.reset_btn)
        root.addLayout(actions)

        self._mount_coordinate_picker()

    def _mount_coordinate_picker(self) -> None:
        coords = self.profile_form.coordinates_widget
        picker = coords.take_map_picker()
        host_layout = self._map_picker_host.layout()
        assert host_layout is not None
        host_layout.addWidget(picker)
        coords.map_picker_visibility_changed.connect(self._sync_map_picker_host)

    def _sync_map_picker_host(self, visible: bool) -> None:
        self._map_picker_host.setVisible(visible)
        if not visible:
            return
        coords = self.profile_form.coordinates_widget
        coords.refresh_map_picker()
        picker = coords.take_map_picker()
        picker.setVisible(True)
        picker.setFocus(Qt.FocusReason.OtherFocusReason)

    def set_scenario(self, scenario_id: str | None) -> None:
        self._scenario_id = scenario_id
        self._target_id = None
        self.begin_create()

    def begin_create(self) -> None:
        self._target_id = None
        self.profile_form.clear_form()
        self.profile_form.coordinates_widget.hide_embedded_map()
        self._set_mode("create")

    def begin_create_random(self) -> None:
        self.begin_create()
        existing_count = 0
        if self._scenario_id:
            existing_count = len(self.target_service.list_target_cards(self._scenario_id))
        suggestion = generate_random_target(existing_count)
        self.profile_form.apply_random_suggestion(suggestion)

    def load_target(self, target_id: str) -> None:
        detail = self.target_service.get_target_detail(target_id)
        if detail is None:
            return
        self._target_id = target_id
        self.profile_form.load_detail(detail)
        self.profile_form.coordinates_widget.hide_embedded_map()
        self._set_mode("edit", label=detail.card.label)

    def set_coordinates(self, lat: float, lng: float) -> None:
        self.profile_form.set_coordinates(lat, lng)

    def _set_mode(self, mode: str, *, label: str = "") -> None:
        is_edit = mode == "edit"
        self.delete_btn.setVisible(is_edit)
        if is_edit and label:
            self.mode_label.setText(f"แก้ไขเป้าหมาย — {label}")
        elif is_edit:
            self.mode_label.setText("แก้ไขเป้าหมาย")
        else:
            self.mode_label.setText("เพิ่มเป้าหมายใหม่")

    def _on_reset(self) -> None:
        if self._target_id:
            self.load_target(self._target_id)
            return
        self.begin_create()

    def _on_delete(self) -> None:
        if not self._target_id:
            return
        answer = QMessageBox.question(
            self,
            "ลบเป้าหมาย",
            "ลบเป้าหมายนี้ถาวร? ข้อมูลที่เกี่ยวข้องจะถูกลบทั้งหมด",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.target_service.delete_target_card(self._target_id)
        except ValueError as exc:
            QMessageBox.warning(self, "ลบไม่สำเร็จ", str(exc))
            return
        deleted_id = self._target_id
        self._target_id = None
        self.begin_create()
        self.targets_changed.emit()
        self.target_saved.emit(deleted_id)

    def _on_save(self) -> None:
        if not self._scenario_id:
            QMessageBox.warning(self, "ไม่มี scenario", "เลือกหรือสร้าง scenario ก่อน")
            return
        label, priority, complexity, profile, coordinates = self.profile_form.values()
        if not label:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "กรุณากรอกชื่อเป้าหมาย")
            return
        try:
            if self._target_id:
                self.target_service.update_target_card(
                    UpdateTargetCardRequest(
                        target_card_id=self._target_id,
                        label=label,
                        priority_score=priority,
                        complexity_score=complexity,
                        profile=profile,
                    )
                )
                target_id = self._target_id
            else:
                target_id = self.target_service.create_target_card(
                    CreateTargetCardRequest(
                        scenario_id=self._scenario_id,
                        label=label,
                        priority_score=priority,
                        complexity_score=complexity,
                        profile=profile,
                    )
                )
                self._target_id = target_id
            if coordinates:
                self.target_service.save_target_coordinates(
                    SaveTargetCoordinatesRequest(
                        target_card_id=target_id,
                        scenario_id=self._scenario_id,
                        coordinates=coordinates,
                    )
                )
        except ValueError as exc:
            QMessageBox.warning(self, "Guardrail", str(exc))
            return
        self.load_target(target_id)
        self.targets_changed.emit()
        self.target_saved.emit(target_id)
