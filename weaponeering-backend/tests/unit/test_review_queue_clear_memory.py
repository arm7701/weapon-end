from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from maap_app.config.ai_settings import AiSettings
from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.ai.context import ContextBundleBuilder
from maap_app.modules.ai.repository import AiRepository
from maap_app.modules.ai.service import AiAssistantService
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.review.service import HumanReviewService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.schemas import CreateTargetCardRequest
from maap_app.modules.target.service import TargetService
from maap_app.modules.weaponeering.repository import WeaponeeringRepository
from maap_app.ui.panels.review_queue_panel import ReviewQueuePanel


def _app() -> QApplication:
    return QApplication.instance() or QApplication(sys.argv)


def _build_services(tmp_path: Path):
    settings = AppSettings(data_dir=tmp_path, database_path=tmp_path / "test.sqlite3")
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    audit_service = AuditService(AuditRepository(database))
    guardrail_service = GuardrailService(GuardrailRepository(database), audit_service)
    scenario_repository = ScenarioRepository(database)
    scenario_service = ScenarioService(
        repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    target_repository = TargetRepository(database)
    target_service = TargetService(
        repository=target_repository,
        scenario_repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    weaponeering_repository = WeaponeeringRepository(database)
    ranking_repository = RankingRepository(database)
    ai_repository = AiRepository(database)
    context_builder = ContextBundleBuilder(
        scenario_repository=scenario_repository,
        target_repository=target_repository,
        weaponeering_repository=weaponeering_repository,
        logistics_repository=LogisticsRepository(database),
        ranking_repository=ranking_repository,
    )
    ai_service = AiAssistantService(
        repository=ai_repository,
        context_builder=context_builder,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
        ai_settings=AiSettings(adapter_mode="rule_based"),
    )
    review_service = HumanReviewService(
        target_repository=target_repository,
        ai_repository=ai_repository,
        weaponeering_repository=weaponeering_repository,
        ranking_repository=ranking_repository,
        audit_service=audit_service,
    )
    return scenario_service, target_service, ai_service, review_service


def test_clear_memory_in_scenario_chat_removes_target_scoped_interactions(
    tmp_path: Path, monkeypatch
) -> None:
    """Reproduces: AI Review > Scenario Chat shows the 'Analyze Product' result
    (a target-scoped interaction), but clicking 'Clear Memory' while viewing
    Scenario Chat left it behind because it only cleared entity_id=='' rows.
    """
    _app()
    scenario_service, target_service, ai_service, review_service = _build_services(
        tmp_path
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Clear Memory Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-CLEAR")
    )

    # Simulates clicking "Analyze Product" in the Weaponeering panel.
    ai_service.analyze_product_selection(
        scenario_id, target_id, analysis_prompt="Analyze MK-82 for TGT-CLEAR"
    )
    # Simulates a real scenario-wide chat message.
    ai_service.chat_with_context(scenario_id, "สวัสดีครับ", target_card_id=None)

    assert len(ai_service.list_interactions(scenario_id)) == 2

    monkeypatch.setattr(
        QMessageBox, "question", staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
    )

    panel = ReviewQueuePanel(review_service, ai_service)
    panel.set_scenario(scenario_id)

    # Scenario Chat (row 0, target_id=None) is selected by default and must show both.
    assert panel._selected_target_id is None
    assert panel.chat_list.count() == 2

    QTest.mouseClick(panel.clear_memory_btn, Qt.MouseButton.LeftButton)

    # All underlying data must be gone — the panel always shows one
    # "No AI interactions" placeholder row when the list is genuinely empty.
    assert ai_service.list_interactions(scenario_id) == []
    assert panel.chat_list.count() == 1
    assert panel.chat_list.item(0).text() == "No AI interactions for this selection."


def test_clear_memory_in_target_thread_does_not_affect_other_threads(
    tmp_path: Path, monkeypatch
) -> None:
    """Clearing memory while viewing one Target's thread must only remove that
    target's interactions — Scenario Chat and other targets must be untouched.
    """
    _app()
    scenario_service, target_service, ai_service, review_service = _build_services(
        tmp_path
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Target Scope Scenario")
    )
    target_a = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-A")
    )
    target_b = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-B")
    )

    ai_service.analyze_product_selection(
        scenario_id, target_a, analysis_prompt="Analyze for TGT-A"
    )
    ai_service.analyze_product_selection(
        scenario_id, target_b, analysis_prompt="Analyze for TGT-B"
    )
    ai_service.chat_with_context(scenario_id, "สวัสดีครับ", target_card_id=None)

    assert len(ai_service.list_interactions(scenario_id)) == 3

    monkeypatch.setattr(
        QMessageBox, "question", staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
    )

    panel = ReviewQueuePanel(review_service, ai_service)
    panel.set_scenario(scenario_id)

    # Row 0 is Scenario Chat; row 1 is the first target thread (TGT-A).
    panel.target_list.setCurrentRow(1)
    assert panel._selected_target_id == target_a

    QTest.mouseClick(panel.clear_memory_btn, Qt.MouseButton.LeftButton)

    remaining = ai_service.list_interactions(scenario_id)
    assert len(remaining) == 2
    remaining_entity_ids = {r.entity_id for r in remaining}
    assert target_a not in remaining_entity_ids
    assert target_b in remaining_entity_ids
    assert "" in remaining_entity_ids
