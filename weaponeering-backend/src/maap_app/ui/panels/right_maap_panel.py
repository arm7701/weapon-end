from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


def _section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("color: #dbeafe; font-size: 12px; font-weight: 800;")
    return label


def _muted_label(text: str = "—") -> QLabel:
    label = QLabel(text)
    label.setObjectName("OutputCardHint")
    label.setWordWrap(True)
    return label


class RightMaapPanel(QWidget):
    """Target-focused MAAP output panel.

    The right panel intentionally shows only data about the currently selected
    Target so the map workspace can act as the operator's main context.
    """

    ranking_item_selected = Signal(str)
    ai_output_changed = Signal()

    def __init__(
        self,
        ranking_service: object | None = None,
        ai_service: object | None = None,
        review_service: object | None = None,
        export_service: object | None = None,
    ) -> None:
        super().__init__()
        self.ranking_service = ranking_service
        self.ai_service = ai_service
        self.review_service = review_service
        self.export_service = export_service
        self._scenario_id: str | None = None
        self._scenario_name: str = "None selected"

        self.setObjectName("SidePanel")
        self.setMinimumWidth(320)
        self.setMaximumWidth(420)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("MAAP OUTPUT")
        title.setObjectName("SectionTitle")
        subtitle = _muted_label("เลือก Target เพื่อดูข้อมูลประกอบการจัดลำดับและแผนจำลอง")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.target_card = self._build_summary_card()
        self.risk_card = self._build_risk_card()
        self.product_card = self._build_product_card()
        self.plan_card = self._build_plan_card()
        self.wing_card = self._build_wing_card()

        for card in (
            self.target_card,
            self.risk_card,
            self.product_card,
            self.plan_card,
            self.wing_card,
        ):
            layout.addWidget(card)
        layout.addStretch(1)
        scroll.setWidget(body)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self.clear_target_output()

    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("OutputCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        return card, layout

    def _build_summary_card(self) -> QWidget:
        card, layout = self._card()
        layout.addWidget(_section_title("Target Summary"))
        self.target_label = QLabel("—")
        self.target_label.setObjectName("OutputCardValue")
        self.target_meta = _muted_label()
        self.target_location = _muted_label()
        self.target_recognition = _muted_label()
        self.target_warnings = _muted_label()
        layout.addWidget(self.target_label)
        layout.addWidget(self.target_meta)
        layout.addWidget(self.target_location)
        layout.addWidget(self.target_recognition)
        layout.addWidget(self.target_warnings)
        return card

    def _build_risk_card(self) -> QWidget:
        card, layout = self._card()
        layout.addWidget(_section_title("Risk & Detection"))
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        self.risk_objects = self._metric("Objects", "—")
        self.risk_high = self._metric("High", "—")
        self.risk_medium = self._metric("Medium", "—")
        self.risk_low = self._metric("Low", "—")
        self.risk_model = self._metric("Model", "—")
        for index, widget in enumerate(
            (
                self.risk_objects,
                self.risk_high,
                self.risk_medium,
                self.risk_low,
                self.risk_model,
            )
        ):
            grid.addWidget(widget, index // 2, index % 2)
        self.risk_detail = _muted_label()
        self.object_table = QTableWidget(0, 4)
        self.object_table.setHorizontalHeaderLabels(["Object", "Risk", "Conf.", "Location"])
        self.object_table.verticalHeader().setVisible(False)
        self.object_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.object_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.object_table.setMaximumHeight(190)
        object_header = self.object_table.horizontalHeader()
        object_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        object_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        object_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        object_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(grid_host)
        layout.addWidget(self.risk_detail)
        layout.addWidget(self.object_table)
        return card

    def _metric(self, title: str, value: str) -> QWidget:
        host = QFrame()
        host.setStyleSheet(
            "QFrame { background: rgba(15, 23, 42, 0.55); "
            "border: 1px solid rgba(148, 163, 184, 0.18); border-radius: 6px; }"
        )
        layout = QVBoxLayout(host)
        layout.setContentsMargins(8, 7, 8, 7)
        label = QLabel(title)
        label.setObjectName("OutputCardTitle")
        value_label = QLabel(value)
        value_label.setObjectName("OutputCardValue")
        layout.addWidget(label)
        layout.addWidget(value_label)
        host.value_label = value_label  # type: ignore[attr-defined]
        return host

    def _set_metric(self, metric: QWidget, value: str) -> None:
        metric.value_label.setText(value)  # type: ignore[attr-defined]

    def _build_product_card(self) -> QWidget:
        card, layout = self._card()
        layout.addWidget(_section_title("Product Ranking"))
        self.product_hint = _muted_label()
        self.product_table = QTableWidget(0, 4)
        self.product_table.setHorizontalHeaderLabels(["#", "Product", "Pd", "N"])
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.product_table.setMaximumHeight(170)
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.product_hint)
        layout.addWidget(self.product_table)
        return card

    def _build_plan_card(self) -> QWidget:
        card, layout = self._card()
        layout.addWidget(_section_title("Target Plan"))
        self.plan_status = QLabel("—")
        self.plan_status.setObjectName("OutputCardValue")
        self.plan_detail = _muted_label()
        self.plan_aircraft = _muted_label()
        self.plan_route = _muted_label()
        layout.addWidget(self.plan_status)
        layout.addWidget(self.plan_detail)
        layout.addWidget(self.plan_aircraft)
        layout.addWidget(self.plan_route)
        return card

    def _build_wing_card(self) -> QWidget:
        card, layout = self._card()
        layout.addWidget(_section_title("Nearest Air Wing"))
        self.wing_name = QLabel("—")
        self.wing_name.setObjectName("OutputCardValue")
        self.wing_distance = _muted_label()
        self.wing_readiness = _muted_label()
        layout.addWidget(self.wing_name)
        layout.addWidget(self.wing_distance)
        layout.addWidget(self.wing_readiness)
        return card

    def clear_target_output(self) -> None:
        self.target_label.setText("No Target selected")
        self.target_meta.setText(f"Scenario: {self._scenario_name}")
        self.target_location.setText("เลือก Target จากแผนที่หรือเมนู Target")
        self.target_recognition.setText("Recognition: —")
        self.target_warnings.setText("")
        self._set_metric(self.risk_objects, "—")
        self._set_metric(self.risk_high, "—")
        self._set_metric(self.risk_medium, "—")
        self._set_metric(self.risk_low, "—")
        self._set_metric(self.risk_model, "—")
        self.risk_detail.setText("ยังไม่มีข้อมูล detection สำหรับ Target")
        self.object_table.setRowCount(0)
        self.product_hint.setText("ยังไม่ได้เลือก Target หรือยังไม่มี Product ใน Database")
        self.product_table.setRowCount(0)
        self.plan_status.setText("No plan")
        self.plan_detail.setText("ยังไม่ได้บันทึกแผนประจำ Target")
        self.plan_aircraft.setText("")
        self.plan_route.setText("")
        self.wing_name.setText("—")
        self.wing_distance.setText("ต้องมีพิกัด Target และกองบินใน Database")
        self.wing_readiness.setText("")

    def show_target_output(self, payload: dict[str, Any]) -> None:
        target = payload.get("target", {})
        self.target_label.setText(str(target.get("label") or "Target"))
        self.target_meta.setText(
            " · ".join(
                part
                for part in (
                    f"Type: {target.get('targetType') or '—'}",
                    f"Priority: {target.get('priorityScore', '—')}",
                    f"Complexity: {target.get('complexityScore', '—')}",
                )
                if part
            )
        )
        self.target_location.setText(str(payload.get("location") or "Location: —"))
        self.target_recognition.setText(str(payload.get("recognition") or "Recognition: —"))
        warnings = payload.get("warnings") or []
        self.target_warnings.setText(
            "Warnings: " + "; ".join(warnings[:3]) if warnings else "Warnings: none"
        )

        risk = payload.get("risk") or {}
        self._set_metric(self.risk_objects, str(risk.get("objectCount", 0)))
        self._set_metric(self.risk_high, str(risk.get("highCount", 0)))
        self._set_metric(self.risk_medium, str(risk.get("mediumCount", 0)))
        self._set_metric(self.risk_low, str(risk.get("lowCount", 0)))
        self._set_metric(self.risk_model, str(risk.get("modelName") or "—"))
        self.risk_detail.setText(str(risk.get("detail") or "ยังไม่มีข้อมูล detection"))
        self._populate_object_table(risk.get("objects") or [])

        products = payload.get("products") or []
        self.product_table.setRowCount(0)
        if products:
            self.product_hint.setText(str(payload.get("productHint") or "Top ranked products"))
            for row_index, item in enumerate(products[:5]):
                self.product_table.insertRow(row_index)
                values = [
                    str(item.get("rank", row_index + 1)),
                    str(item.get("productName", "—")),
                    f"{float(item.get('pdBase', 0.0)):.4f}",
                    str(item.get("nRequired", "—")),
                ]
                for col, value in enumerate(values):
                    self.product_table.setItem(row_index, col, QTableWidgetItem(value))
        else:
            self.product_hint.setText("ไม่มี Product Ranking สำหรับ Target นี้")

        plan = payload.get("plan") or {}
        self.plan_status.setText(str(plan.get("status") or "No plan"))
        self.plan_detail.setText(str(plan.get("detail") or "ยังไม่ได้บันทึกแผนประจำ Target"))
        self.plan_aircraft.setText(str(plan.get("aircraft") or ""))
        self.plan_route.setText(str(plan.get("route") or ""))

        wing = payload.get("nearestWing") or {}
        self.wing_name.setText(str(wing.get("name") or "—"))
        self.wing_distance.setText(str(wing.get("distance") or "ไม่พบกองบินที่มีพิกัด"))
        self.wing_readiness.setText(str(wing.get("readiness") or ""))

    def _populate_object_table(self, objects: list[dict[str, Any]]) -> None:
        self.object_table.setRowCount(0)
        for row_index, item in enumerate(objects):
            self.object_table.insertRow(row_index)
            risk_label = self._display_risk_label(
                str(item.get("label") or "Building"),
                str(item.get("riskLevel") or ""),
                str(item.get("riskMeaning") or ""),
            )
            values = [
                str(item.get("label") or "Building"),
                risk_label,
                f"{float(item.get('confidence', 0.0)):.2f}",
                self._object_location(item),
            ]
            for col, value in enumerate(values):
                self.object_table.setItem(row_index, col, QTableWidgetItem(value))

    @staticmethod
    def _display_risk_label(label: str, risk_level: str, meaning: str) -> str:
        risk_name = risk_level.title() if risk_level else "Unknown"
        if label.lower() == "building":
            return f"Building {risk_name} · {meaning}"
        return f"{risk_name} · {meaning}"

    @staticmethod
    def _object_location(item: dict[str, Any]) -> str:
        try:
            lat = float(item.get("lat"))
            lng = float(item.get("lng"))
        except (TypeError, ValueError):
            return "—"
        return f"{lat:.5f}, {lng:.5f}"

    def set_scenario(self, scenario_id: str, name: str) -> None:
        self._scenario_id = scenario_id
        self._scenario_name = name
        self.clear_target_output()

    # Compatibility hooks retained for existing MainWindow signal wiring.
    def set_review_summary(self, pending: int) -> None:
        return

    def set_export_readiness(self, ready: bool, hint: str) -> None:
        return

    def set_ai_output(self, text: str, interaction_id: str | None, review_status: str) -> None:
        self.ai_output_changed.emit()

    def _update_ai_status(self) -> None:
        return

    def refresh_ranking(self) -> None:
        return

    def set_logistics_result(self, score: int, rationale: str, warnings: list[str]) -> None:
        return
