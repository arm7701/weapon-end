from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from maap_app.modules.export.schemas import (
    EXPORT_FORMATS,
    EXPORT_TYPES,
    CompareRankingRequest,
    CreateExportRequest,
    ExportReadinessRequest,
    ReplayRankingRequest,
    UpdateActionItemRequest,
)
from maap_app.modules.export.service import ExportService
from maap_app.modules.ranking.repository import RankingRepository


class ExportPanel(QWidget):
    export_changed = Signal()
    readiness_changed = Signal(bool, str)

    def __init__(
        self,
        export_service: ExportService,
        ranking_repository: RankingRepository,
    ) -> None:
        super().__init__()
        self.export_service = export_service
        self.ranking_repository = ranking_repository
        self._scenario_id: str | None = None

        self.setObjectName("SidePanel")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        title = QLabel("AAR & EXPORT")
        title.setObjectName("SectionTitle")
        outer.addWidget(title)
        self.subtitle = QLabel("Phase 6 local exercise outputs, replay, export packages, and after-action review")
        self.subtitle.setObjectName("SectionSubtitle")
        outer.addWidget(self.subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setSpacing(10)

        form = QFormLayout()
        self.export_type = QComboBox()
        self.export_type.addItems(list(EXPORT_TYPES))
        self.export_format = QComboBox()
        self.export_format.addItems(list(EXPORT_FORMATS))
        form.addRow("Export type", self.export_type)
        form.addRow("Format", self.export_format)
        body_layout.addLayout(form)

        self.readiness_label = QLabel("Readiness: not checked")
        self.readiness_label.setWordWrap(True)
        self.readiness_label.setObjectName("OutputCardHint")
        body_layout.addWidget(self.readiness_label)

        btn_row = QHBoxLayout()
        check_btn = QPushButton("Check Readiness")
        check_btn.setObjectName("GhostButton")
        check_btn.clicked.connect(self._check_readiness)
        export_btn = QPushButton("Export")
        export_btn.setObjectName("PrimaryButton")
        export_btn.clicked.connect(self._create_export)
        btn_row.addWidget(check_btn)
        btn_row.addWidget(export_btn)
        body_layout.addLayout(btn_row)

        body_layout.addWidget(_section("Ranking Compare & Replay"))
        compare_form = QFormLayout()
        self.run_a = QComboBox()
        self.run_b = QComboBox()
        compare_form.addRow("Run A", self.run_a)
        compare_form.addRow("Run B", self.run_b)
        body_layout.addLayout(compare_form)
        compare_row = QHBoxLayout()
        compare_btn = QPushButton("Compare Runs")
        compare_btn.setObjectName("SecondaryButton")
        compare_btn.clicked.connect(self._compare_runs)
        replay_btn = QPushButton("Replay Run A")
        replay_btn.setObjectName("GhostButton")
        replay_btn.clicked.connect(self._replay_run)
        compare_row.addWidget(compare_btn)
        compare_row.addWidget(replay_btn)
        body_layout.addLayout(compare_row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(120)
        self.output.setPlaceholderText("Comparison, replay, or AAR output...")
        body_layout.addWidget(self.output)

        aar_btn = QPushButton("Generate AAR")
        aar_btn.setObjectName("SecondaryButton")
        aar_btn.clicked.connect(self._generate_aar)
        body_layout.addWidget(aar_btn)

        body_layout.addWidget(_section("Export History"))
        self.history = QListWidget()
        self.history.setMaximumHeight(100)
        body_layout.addWidget(self.history)

        body_layout.addWidget(_section("AAR Action Items"))
        self.actions = QListWidget()
        self.actions.setMaximumHeight(80)
        body_layout.addWidget(self.actions)
        action_row = QHBoxLayout()
        accept_btn = QPushButton("Accept")
        accept_btn.clicked.connect(lambda: self._update_action("accepted"))
        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.clicked.connect(lambda: self._update_action("dismissed"))
        action_row.addWidget(accept_btn)
        action_row.addWidget(dismiss_btn)
        body_layout.addLayout(action_row)

        body_layout.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, stretch=1)

    def set_scenario(self, scenario_id: str) -> None:
        self._scenario_id = scenario_id
        self.refresh()

    def refresh(self) -> None:
        self._refresh_ranking_runs()
        self._refresh_history()
        self._refresh_actions()
        if self.readiness_label.text() == "":
            self.readiness_label.setText("Readiness: not checked")

    def _refresh_ranking_runs(self) -> None:
        self.run_a.clear()
        self.run_b.clear()
        if not self._scenario_id:
            return
        runs = self.ranking_repository.list_ranking_runs(self._scenario_id)
        for run in runs:
            label = f"{run.created_at or run.id[:8]} — {run.summary[:30]}"
            self.run_a.addItem(label, run.id)
            self.run_b.addItem(label, run.id)

    def _refresh_history(self) -> None:
        self.history.clear()
        if not self._scenario_id:
            return
        for package in self.export_service.list_exports(self._scenario_id):
            text = f"{package.export_type} | {package.export_status}"
            if package.blocked_reason:
                text += f" — {package.blocked_reason[:40]}"
            self.history.addItem(text)

    def _refresh_actions(self) -> None:
        self.actions.clear()
        if not self._scenario_id:
            return
        for item in self.export_service.list_action_items(self._scenario_id):
            self.actions.addItem(f"[{item.status}] {item.description[:60]}")

    def _check_readiness(self) -> None:
        if not self._scenario_id:
            return
        result = self.export_service.check_readiness(
            ExportReadinessRequest(
                scenario_id=self._scenario_id,
                export_type=self.export_type.currentText(),
            )
        )
        lines = []
        if result.ready:
            lines.append("Ready for export.")
        else:
            lines.append("Blocked:")
            lines.extend(f"• {b}" for b in result.blockers)
        if result.warnings:
            lines.append("Warnings:")
            lines.extend(f"• {w}" for w in result.warnings)
        text = "\n".join(lines)
        self.readiness_label.setText(text)
        self.readiness_changed.emit(result.ready, text)

    def _create_export(self) -> None:
        if not self._scenario_id:
            return
        dest = QFileDialog.getExistingDirectory(self, "Select export destination")
        if not dest:
            return
        try:
            package = self.export_service.create_export(
                CreateExportRequest(
                    scenario_id=self._scenario_id,
                    export_type=self.export_type.currentText(),
                    export_format=self.export_format.currentText(),
                    destination_dir=Path(dest),
                    ranking_run_id=self.run_a.currentData(),
                )
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Export", str(exc))
            return
        if package.export_status == "exported":
            QMessageBox.information(self, "Export", f"Exported to:\n{package.destination_path}")
        else:
            QMessageBox.warning(self, "Export blocked", package.blocked_reason)
        self._refresh_history()
        self.export_changed.emit()

    def _compare_runs(self) -> None:
        if not self._scenario_id:
            return
        run_a = self.run_a.currentData()
        run_b = self.run_b.currentData()
        if not run_a or not run_b:
            QMessageBox.information(self, "Compare", "Select two ranking runs.")
            return
        result = self.export_service.compare_ranking_runs(
            CompareRankingRequest(
                scenario_id=self._scenario_id,
                run_a_id=str(run_a),
                run_b_id=str(run_b),
            )
        )
        lines = [result.summary]
        for row in result.rows:
            if row.rank_delta or row.score_delta:
                lines.append(
                    f"{row.entity_label}: rank {row.run_a_rank}->{row.run_b_rank}, "
                    f"score {row.run_a_score}->{row.run_b_score}"
                )
        self.output.setText("\n".join(lines))

    def _replay_run(self) -> None:
        if not self._scenario_id:
            return
        run_id = self.run_a.currentData()
        if not run_id:
            QMessageBox.information(self, "Replay", "Select a ranking run.")
            return
        result = self.export_service.replay_ranking(
            ReplayRankingRequest(
                scenario_id=self._scenario_id,
                ranking_run_id=str(run_id),
            )
        )
        lines = [result.summary]
        for diff in result.differences:
            lines.append(
                f"{diff.entity_label}: rank {diff.original_rank}->{diff.replay_rank}, "
                f"score {diff.original_score}->{diff.replay_score} — {diff.explanation}"
            )
        self.output.setText("\n".join(lines))
        self._refresh_ranking_runs()

    def _generate_aar(self) -> None:
        if not self._scenario_id:
            return
        text, _items = self.export_service.generate_aar(self._scenario_id)
        self.output.setText(text[:3000])
        self._refresh_actions()

    def _update_action(self, status: str) -> None:
        if not self._scenario_id:
            return
        row = self.actions.currentRow()
        items = self.export_service.list_action_items(self._scenario_id)
        if row < 0 or row >= len(items):
            return
        self.export_service.update_action_item(
            UpdateActionItemRequest(action_item_id=items[row].id, status=status)
        )
        self._refresh_actions()


def _section(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("color: #c8d4e0; font-size: 12px; font-weight: 700;")
    return label
