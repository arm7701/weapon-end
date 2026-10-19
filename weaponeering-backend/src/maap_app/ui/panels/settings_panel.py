from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from maap_app.config.ai_settings import ADAPTER_MODES, AiSettings, normalize_chat_url
from maap_app.config.map_settings import MapSettings
from maap_app.config.settings import AppSettings
from maap_app.modules.ai.service import AiAssistantService


class SettingsPanel(QWidget):
    ai_settings_changed = Signal(str)
    map_settings_changed = Signal(object)

    def __init__(
        self,
        ai_service: AiAssistantService,
        app_settings: AppSettings,
        map_settings: MapSettings | None = None,
    ) -> None:
        super().__init__()
        self.ai_service = ai_service
        self.app_settings = app_settings
        self.map_settings = map_settings or MapSettings.load(app_settings.data_dir)
        self.setObjectName("MapWorkspace")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setObjectName("MapWorkspaceHeader")
        header.setFixedHeight(48)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 14, 0)
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title = QLabel("ตั้งค่าระบบ")
        title.setObjectName("MapWorkspaceTitle")
        subtitle = QLabel("กำหนด Local LLM, OpenAI-compatible API และค่าการทำงานของ AI")
        subtitle.setObjectName("SectionSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch(1)
        root.addWidget(header)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 12, 14, 12)
        body_layout.setSpacing(10)
        tabs = QTabWidget()
        tabs.setObjectName("WingDataTabs")
        tabs.addTab(self._build_ai_tab(), "AI")
        tabs.addTab(self._build_map_tab(), "Map")
        body_layout.addWidget(tabs, stretch=1)
        root.addWidget(body, stretch=1)

        self._load_from_service()
        self._load_map_settings()
        self._syncing_adapter_mode = False

    def sync_adapter_mode(self, mode: str) -> None:
        index = self.mode.findText(mode)
        self._syncing_adapter_mode = True
        try:
            if index >= 0:
                self.mode.setCurrentIndex(index)
        finally:
            self._syncing_adapter_mode = False

    def _build_map_tab(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        stadia_group, stadia_form = self._form_card(
            "Stadia Maps",
            "Stadia Satellite และ Smooth Dark ต้องใช้ API Key ฟรีจาก stadiamaps.com",
        )
        self.stadia_api_key = QLineEdit()
        self.stadia_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.stadia_api_key.setPlaceholderText("Stadia API key")
        self._set_field_width(self.stadia_api_key, 520)
        stadia_form.addRow("API Key", self.stadia_api_key)
        layout.addWidget(stadia_group)

        info_card, info_layout = self._form_card(
            "Basemap Notes",
            "OpenTopoMap, Cesium/ดาวเทียม และ RTAF ใช้ได้โดยไม่ต้องมี Stadia key",
        )
        note = QLabel(
            "สมัคร API Key ฟรีที่ https://client.stadiamaps.com/ "
            "แล้วนำ key มาใส่ด้านบน · เก็บในเครื่อง local เท่านั้น"
        )
        note.setObjectName("FormSectionSubtitle")
        note.setWordWrap(True)
        info_layout.addWidget(note)
        layout.addWidget(info_card)

        layout.addStretch(1)
        scroll.setWidget(content)
        page_layout.addWidget(scroll, stretch=1)

        btn_container = QWidget()
        btn_container.setObjectName("FormCard")
        button_row = QHBoxLayout(btn_container)
        button_row.setContentsMargins(14, 10, 14, 10)
        button_row.setSpacing(8)
        save_btn = QPushButton("Save Map Settings")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._save_map_settings)
        reload_btn = QPushButton("Reload")
        reload_btn.setObjectName("GhostButton")
        reload_btn.clicked.connect(self._load_map_settings)
        button_row.addWidget(save_btn)
        button_row.addWidget(reload_btn)
        button_row.addStretch(1)
        page_layout.addWidget(btn_container)
        return page

    def _build_ai_tab(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        # --- scrollable content area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # AI Adapter
        mode_group, mode_form = self._form_card(
            "AI Adapter",
            "เลือกโหมดการทำงานของ AI สำหรับ workflow ภายในระบบ",
        )
        self.mode = QComboBox()
        self.mode.addItems(list(ADAPTER_MODES))
        self._set_field_width(self.mode, 280)
        mode_form.addRow("Mode", self.mode)
        layout.addWidget(mode_group)

        # Local LLM Server
        local_group, local_form = self._form_card(
            "Local LLM Server",
            "ตั้งค่า server ภายใน เช่น Ollama-compatible /api/chat",
        )
        self.local_url = QLineEdit()
        self.local_url.setPlaceholderText("http://127.0.0.1:11434/api/chat")
        self._set_field_width(self.local_url, 680)
        self.local_model = QLineEdit()
        self.local_model.setPlaceholderText("llama3.1:8b")
        self._set_field_width(self.local_model, 320)
        self.local_context_window = QSpinBox()
        self.local_context_window.setRange(512, 131072)
        self.local_context_window.setSingleStep(512)
        self.local_context_window.setToolTip(
            "Context window (num_ctx) sent to the local server.\n"
            "Local servers like Ollama default to a small window (often 2048-4096 tokens) "
            "regardless of what the model supports. If chat with a long scenario or memory "
            "history comes back empty, raise this value."
        )
        self._set_field_width(self.local_context_window, 160)
        self.local_timeout = QSpinBox()
        self.local_timeout.setRange(5, 600)
        self.local_timeout.setSingleStep(5)
        self.local_timeout.setSuffix(" s")
        self.local_timeout.setToolTip(
            "How long to wait for the local server to respond before giving up.\n"
            "Local inference can be slower than cloud APIs, especially with large models "
            "or a large context window. Raise this if you see 'AI adapter request failed' "
            "timeouts on slow hardware."
        )
        self._set_field_width(self.local_timeout, 160)
        self.strip_cot = QCheckBox("Strip chain-of-thought tags (<think> blocks)")
        self.strip_cot.setToolTip(
            "Enable for reasoning models: DeepSeek-R1, QwQ, and similar.\n"
            "Removes <think>…</think> content and returns only the final answer.\n"
            "Safe to leave on for all models — has no effect if the model does not output think tags."
        )
        self.enable_cot = QCheckBox("Enable chain-of-thought reasoning")
        self.enable_cot.setToolTip(
            "When enabled, the model reasons step-by-step before answering (reasoning models only).\n"
            "When disabled, sends /no_think — skips reasoning phase for faster responses.\n"
            "Has no effect on standard models (LLaMA, Nemotron, Qwen, etc.)."
        )
        local_form.addRow("Chat URL", self.local_url)
        local_form.addRow("Model", self.local_model)
        local_form.addRow("Context window", self.local_context_window)
        local_form.addRow("Request timeout", self.local_timeout)
        local_form.addRow("", self.strip_cot)
        local_form.addRow("", self.enable_cot)
        layout.addWidget(local_group)

        # OpenAI-Compatible API
        openai_group, openai_form = self._form_card(
            "OpenAI-Compatible API",
            "ตั้งค่า endpoint, model และ API key สำหรับ chat completions",
        )
        self.openai_url = QLineEdit()
        self.openai_url.setPlaceholderText("https://api.openai.com/v1/chat/completions")
        self._set_field_width(self.openai_url, 680)
        self.openai_model = QLineEdit()
        self.openai_model.setPlaceholderText("gpt-4o-mini")
        self._set_field_width(self.openai_model, 360)
        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key.setPlaceholderText("API key")
        self._set_field_width(self.openai_key, 520)
        openai_form.addRow("Chat URL", self.openai_url)
        openai_form.addRow("Model", self.openai_model)
        openai_form.addRow("API Key", self.openai_key)
        layout.addWidget(openai_group)

        # Gemini API
        gemini_group, gemini_form = self._form_card(
            "Gemini API",
            "ตั้งค่า endpoint, model และ API key สำหรับ Google Gemini",
        )
        self.gemini_url = QLineEdit()
        self.gemini_url.setPlaceholderText(
            "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        )
        self._set_field_width(self.gemini_url, 680)
        self.gemini_model = QLineEdit()
        self.gemini_model.setPlaceholderText("gemini-flash-latest")
        self._set_field_width(self.gemini_model, 360)
        self.gemini_key = QLineEdit()
        self.gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key.setPlaceholderText("API key")
        self._set_field_width(self.gemini_key, 520)
        gemini_form.addRow("Chat URL", self.gemini_url)
        gemini_form.addRow("Model", self.gemini_model)
        gemini_form.addRow("API Key", self.gemini_key)
        layout.addWidget(gemini_group)

        # Connection Notes
        info_card, info_layout = self._form_card(
            "Connection Notes",
            "ตัวอย่าง payload และข้อควรระวังสำหรับการเก็บ key",
        )
        example = QLabel(
            'Local server example: POST /api/chat with {"model": "...", '
            '"messages": [...], "stream": false}'
        )
        example.setObjectName("FormSectionSubtitle")
        example.setWordWrap(True)
        info_layout.addWidget(example)
        warning = QLabel(
            "API keys are stored locally in the app data folder. "
            "Use local LLM mode when possible for offline training workflows."
        )
        warning.setObjectName("FormSectionSubtitle")
        warning.setWordWrap(True)
        info_layout.addWidget(warning)
        layout.addWidget(info_card)

        layout.addStretch(1)
        scroll.setWidget(content)
        page_layout.addWidget(scroll, stretch=1)

        # --- action buttons pinned outside scroll, always visible ---
        btn_container = QWidget()
        btn_container.setObjectName("FormCard")
        button_row = QHBoxLayout(btn_container)
        button_row.setContentsMargins(14, 10, 14, 10)
        button_row.setSpacing(8)
        save_btn = QPushButton("Save AI Settings")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._save)
        test_btn = QPushButton("Test Connection")
        test_btn.setObjectName("SecondaryButton")
        test_btn.clicked.connect(self._test_connection)
        reset_btn = QPushButton("Reload")
        reset_btn.setObjectName("GhostButton")
        reset_btn.clicked.connect(self._load_from_service)
        button_row.addWidget(save_btn)
        button_row.addWidget(test_btn)
        button_row.addWidget(reset_btn)
        button_row.addStretch(1)
        page_layout.addWidget(btn_container)

        return page

    def _form_card(self, title: str, subtitle: str) -> tuple[QWidget, QFormLayout]:
        card = QWidget()
        card.setObjectName("FormCard")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("FormSectionTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("FormSectionSubtitle")
        subtitle_label.setWordWrap(True)
        outer.addWidget(title_label)
        outer.addWidget(subtitle_label)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)
        outer.addLayout(form)
        return card, form

    def _set_field_width(self, widget: QWidget, width: int) -> None:
        widget.setMinimumWidth(min(width, 280))
        widget.setMaximumWidth(width)

    def _load_from_service(self) -> None:
        settings = self.ai_service.ai_settings
        self.mode.setCurrentText(settings.adapter_mode)
        self.local_url.setText(settings.local_server_url)
        self.local_model.setText(settings.local_model)
        self.local_context_window.setValue(settings.local_context_window)
        self.local_timeout.setValue(settings.local_request_timeout)
        self.strip_cot.setChecked(settings.strip_chain_of_thought)
        self.enable_cot.setChecked(settings.enable_chain_of_thought)
        self.openai_url.setText(settings.openai_base_url)
        self.openai_model.setText(settings.openai_model)
        self.openai_key.setText(settings.openai_api_key)
        self.gemini_url.setText(settings.gemini_base_url)
        self.gemini_model.setText(settings.gemini_model)
        self.gemini_key.setText(settings.gemini_api_key)

    def _settings_from_form(self) -> AiSettings:
        # preserve guardrail_enabled — it is toggled via the chat panel button, not this form
        current = self.ai_service.ai_settings
        return AiSettings(
            adapter_mode=self.mode.currentText(),
            local_server_url=normalize_chat_url(self.local_url.text()),
            local_model=self.local_model.text().strip(),
            local_context_window=self.local_context_window.value(),
            local_request_timeout=self.local_timeout.value(),
            openai_base_url=normalize_chat_url(self.openai_url.text()),
            openai_model=self.openai_model.text().strip(),
            openai_api_key=self.openai_key.text().strip(),
            gemini_base_url=normalize_chat_url(self.gemini_url.text()),
            gemini_model=self.gemini_model.text().strip(),
            gemini_api_key=self.gemini_key.text().strip(),
            guardrail_enabled=current.guardrail_enabled,
            strip_chain_of_thought=self.strip_cot.isChecked(),
            enable_chain_of_thought=self.enable_cot.isChecked(),
        )

    def _validate_settings(self, settings: AiSettings) -> bool:
        if settings.adapter_mode == "local_model" and (
            not settings.local_server_url or not settings.local_model
        ):
            QMessageBox.warning(self, "AI Settings", "Local server URL and model are required.")
            return False
        if settings.adapter_mode == "openai" and (
            not settings.openai_base_url
            or not settings.openai_model
            or not settings.openai_api_key
        ):
            QMessageBox.warning(
                self,
                "AI Settings",
                "OpenAI-compatible URL, model, and API key are required.",
            )
            return False
        if settings.adapter_mode == "gemini" and (
            not settings.gemini_base_url
            or not settings.gemini_model
            or not settings.gemini_api_key
        ):
            QMessageBox.warning(
                self,
                "AI Settings",
                "Gemini URL, model, and API key are required.",
            )
            return False
        return True

    def _save(self) -> None:
        settings = self._settings_from_form()
        if not self._validate_settings(settings):
            return
        self.ai_service.update_settings(settings, self.app_settings.data_dir)
        self.ai_settings_changed.emit(settings.adapter_mode)
        QMessageBox.information(self, "AI Settings", "AI settings saved.")

    def _test_connection(self) -> None:
        settings = self._settings_from_form()
        if not self._validate_settings(settings):
            return
        ok, message = self.ai_service.test_connection(settings)
        if ok:
            QMessageBox.information(self, "AI Connection", f"Connection OK.\n\n{message}")
        else:
            QMessageBox.warning(self, "AI Connection", f"Connection failed.\n\n{message}")

    def _load_map_settings(self) -> None:
        self.map_settings = MapSettings.load(self.app_settings.data_dir)
        self.stadia_api_key.setText(self.map_settings.stadia_api_key)

    def _save_map_settings(self) -> None:
        self.map_settings = MapSettings(
            stadia_api_key=self.stadia_api_key.text().strip(),
        )
        self.map_settings.save(self.app_settings.data_dir)
        self.map_settings_changed.emit(self.map_settings)
        QMessageBox.information(self, "Map Settings", "Map settings saved.")
