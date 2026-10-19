from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.ai.service import AiAssistantService
from maap_app.modules.detection.persistence_service import TargetDetectionService
from maap_app.modules.target.service import TargetService
from maap_app.ui.panels.wing_form_widgets import _form_card


_SOURCE_OPTIONS = ("Image File", "Video File", "Connect CCTV")
_MODEL_OPTIONS = (
    "YOLOv8-MAAP Tactical",
    "RT-DETR Surveillance",
    "Faster-RCNN MilSpec v2",
)
_CLASS_FILTERS = ("SMV", "LMV", "AFV", "CV", "MCV")
_MOCK_EVENTS = (
    ("SMV", 0.94, "128,96,52,38", "T-001"),
    ("LMV", 0.88, "312,140,44,32", "T-002"),
    ("AFV", 0.91, "480,220,96,72", "T-003"),
    ("CV", 0.86, "640,180,88,64", "T-004"),
    ("MCV", 0.83, "820,260,76,58", "T-005"),
)


class BoundedPreviewLabel(QLabel):
    """Preview that scales down to fit the column without expanding the layout."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._source: QPixmap | None = None
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(0, 0)
        self.setScaledContents(False)

    def minimumSizeHint(self) -> QSize:
        return QSize(0, 0)

    def sizeHint(self) -> QSize:
        return QSize(200, 120)

    def has_image(self) -> bool:
        return self._source is not None and not self._source.isNull()

    def set_source_pixmap(self, pixmap: QPixmap | None) -> None:
        if pixmap is None or pixmap.isNull():
            self.clear_image()
            return
        self._source = pixmap
        self._refresh()

    def clear_image(self) -> None:
        self._source = None
        super().setPixmap(QPixmap())

    def refresh_image(self) -> None:
        self._refresh()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self.has_image():
            self._refresh()

    def _refresh(self) -> None:
        if not self.has_image() or self._source is None:
            return
        avail_w = max(self.width(), 1)
        avail_h = max(self.height(), 1)
        src_w = self._source.width()
        src_h = self._source.height()
        scale = min(avail_w / src_w, avail_h / src_h, 1.0)
        target_w = max(int(src_w * scale), 1)
        target_h = max(int(src_h * scale), 1)
        if target_w == src_w and target_h == src_h:
            super().setPixmap(self._source)
            return
        super().setPixmap(
            self._source.scaled(
                target_w,
                target_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class ObjectDetectionPanel(QWidget):
    link_map_requested = Signal(str)
    targets_changed = Signal()
    ai_summary_ready = Signal(str, str)

    def __init__(
        self,
        target_service: TargetService,
        ai_service: AiAssistantService | None = None,
        detection_service: TargetDetectionService | None = None,
    ) -> None:
        super().__init__()
        self.target_service = target_service
        self.ai_service = ai_service
        self.detection_service = detection_service
        self._scenario_id: str | None = None
        self._selected_target_id: str | None = None
        self._coordinates: list[dict[str, object]] = []
        self._media_path: str | None = None
        self._running = False
        self._class_checks: dict[str, QCheckBox] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.target_label = QLabel("Target Card: —")
        self.target_label.setObjectName("FormSectionSubtitle")
        root.addWidget(self.target_label)

        map_detect_card, map_detect_layout = _form_card(
            "Map Detection (YOLO)",
            "รัน Detection รอบพิกัดแต่ละจุดจากแผนที่ · ใช้ปุ่ม Run Detection บนแผนที่",
        )
        self.detection_coordinate = QComboBox()
        self.detection_coordinate.currentIndexChanged.connect(
            self._update_detection_status
        )
        map_detect_layout.addWidget(
            _stacked_detection_field("พิกัด", self.detection_coordinate)
        )
        self.detection_status = QLabel(
            "เลือก Target และพิกัด · จากนั้นกด Run Detection บนแผนที่"
        )
        self.detection_status.setWordWrap(True)
        self.detection_status.setStyleSheet("color: #9fb0c2; font-size: 10px;")
        map_detect_layout.addWidget(self.detection_status)
        root.addWidget(map_detect_card)

        source_card, source_layout = _form_card(
            "Source Input & Model",
            "เลือกช่องทางข้อมูลและโมเดลสำหรับตรวจจับวัตถุ",
        )
        source_form = QFormLayout()
        source_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        source_form.setHorizontalSpacing(12)
        source_form.setVerticalSpacing(8)

        source_row = QWidget()
        source_row_layout = QHBoxLayout(source_row)
        source_row_layout.setContentsMargins(0, 0, 0, 0)
        source_row_layout.setSpacing(8)
        self.source_input = QComboBox()
        self.source_input.addItems(list(_SOURCE_OPTIONS))
        self.source_input.currentTextChanged.connect(self._on_source_changed)
        self.source_action_btn = QPushButton("Browse…")
        self.source_action_btn.setObjectName("SecondaryButton")
        self.source_action_btn.clicked.connect(self._on_source_action)
        source_row_layout.addWidget(self.source_input, 1)
        source_row_layout.addWidget(self.source_action_btn)
        source_form.addRow("Source Input", source_row)

        self.model_input = QComboBox()
        self.model_input.addItems(list(_MODEL_OPTIONS))
        source_form.addRow("Model", self.model_input)
        source_layout.addLayout(source_form)
        root.addWidget(source_card)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        preview_frame = QWidget()
        preview_frame.setObjectName("DetectionPreviewFrame")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)

        self.preview_status = QLabel("Media Preview")
        self.preview_status.setObjectName("FormFieldLabel")
        self.preview_status.setContentsMargins(8, 6, 8, 4)
        preview_layout.addWidget(self.preview_status)

        self.preview = BoundedPreviewLabel()
        self.preview.setObjectName("DetectionPreview")
        self.preview.setText("ยังไม่มีสื่อ — เลือก Source Input แล้วโหลดไฟล์หรือเชื่อม CCTV")
        self.preview.setWordWrap(True)
        preview_layout.addWidget(self.preview, stretch=1)
        splitter.addWidget(preview_frame)

        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        control_card, control_layout = _form_card(
            "Detection Controls",
            "เลือกประเภทวัตถุที่ต้องการตรวจจับ แล้วเริ่มการทำงาน",
        )
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)
        self.all_check = QCheckBox("ALL")
        self.all_check.setChecked(True)
        self.all_check.toggled.connect(self._on_all_toggled)
        filter_row.addWidget(self.all_check)
        for label in _CLASS_FILTERS:
            check = QCheckBox(label)
            check.setChecked(True)
            check.toggled.connect(self._on_class_toggled)
            self._class_checks[label] = check
            filter_row.addWidget(check)
        filter_row.addStretch(1)
        control_layout.addLayout(filter_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("PrimaryButton")
        self.start_btn.clicked.connect(self._on_start)
        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn = QPushButton("Stop")
        for btn in (self.play_btn, self.pause_btn, self.stop_btn):
            btn.setObjectName("SecondaryButton")
            btn.setEnabled(False)
        self.play_btn.clicked.connect(lambda: self._video_action("Play"))
        self.pause_btn.clicked.connect(lambda: self._video_action("Pause"))
        self.stop_btn.clicked.connect(lambda: self._video_action("Stop"))
        action_row.addWidget(self.start_btn)
        action_row.addWidget(self.play_btn)
        action_row.addWidget(self.pause_btn)
        action_row.addWidget(self.stop_btn)
        action_row.addStretch(1)
        control_layout.addLayout(action_row)
        bottom_layout.addWidget(control_card)

        log_card, log_layout = _form_card(
            "Event Log",
            "บันทึกวัตถุที่ระบบตรวจจับได้",
        )
        self.event_table = QTableWidget(0, 6)
        self.event_table.setHorizontalHeaderLabels(
            ["Time", "Class", "Confidence", "BBox", "Track ID", "Source"]
        )
        self.event_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.event_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.event_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.event_table.setAlternatingRowColors(True)
        self.event_table.verticalHeader().setVisible(False)
        self.event_table.setMaximumHeight(150)
        header = self.event_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        log_layout.addWidget(self.event_table)
        bottom_layout.addWidget(log_card)

        splitter.addWidget(bottom)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([480, 180])

        root.addWidget(splitter, stretch=1)

        self._on_source_changed(self.source_input.currentText())

    def set_scenario(self, scenario_id: str | None) -> None:
        self._scenario_id = scenario_id
        self._selected_target_id = None
        self._update_target_label()

    def show_target(self, target_id: str) -> None:
        self._selected_target_id = target_id
        self._update_target_label()
        self._update_detection_status()

    def refresh_detection_coordinates(
        self,
        target_id: str,
        coordinates: list[dict[str, object]],
    ) -> None:
        self._selected_target_id = target_id
        self._coordinates = coordinates
        self.detection_coordinate.blockSignals(True)
        self.detection_coordinate.clear()
        for index, coord in enumerate(coordinates):
            coord_id = str(coord.get("id") or f"coord-{index}")
            label = str(coord.get("label") or f"P{index + 1}")
            lat = float(coord.get("lat") or 0.0)
            lng = float(coord.get("lng") or 0.0)
            primary_suffix = " · หลัก" if coord.get("isPrimary") else ""
            self.detection_coordinate.addItem(
                f"{label} — {lat:.5f}, {lng:.5f}{primary_suffix}",
                coord_id,
            )
        if self.detection_coordinate.count():
            primary_index = next(
                (
                    index
                    for index in range(self.detection_coordinate.count())
                    if " · หลัก" in self.detection_coordinate.itemText(index)
                ),
                0,
            )
            self.detection_coordinate.setCurrentIndex(primary_index)
        self.detection_coordinate.blockSignals(False)
        self._update_target_label()
        self._update_detection_status()

    def complete_map_link(self, target_id: str) -> None:
        self.show_target(target_id)

    def _update_target_label(self) -> None:
        if not self._selected_target_id:
            self.target_label.setText("Target Card: — (เลือกจาก Target Stack ด้านซ้าย)")
            return
        detail = self.target_service.get_target_detail(self._selected_target_id)
        if detail is None:
            self.target_label.setText("Target Card: —")
            return
        self.target_label.setText(
            f"Target Card: {detail.card.label} · {detail.card.target_type}"
        )

    def _update_detection_status(self) -> None:
        if not self._selected_target_id:
            self.detection_status.setText(
                "เลือก Target จาก Target Stack แล้วเลือกพิกัดสำหรับ Run Detection"
            )
            return
        coordinate_id = str(self.detection_coordinate.currentData() or "")
        if not coordinate_id:
            self.detection_status.setText("ยังไม่มีพิกัด — เพิ่มพิกัดใน Target Stack")
            return
        if coordinate_id.startswith("draft-"):
            self.detection_status.setText(
                "พิกัดนี้ยังไม่ได้บันทึก — กดบันทึกใน Target Stack ก่อน Run Detection"
            )
            return
        if self.detection_service is None:
            self.detection_status.setText(
                "พร้อม Run Detection บนแผนที่สำหรับพิกัดที่เลือก"
            )
            return
        run = self.detection_service.get_run_for_coordinate(
            self._selected_target_id,
            coordinate_id,
        )
        if run is None:
            self.detection_status.setText(
                "ยังไม่มีผล Detection สำหรับพิกัดนี้ — กด Run Detection บนแผนที่"
            )
            return
        self.detection_status.setText(
            f"ล่าสุด: {run.model_name} · {run.object_count} วัตถุ · "
            f"รัศมี {run.radius_m} m · {run.detection_message or 'บันทึกแล้ว'}"
        )

    def _on_source_changed(self, source: str) -> None:
        is_cctv = source == "Connect CCTV"
        self.source_action_btn.setText("Connect…" if is_cctv else "Browse…")
        self.source_action_btn.setEnabled(True)
        self._set_video_controls(source in ("Video File", "Connect CCTV") and bool(self._media_path))
        if not self._media_path:
            hint = {
                "Image File": "ยังไม่มีภาพ — กด Browse เพื่อเลือกไฟล์",
                "Video File": "ยังไม่มีวิดีโอ — กด Browse เพื่อเลือกไฟล์",
                "Connect CCTV": "ยังไม่ได้เชื่อม CCTV — กด Connect เพื่อระบุ URL",
            }
            self._set_preview_message(hint.get(source, "ยังไม่มีสื่อ"))

    def _set_preview_message(self, message: str, status: str = "Media Preview") -> None:
        self.preview.clear_image()
        self.preview.setText(message)
        self.preview_status.setText(status)

    def _show_preview_image(self, path: str) -> None:
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._set_preview_message("ไม่สามารถโหลดภาพได้", f"Image · {path.rsplit('/', 1)[-1]}")
            return
        self.preview.setText("")
        self.preview.set_source_pixmap(pixmap)
        name = path.rsplit("/", 1)[-1]
        self.preview_status.setText(f"Image · {name} · {pixmap.width()}×{pixmap.height()}")

    def _on_source_action(self) -> None:
        source = self.source_input.currentText()
        if source == "Image File":
            path, _ = QFileDialog.getOpenFileName(
                self,
                "เลือกไฟล์ภาพ",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)",
            )
            if path:
                self._load_media(path, "image")
        elif source == "Video File":
            path, _ = QFileDialog.getOpenFileName(
                self,
                "เลือกไฟล์วิดีโอ",
                "",
                "Videos (*.mp4 *.avi *.mov *.mkv);;All Files (*)",
            )
            if path:
                self._load_media(path, "video")
        else:
            self._connect_cctv()

    def _load_media(self, path: str, kind: str) -> None:
        self._media_path = path
        name = path.rsplit("/", 1)[-1]
        if kind == "image":
            self._show_preview_image(path)
            self._set_video_controls(False)
        else:
            self._set_preview_message(
                f"🎬 Video loaded\n{name}\n\n(Mock preview — ใช้ Video Control หรือกด Start)",
                f"Video · {name}",
            )
            self._set_video_controls(True)
        self._clear_event_log()
        self._running = False
        self.start_btn.setText("Start")

    def _connect_cctv(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Connect CCTV")
        dialog.setMinimumWidth(360)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        url_field = QLineEdit()
        url_field.setPlaceholderText("rtsp://192.168.1.10:554/stream1")
        name_field = QLineEdit()
        name_field.setPlaceholderText("CCTV Tower-01")
        form.addRow("Stream URL", url_field)
        form.addRow("Label", name_field)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        url = url_field.text().strip()
        if not url:
            QMessageBox.warning(self, "Connect CCTV", "กรุณาระบุ Stream URL")
            return
        label = name_field.text().strip() or "CCTV Feed"
        self._media_path = url
        self._set_preview_message(
            f"📡 CCTV connected\n{label}\n{url}\n\n(Mock stream — ใช้ Video Control หรือกด Start)",
            f"CCTV · {label}",
        )
        self._set_video_controls(True)
        self._clear_event_log()
        self._running = False
        self.start_btn.setText("Start")

    def _set_video_controls(self, enabled: bool) -> None:
        for btn in (self.play_btn, self.pause_btn, self.stop_btn):
            btn.setEnabled(enabled and bool(self._media_path))

    def _on_all_toggled(self, checked: bool) -> None:
        for check in self._class_checks.values():
            check.blockSignals(True)
            check.setChecked(checked)
            check.blockSignals(False)

    def _on_class_toggled(self, _checked: bool) -> None:
        all_on = all(c.isChecked() for c in self._class_checks.values())
        self.all_check.blockSignals(True)
        self.all_check.setChecked(all_on)
        self.all_check.blockSignals(False)

    def _active_classes(self) -> set[str]:
        if self.all_check.isChecked():
            return set(_CLASS_FILTERS)
        return {label for label, check in self._class_checks.items() if check.isChecked()}

    def _on_start(self) -> None:
        if not self._media_path:
            QMessageBox.information(
                self,
                "Object Detection",
                "โหลด Image / Video หรือเชื่อม CCTV ก่อนเริ่มตรวจจับ",
            )
            return
        active = self._active_classes()
        if not active:
            QMessageBox.information(
                self,
                "Object Detection",
                "เลือกอย่างน้อย 1 ประเภทวัตถุ (SMV, LMV, AFV, CV, MCV)",
            )
            return
        if self._running:
            self._running = False
            self.start_btn.setText("Start")
            self.preview.setStyleSheet("")
            if self.preview.has_image():
                self.preview.refresh_image()
            return

        self._running = True
        self.start_btn.setText("Stop")
        source = self.source_input.currentText()
        model = self.model_input.currentText()
        classes = ", ".join(sorted(active))
        status = (
            f"🔴 DETECTION ACTIVE · {model} · {classes} · {source}"
        )
        self.preview_status.setText(status)
        self.preview.setStyleSheet("border: 1px solid #2563eb;")
        if self.preview.has_image():
            self.preview.refresh_image()

        self._clear_event_log()
        now = datetime.now()
        source_tag = self._media_path.rsplit("/", 1)[-1] if self._media_path else "-"
        for index, (cls, conf, bbox, track) in enumerate(_MOCK_EVENTS):
            if cls not in active:
                continue
            ts = now.replace(second=min(now.second + index, 59)).strftime("%H:%M:%S")
            self._append_event(ts, cls, conf, bbox, track, source_tag)

    def _video_action(self, action: str) -> None:
        if not self._media_path:
            return
        self._append_event(
            datetime.now().strftime("%H:%M:%S"),
            "—",
            0.0,
            "—",
            "—",
            f"Video {action}",
        )

    def _append_event(
        self,
        time_str: str,
        cls: str,
        confidence: float,
        bbox: str,
        track_id: str,
        source: str,
    ) -> None:
        row = self.event_table.rowCount()
        self.event_table.insertRow(row)
        conf_text = "—" if confidence <= 0 else f"{confidence:.2f}"
        values = [time_str, cls, conf_text, bbox, track_id, source]
        for col, value in enumerate(values):
            self.event_table.setItem(row, col, QTableWidgetItem(value))

    def _clear_event_log(self) -> None:
        self.event_table.setRowCount(0)


def _stacked_detection_field(label: str, widget: QWidget) -> QWidget:
    host = QWidget()
    layout = QVBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    name = QLabel(label)
    name.setObjectName("FormFieldLabel")
    layout.addWidget(name)
    layout.addWidget(widget)
    return host
