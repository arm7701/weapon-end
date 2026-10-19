from __future__ import annotations

import json

from PySide6.QtCore import QSize, QThread, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QApplication,
    QComboBox,
    QSizePolicy,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.ai.service import AiAssistantService
from maap_app.modules.review.schemas import ReviewActionRequest
from maap_app.modules.review.service import HumanReviewService


class _AiChatWorker(QThread):
    response_ready = Signal(object)
    error = Signal(str)

    def __init__(self, ai_service, scenario_id, message, target_card_id):
        super().__init__()
        self._ai_service = ai_service
        self._scenario_id = scenario_id
        self._message = message
        self._target_card_id = target_card_id

    def run(self):
        try:
            result = self._ai_service.chat_with_context(
                self._scenario_id,
                self._message,
                target_card_id=self._target_card_id,
            )
            self.response_ready.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class _ChatList(QListWidget):
    """QListWidget whose size hints are fixed so adding items never expands the window."""

    def sizeHint(self) -> QSize:
        return QSize(400, 300)

    def minimumSizeHint(self) -> QSize:
        return QSize(200, 100)


def _thread_subtitle(priority, complexity, interactions: list) -> str:
    count = len(interactions)
    parts = []
    if priority is not None:
        parts.append(f"Priority {priority}/5")
    if count == 0:
        parts.append("No messages yet")
    else:
        last_at = getattr(interactions[0], "created_at", None)
        time_hint = f" · {str(last_at)[:16]}" if last_at else ""
        parts.append(f"{count} message{'s' if count != 1 else ''}{time_hint}")
    return " | ".join(parts)


class ReviewQueuePanel(QWidget):
    review_changed = Signal()
    ai_mode_changed = Signal(str)

    def __init__(
        self,
        review_service: HumanReviewService,
        ai_service: AiAssistantService,
    ) -> None:
        super().__init__()
        self.review_service = review_service
        self.ai_service = ai_service
        self._scenario_id: str | None = None
        self._selected_target_id: str | None = None
        self._selected_entity_type: str | None = None
        self._selected_entity_id: str | None = None
        self._typing_item: QListWidgetItem | None = None
        self._worker: _AiChatWorker | None = None

        self.setObjectName("MapWorkspace")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("MapWorkspaceHeader")
        header.setFixedHeight(48)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 14, 0)
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title = QLabel("AI REVIEW QUEUE")
        title.setObjectName("MapWorkspaceTitle")
        self.subtitle = QLabel("เลือก Target เพื่อดูบทสนทนา AI, LLM input, output และรายการที่ต้องอนุมัติ")
        self.subtitle.setObjectName("SectionSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(self.subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch(1)
        layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)

        target_col = QWidget()
        target_col.setObjectName("TargetThreadPanel")
        target_col.setMinimumWidth(180)
        target_layout = QVBoxLayout(target_col)
        target_layout.setContentsMargins(14, 14, 14, 14)
        target_layout.setSpacing(10)
        target_title = QLabel("CHAT THREADS")
        target_title.setObjectName("ThreadPanelTitle")
        target_layout.addWidget(target_title)
        target_hint = QLabel("เลือก Scenario หรือ Target เพื่อกรองห้องแชท")
        target_hint.setObjectName("ThreadPanelSubtitle")
        target_layout.addWidget(target_hint)
        self.target_list = QListWidget()
        self.target_list.setObjectName("TargetThreadList")
        self.target_list.setSpacing(8)
        self.target_list.currentItemChanged.connect(self._on_target_selected)
        target_layout.addWidget(self.target_list, stretch=1)
        splitter.addWidget(target_col)

        chat_col = QWidget()
        chat_col.setObjectName("ChatPanel")
        chat_col.setMinimumWidth(300)
        chat_layout = QVBoxLayout(chat_col)
        chat_layout.setContentsMargins(14, 14, 14, 14)
        chat_layout.setSpacing(10)

        chat_header = QWidget()
        chat_header.setObjectName("ChatHeader")
        chat_header_layout = QHBoxLayout(chat_header)
        chat_header_layout.setContentsMargins(12, 10, 12, 10)
        chat_header_layout.setSpacing(10)
        chat_title_box = QVBoxLayout()
        chat_title_box.setSpacing(2)
        chat_title = QLabel("AI CHAT ROOM")
        chat_title.setObjectName("ChatTitle")
        self.chat_scope = QLabel("Scenario-wide conversation")
        self.chat_scope.setObjectName("ChatSubtitle")
        chat_title_box.addWidget(chat_title)
        chat_title_box.addWidget(self.chat_scope)
        chat_header_layout.addLayout(chat_title_box)
        chat_header_layout.addStretch(1)
        self.clear_memory_btn = QPushButton("ล้าง Memory")
        self.clear_memory_btn.setObjectName("GhostButton")
        self.clear_memory_btn.clicked.connect(self._clear_memory)
        chat_header_layout.addWidget(self.clear_memory_btn)
        self.guardrail_btn = QPushButton()
        self.guardrail_btn.clicked.connect(self._toggle_guardrail)
        chat_header_layout.addWidget(self.guardrail_btn)
        self.cot_btn = QPushButton()
        self.cot_btn.clicked.connect(self._toggle_cot)
        chat_header_layout.addWidget(self.cot_btn)
        self.memory_badge = QLabel("MEMORY ON")
        self.memory_badge.setObjectName("ChatBadge")
        chat_header_layout.addWidget(self.memory_badge)
        chat_layout.addWidget(chat_header)
        self._update_guardrail_btn()
        self._update_cot_btn()

        self.chat_list = _ChatList()
        self.chat_list.setObjectName("ChatList")
        self.chat_list.setSpacing(10)
        self.chat_list.setWordWrap(True)
        self.chat_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.chat_list.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.chat_list.verticalScrollBar().setSingleStep(20)
        self.chat_list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self.chat_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.chat_list.currentItemChanged.connect(self._on_item_selected)
        chat_layout.addWidget(self.chat_list, stretch=1)

        self.chat_input = QTextEdit()
        self.chat_input.setObjectName("ChatComposer")
        self.chat_input.setPlaceholderText(
            "พิมพ์คำถามเพื่อคุยกับ AI ตาม Scenario หรือ Target ที่เลือก..."
        )
        self.chat_input.setMinimumHeight(68)
        self.chat_input.setMaximumHeight(150)
        chat_layout.addWidget(self.chat_input)

        send_row = QHBoxLayout()
        send_row.setSpacing(10)
        self.chat_status = QLabel("Memory uses recent local interactions for this selection.")
        self.chat_status.setObjectName("ChatStatus")
        send_row.addWidget(self.chat_status, stretch=1)
        mode_label = QLabel("AI mode")
        mode_label.setObjectName("ChatStatus")
        send_row.addWidget(mode_label)
        self.ai_mode = QComboBox()
        self.ai_mode.setObjectName("ChatModeCombo")
        self.ai_mode.addItems(["rule_based", "disabled", "local_model", "openai", "gemini", "sandboxed"])
        self._syncing_ai_mode = False
        self.ai_mode.currentTextChanged.connect(self._on_ai_mode_combo_changed)
        send_row.addWidget(self.ai_mode)
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("ChatSendButton")
        self.send_btn.clicked.connect(self._send_chat_message)
        send_row.addWidget(self.send_btn)
        chat_layout.addLayout(send_row)
        splitter.addWidget(chat_col)

        detail_col = QWidget()
        detail_col.setObjectName("ToolsPanel")
        detail_col.setMinimumWidth(180)
        detail_layout = QVBoxLayout(detail_col)
        detail_layout.setContentsMargins(14, 14, 14, 14)
        detail_layout.setSpacing(10)
        detail_title = QLabel("TOOLS")
        detail_title.setObjectName("ThreadPanelTitle")
        detail_layout.addWidget(detail_title)
        tools_hint = QLabel("เลือก chat card ก่อนใช้เครื่องมือตรวจสอบ")
        tools_hint.setObjectName("ThreadPanelSubtitle")
        detail_layout.addWidget(tools_hint)

        self.detail = QTextEdit()
        self.detail.setObjectName("ToolsDetail")
        self.detail.setReadOnly(True)
        self.detail.setPlaceholderText("Selected card detail appears here.")
        self.detail.setMinimumHeight(60)
        detail_layout.addWidget(self.detail, stretch=1)

        input_btn = QPushButton("View LLM Input")
        input_btn.setObjectName("SecondaryButton")
        input_btn.clicked.connect(self._show_llm_input)
        output_btn = QPushButton("View Output")
        output_btn.setObjectName("GhostButton")
        output_btn.clicked.connect(self._show_llm_output)
        detail_layout.addWidget(input_btn)
        detail_layout.addWidget(output_btn)

        self.notes = QLineEdit()
        self.notes.setPlaceholderText("Instructor notes (required for revision)")
        detail_layout.addWidget(self.notes)

        approve_btn = QPushButton("Approve")
        approve_btn.setObjectName("PrimaryButton")
        approve_btn.clicked.connect(lambda: self._apply_action("approve"))
        reject_btn = QPushButton("Reject")
        reject_btn.setObjectName("GhostButton")
        reject_btn.clicked.connect(lambda: self._apply_action("reject"))
        revision_btn = QPushButton("Request Revision")
        revision_btn.setObjectName("SecondaryButton")
        revision_btn.clicked.connect(lambda: self._apply_action("needs_revision"))
        detail_layout.addWidget(approve_btn)
        detail_layout.addWidget(reject_btn)
        detail_layout.addWidget(revision_btn)
        detail_layout.addStretch(0)

        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        detail_scroll.setWidget(detail_col)
        splitter.addWidget(detail_scroll)

        self._splitter = splitter
        layout.addWidget(splitter, stretch=1)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._apply_splitter_sizes)

    def _apply_splitter_sizes(self) -> None:
        total = self._splitter.width()
        if total <= 0:
            return
        handles = self._splitter.handleWidth() * 2
        avail = total - handles
        left = max(180, min(280, int(avail * 0.21)))
        right = max(180, min(260, int(avail * 0.19)))
        center = avail - left - right
        self._splitter.setSizes([left, max(center, 300), right])

    def set_scenario(self, scenario_id: str) -> None:
        self._scenario_id = scenario_id
        self.refresh()

    def _on_ai_mode_combo_changed(self, mode: str) -> None:
        if self._syncing_ai_mode or not mode:
            return
        self.ai_mode_changed.emit(mode)

    def set_ai_mode(self, mode: str) -> None:
        index = self.ai_mode.findText(mode)
        self._syncing_ai_mode = True
        try:
            if index >= 0:
                self.ai_mode.setCurrentIndex(index)
        finally:
            self._syncing_ai_mode = False

    def refresh(self) -> None:
        self.target_list.clear()
        self.chat_list.clear()
        self._selected_entity_type = None
        self._selected_entity_id = None
        self.detail.clear()
        if not self._scenario_id:
            return
        scenario_ixs = self.review_service.list_all_ai_interactions(self._scenario_id)
        self._add_thread_item(
            title="Scenario Chat",
            subtitle=_thread_subtitle(None, None, scenario_ixs),
            badge="ALL",
            target_id=None,
            is_scenario=True,
        )
        for target in self.review_service.list_targets(self._scenario_id):
            target_ixs = self.review_service.list_ai_interactions(self._scenario_id, target.id)
            self._add_thread_item(
                title=target.label,
                subtitle=_thread_subtitle(target.priority_score, target.complexity_score, target_ixs),
                badge=target.review_status.replace("_", " ").upper(),
                target_id=target.id,
                is_scenario=False,
            )
        if self.target_list.count() > 0:
            self.target_list.setCurrentRow(0)
        else:
            self._update_chat_scope(None)
            self._refresh_chat()

    def _add_thread_item(
        self,
        *,
        title: str,
        subtitle: str,
        badge: str,
        target_id: str | None,
        is_scenario: bool = False,
    ) -> None:
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, target_id)
        item.setData(
            Qt.ItemDataRole.DisplayRole,
            title if target_id else "All AI Interactions",
        )
        self.target_list.addItem(item)
        card = self._build_thread_card(item, title, subtitle, badge, target_id, is_scenario=is_scenario)
        item.setSizeHint(card.sizeHint())
        self.target_list.setItemWidget(item, card)

    def _build_thread_card(
        self,
        item: QListWidgetItem,
        title: str,
        subtitle: str,
        badge: str,
        target_id: str | None,
        *,
        is_scenario: bool = False,
    ) -> QWidget:
        card = QWidget()
        card.setObjectName("TargetThreadCardScenario" if is_scenario else "TargetThreadCard")
        card.setProperty("active", False)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName(
            "ThreadCardScenarioTitle" if is_scenario else "ThreadCardTitle"
        )
        title_label.setWordWrap(True)
        top_row.addWidget(title_label, stretch=1)
        badge_label = QLabel(badge)
        badge_label.setObjectName("ThreadCardBadge" if target_id else "ThreadCardAllBadge")
        top_row.addWidget(badge_label)
        layout.addLayout(top_row)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("ThreadCardSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)

        def select_item(_event=None) -> None:
            self.target_list.setCurrentItem(item)

        card.mousePressEvent = select_item  # type: ignore[method-assign]
        title_label.mousePressEvent = select_item  # type: ignore[method-assign]
        subtitle_label.mousePressEvent = select_item  # type: ignore[method-assign]
        badge_label.mousePressEvent = select_item  # type: ignore[method-assign]
        return card

    def _refresh_chat(self) -> None:
        self.chat_list.clear()
        self._selected_entity_type = None
        self._selected_entity_id = None
        self.detail.clear()
        if not self._scenario_id:
            return

        if self._selected_target_id is None:
            # Scenario Chat: show ALL threads in chronological order with origin labels
            id_to_label: dict[str, str] = {}
            for target in self.review_service.list_targets(self._scenario_id):
                id_to_label[target.id] = target.label
            interactions = self.review_service.list_all_ai_interactions(self._scenario_id)
            for interaction in interactions:
                if interaction.entity_type == "target_card" and interaction.entity_id:
                    thread_label = f"Target: {id_to_label.get(interaction.entity_id, interaction.entity_id[:8])}"
                else:
                    thread_label = "Scenario Chat"
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, ("ai_interaction", interaction.id))
                self.chat_list.addItem(item)
                bubble = self._build_chat_bubble(interaction, item, thread_label=thread_label)
                item.setSizeHint(bubble.sizeHint())
                self.chat_list.setItemWidget(item, bubble)
        else:
            interactions = self.review_service.list_ai_interactions(
                self._scenario_id,
                self._selected_target_id,
            )
            for interaction in reversed(interactions):
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, ("ai_interaction", interaction.id))
                self.chat_list.addItem(item)
                bubble = self._build_chat_bubble(interaction, item)
                item.setSizeHint(bubble.sizeHint())
                self.chat_list.setItemWidget(item, bubble)

        if self._selected_target_id is None:
            for item in self.review_service.list_queue(self._scenario_id):
                if item.entity_type == "ai_interaction":
                    continue
                label = f"[{item.source}] {item.label} — {item.review_status}"
                if item.is_blocked:
                    label = f"⛔ {label}"
                list_item = QListWidgetItem(label)
                list_item.setData(Qt.ItemDataRole.UserRole, (item.entity_type, item.entity_id))
                if item.is_blocked:
                    list_item.setForeground(Qt.GlobalColor.red)
                self.chat_list.addItem(list_item)

        if self.chat_list.count() == 0:
            empty = QListWidgetItem("No AI interactions for this selection.")
            empty.setFlags(empty.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.chat_list.addItem(empty)
        else:
            self.chat_list.clearSelection()
            QTimer.singleShot(0, self.chat_list.scrollToBottom)

    def _build_chat_bubble(
        self,
        interaction,
        item: QListWidgetItem,
        *,
        thread_label: str | None = None,
    ) -> QWidget:
        container = QWidget()
        container.setObjectName("ChatItem")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        def select_item(_event=None) -> None:
            self.chat_list.setCurrentItem(item)

        container.mousePressEvent = select_item  # type: ignore[method-assign]

        if thread_label is not None:
            tag = QLabel(f"[ {thread_label} ]")
            tag.setObjectName("ThreadOriginTag")
            tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tag.mousePressEvent = select_item  # type: ignore[method-assign]
            layout.addWidget(tag)

        user_text = self._chat_user_text(interaction)
        output_text = interaction.sanitized_output.strip() or "AI output blocked or empty."
        meta = f"{interaction.request_type.replace('_', ' ')} | {interaction.review_status}"
        if interaction.created_at:
            meta += f" | {interaction.created_at}"

        if user_text:
            layout.addLayout(
                self._message_row(
                    "YOU",
                    user_text,
                    align_right=True,
                    object_name="UserBubble",
                    on_click=select_item,
                )
            )
        layout.addLayout(
            self._message_row(
                "AI",
                output_text,
                align_right=False,
                object_name=(
                    "BlockedBubble"
                    if interaction.review_status == "blocked_by_guardrail"
                    else "AiBubble"
                ),
                on_click=select_item,
            )
        )

        meta_label = QLabel(meta)
        meta_label.setObjectName("ChatMeta")
        meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        meta_label.mousePressEvent = select_item  # type: ignore[method-assign]
        layout.addWidget(meta_label)
        return container

    def _message_row(
        self,
        speaker: str,
        text: str,
        *,
        align_right: bool,
        object_name: str,
        on_click,
    ) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        bubble = QLabel(f"{speaker}\n{text}")
        bubble.setObjectName(object_name)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setMinimumWidth(260)
        bubble.setMaximumWidth(620)
        bubble.setMargin(10)
        bubble.adjustSize()
        bubble.mousePressEvent = on_click  # type: ignore[method-assign]
        if align_right:
            row.addStretch(1)
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch(1)
        return row

    def _chat_user_text(self, interaction) -> str:
        user_prompt = self._extract_user_prompt(interaction.sanitized_prompt)
        marker = "Current user message:"
        if marker in user_prompt:
            user_prompt = user_prompt.split(marker, 1)[1].strip()
            memory_marker = "Conversation memory from previous local interactions:"
            if memory_marker in user_prompt:
                user_prompt = user_prompt.split(memory_marker, 1)[0].strip()
        if not user_prompt:
            return interaction.request_type.replace("_", " ")
        return self._compact_chat_text(user_prompt, max_chars=1200)

    def _chat_title(self, interaction) -> str:
        if interaction.request_type != "chat_with_context":
            return interaction.request_type.replace("_", " ")
        user_prompt = self._extract_user_prompt(interaction.sanitized_prompt)
        marker = "Current user message:"
        if marker in user_prompt:
            user_prompt = user_prompt.split(marker, 1)[1].strip()
            memory_marker = "Conversation memory from previous local interactions:"
            if memory_marker in user_prompt:
                user_prompt = user_prompt.split(memory_marker, 1)[0].strip()
        first_line = user_prompt.splitlines()[0] if user_prompt else "chat message"
        return first_line[:90]

    @staticmethod
    def _compact_chat_text(text: str, max_chars: int) -> str:
        clean = "\n".join(line.rstrip() for line in text.strip().splitlines())
        if len(clean) <= max_chars:
            return clean
        return clean[: max_chars - 3].rstrip() + "..."

    @staticmethod
    def _extract_user_prompt(sanitized_prompt: str) -> str:
        try:
            data = json.loads(sanitized_prompt)
        except json.JSONDecodeError:
            return sanitized_prompt.strip()
        if isinstance(data, dict):
            value = data.get("user_prompt")
            if isinstance(value, str):
                return value.strip()
        return sanitized_prompt.strip()

    def _on_target_selected(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        for i in range(self.target_list.count()):
            item = self.target_list.item(i)
            card = self.target_list.itemWidget(item)
            if card is not None:
                is_active = item is current
                card.setProperty("active", is_active)
                card.style().unpolish(card)
                card.style().polish(card)
                card.update()
        self._selected_target_id = current.data(Qt.ItemDataRole.UserRole) if current else None
        self._update_chat_scope(current)
        self._refresh_chat()

    def _update_chat_scope(self, current: QListWidgetItem | None) -> None:
        if not current or current.data(Qt.ItemDataRole.UserRole) is None:
            self.chat_scope.setText("Scenario-wide conversation")
            return
        self.chat_scope.setText(f"Target thread: {current.text()}")

    def _on_item_selected(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return
        data = current.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        entity_type, entity_id = data
        self._selected_entity_type = entity_type
        self._selected_entity_id = entity_id
        self.detail.setText(self.review_service.get_item_detail(entity_type, entity_id))

    def _selected_ai_interaction(self):
        if self._selected_entity_type != "ai_interaction" or not self._selected_entity_id:
            QMessageBox.information(self, "AI Review", "Select an AI interaction first.")
            return None
        return self.review_service.get_ai_interaction(self._selected_entity_id)

    def _show_dialog(self, title: str, text: str) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        screen = QApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            dialog.resize(min(900, int(rect.width() * 0.7)), min(620, int(rect.height() * 0.75)))
        else:
            dialog.resize(900, 620)
        layout = QVBoxLayout(dialog)
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        viewer = QTextEdit()
        viewer.setReadOnly(True)
        viewer.setPlainText(text or "No content available.")
        layout.addWidget(viewer, stretch=1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def _show_llm_input(self) -> None:
        interaction = self._selected_ai_interaction()
        if interaction is None:
            return
        self._show_dialog("LLM Input", interaction.sanitized_prompt)

    def _show_llm_output(self) -> None:
        interaction = self._selected_ai_interaction()
        if interaction is None:
            return
        self._show_dialog("LLM Output", interaction.sanitized_output)

    def _send_chat_message(self) -> None:
        if not self._scenario_id:
            QMessageBox.information(self, "AI Chat", "Select or create a scenario first.")
            return
        message = self.chat_input.toPlainText().strip()
        if not message:
            QMessageBox.information(self, "AI Chat", "Type a message first.")
            return
        if not self.ai_service.is_enabled():
            QMessageBox.information(self, "AI disabled", "Enable AI in Settings / AI Review.")
            return

        self.chat_input.clear()
        self.send_btn.setEnabled(False)
        self.chat_status.setText("AI กำลังคิด...")
        self._add_typing_indicator()

        self._worker = _AiChatWorker(
            self.ai_service,
            self._scenario_id,
            message,
            self._selected_target_id,
        )
        self._worker.response_ready.connect(self._on_ai_response)
        self._worker.error.connect(self._on_ai_error)
        self._worker.start()

    def _on_ai_response(self, result) -> None:
        self._typing_item = None
        self.send_btn.setEnabled(True)
        self._refresh_chat()
        self._update_current_thread_subtitle()
        QTimer.singleShot(0, self.chat_list.scrollToBottom)
        if result is not None:
            self.chat_status.setText("Memory: included recent local interactions for this selection.")
        else:
            self.chat_status.setText("No AI response returned.")
        self.chat_input.setFocus()

    def _on_ai_error(self, msg: str) -> None:
        self._remove_typing_indicator()
        self.send_btn.setEnabled(True)
        self.chat_status.setText(f"Error: {msg}")
        self.chat_input.setFocus()

    def _add_typing_indicator(self) -> None:
        item = QListWidgetItem()
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self.chat_list.addItem(item)
        bubble = QLabel("AI กำลังคิด ...")
        bubble.setObjectName("TypingBubble")
        bubble.setMargin(10)
        item.setSizeHint(bubble.sizeHint())
        self.chat_list.setItemWidget(item, bubble)
        self._typing_item = item
        QTimer.singleShot(0, self.chat_list.scrollToBottom)

    def _remove_typing_indicator(self) -> None:
        if self._typing_item is not None:
            row = self.chat_list.row(self._typing_item)
            if row >= 0:
                self.chat_list.takeItem(row)
            self._typing_item = None

    def _update_current_thread_subtitle(self) -> None:
        if not self._scenario_id:
            return
        current = self.target_list.currentItem()
        if current is None:
            return
        target_id = current.data(Qt.ItemDataRole.UserRole)
        interactions = self.review_service.list_ai_interactions(self._scenario_id, target_id)
        card = self.target_list.itemWidget(current)
        if card is None:
            return
        subtitle_label = card.findChild(QLabel, "ThreadCardSubtitle")
        if subtitle_label is not None:
            priority = None
            complexity = None
            if target_id is not None:
                for target in self.review_service.list_targets(self._scenario_id):
                    if target.id == target_id:
                        priority = target.priority_score
                        complexity = target.complexity_score
                        break
            subtitle_label.setText(_thread_subtitle(priority, complexity, interactions))

    def _apply_action(self, decision: str) -> None:
        if not self._scenario_id or not self._selected_entity_id:
            QMessageBox.information(self, "Review", "Select a queue item first.")
            return
        try:
            self.review_service.apply_review_action(
                ReviewActionRequest(
                    scenario_id=self._scenario_id,
                    entity_type=self._selected_entity_type or "",
                    entity_id=self._selected_entity_id,
                    decision=decision,
                    notes=self.notes.text().strip(),
                )
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Review", str(exc))
            return
        self.notes.clear()
        self.refresh()
        self.review_changed.emit()

    def _toggle_guardrail(self) -> None:
        self.ai_service.toggle_guardrail()
        self._update_guardrail_btn()

    def _update_guardrail_btn(self) -> None:
        enabled = self.ai_service.ai_settings.guardrail_enabled
        if enabled:
            self.guardrail_btn.setText("Guardrail ON")
            self.guardrail_btn.setObjectName("GuardrailOnButton")
        else:
            self.guardrail_btn.setText("Guardrail OFF")
            self.guardrail_btn.setObjectName("GuardrailOffButton")
        self.guardrail_btn.style().unpolish(self.guardrail_btn)
        self.guardrail_btn.style().polish(self.guardrail_btn)

    def _toggle_cot(self) -> None:
        self.ai_service.toggle_chain_of_thought()
        self._update_cot_btn()

    def _update_cot_btn(self) -> None:
        enabled = self.ai_service.ai_settings.enable_chain_of_thought
        if enabled:
            self.cot_btn.setText("CoT ON")
            self.cot_btn.setObjectName("CotOnButton")
        else:
            self.cot_btn.setText("CoT OFF")
            self.cot_btn.setObjectName("CotOffButton")
        self.cot_btn.style().unpolish(self.cot_btn)
        self.cot_btn.style().polish(self.cot_btn)

    def _clear_memory(self) -> None:
        if not self._scenario_id:
            QMessageBox.information(self, "ล้าง Memory", "ไม่มี Scenario ที่เลือกอยู่")
            return
        if self._selected_target_id:
            scope_text = "ประวัติการสนทนา AI ของเป้าหมายนี้ (Target Chat)"
        else:
            scope_text = "ประวัติการสนทนา AI ของ Scenario Chat"
        reply = QMessageBox.question(
            self,
            "ล้าง Memory",
            f"ล้าง{scope_text}ใช่หรือไม่?\n\nประวัติที่ลบจะไม่สามารถกู้คืนได้",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._selected_target_id:
                self.ai_service.clear_chat_memory(self._scenario_id, self._selected_target_id)
            else:
                # Scenario Chat displays every interaction across all threads
                # (see _refresh_chat), so clearing it must remove all of them —
                # not just the entity_id=="" subset clear_chat_memory(None) would.
                self.ai_service.clear_scenario_memory(self._scenario_id)
            self._refresh_chat()
            self.chat_status.setText("ล้าง Memory เรียบร้อยแล้ว")
