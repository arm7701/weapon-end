from __future__ import annotations

import json
from pathlib import Path

from maap_app.config.ai_settings import AiSettings
from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.ai.classifier import classify_input
from maap_app.modules.ai.context import ContextBundleBuilder
from maap_app.modules.ai.repository import AiRepository
from maap_app.modules.ai.schemas import AiRequest
from maap_app.modules.ai.service import AiAssistantService
from maap_app.modules.ai.validator import validate_output
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.review.schemas import ReviewActionRequest
from maap_app.modules.review.service import HumanReviewService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.schemas import (
    CreateRecognitionResultRequest,
    CreateTargetCardRequest,
)
from maap_app.modules.target.service import TargetService
from maap_app.modules.weaponeering.repository import WeaponeeringRepository


def build_phase_5_services(
    tmp_path: Path,
) -> tuple[str, str, AiAssistantService, HumanReviewService, TargetService]:
    settings = AppSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.sqlite3",
    )
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
    ai_repository = AiRepository(database)
    weaponeering_repository = WeaponeeringRepository(database)
    ranking_repository = RankingRepository(database)
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

    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Phase 5 Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(
            scenario_id=scenario_id,
            label="TGT-AI-01",
            priority_score=4,
            complexity_score=2,
        )
    )
    target_service.create_recognition_result(
        CreateRecognitionResultRequest(
            target_card_id=target_id,
            source_type="manual",
            recognition_summary="Synthetic training recognition summary.",
            recognition_confidence_score=72,
            missing_data_notes=["No map node linked"],
        )
    )
    return scenario_id, target_id, ai_service, review_service, target_service


def test_classifier_and_validator() -> None:
    assert classify_input("summarize synthetic training target") == "safe_training"
    assert classify_input("recommend weapon for real target") == "blocked_operational"
    allowed, result = validate_output("Training-only abstract scoring summary.")
    assert allowed
    assert result == "allowed_training_output"
    blocked, blocked_result = validate_output("Probability of kill PK=0.9 for GBU-31")
    assert not blocked
    assert blocked_result == "blocked_unsafe_output"


def test_ai_target_summary_and_review_approve(tmp_path: Path) -> None:
    scenario_id, target_id, ai_service, review_service, _ = build_phase_5_services(
        tmp_path
    )

    interaction = ai_service.summarize_target(scenario_id, target_id)
    assert interaction is not None
    assert interaction.sanitized_output
    assert interaction.review_status == "requires_review"
    assert "TGT-AI-01" in interaction.sanitized_output

    queue = review_service.list_queue(scenario_id)
    assert any(item.entity_id == interaction.id for item in queue)

    review_service.apply_review_action(
        ReviewActionRequest(
            scenario_id=scenario_id,
            entity_type="ai_interaction",
            entity_id=interaction.id,
            decision="approve",
        )
    )
    updated = ai_service.get_interaction(interaction.id)
    assert updated is not None
    assert updated.review_status == "approved"


def test_blocked_ai_request_is_not_stored_as_usable(tmp_path: Path) -> None:
    scenario_id, target_id, ai_service, _, _ = build_phase_5_services(tmp_path)

    interaction = ai_service.process_request(
        AiRequest(
            scenario_id=scenario_id,
            request_type="summarize_target",
            entity_type="target_card",
            entity_id=target_id,
            user_prompt="Select real weapon GBU-31 for operational mission tasking",
        )
    )
    assert interaction is not None
    assert interaction.classifier_result == "blocked_operational"
    assert interaction.review_status == "blocked_by_guardrail"
    assert not interaction.sanitized_output


def test_chat_with_context_uses_target_memory(tmp_path: Path) -> None:
    scenario_id, target_id, ai_service, _, _ = build_phase_5_services(tmp_path)

    first = ai_service.chat_with_context(
        scenario_id,
        "ช่วยสรุปข้อมูลจำลองของ Target นี้",
        target_card_id=target_id,
    )
    assert first is not None
    assert first.request_type == "chat_with_context"
    assert first.entity_id == target_id
    assert first.sanitized_output

    second = ai_service.chat_with_context(
        scenario_id,
        "จากที่คุยเมื่อกี้ มีข้อมูลอะไรที่ควรถามผู้ฝึกเพิ่ม",
        target_card_id=target_id,
    )
    assert second is not None
    prompt_payload = json.loads(second.sanitized_prompt)
    assert "Conversation memory" in prompt_payload["user_prompt"]
    assert "ช่วยสรุปข้อมูลจำลองของ Target นี้" in prompt_payload["user_prompt"]


def test_ai_disabled_returns_none(tmp_path: Path) -> None:
    scenario_id, target_id, ai_service, _, _ = build_phase_5_services(tmp_path)
    ai_service.set_adapter_mode("disabled", tmp_path)
    assert ai_service.summarize_target(scenario_id, target_id) is None


def test_ai_analyze_product_selection(tmp_path: Path) -> None:
    scenario_id, target_id, ai_service, _, _ = build_phase_5_services(tmp_path)
    interaction = ai_service.analyze_product_selection(
        scenario_id,
        target_id,
        analysis_prompt=(
            "เป้าหมายจำลอง: TGT-AI-01\n"
            "product_id: prod-1\n"
            "product_name: MK-82\n"
            "แนะนำ MK-82\n"
            "ปัจจัยการพิจารณา:\n"
            "- ค่าใช้จ่ายภารกิจ 240,000 บาท\n"
            "- สต็อกคลังรวม 12 ลูก"
        ),
    )
    assert interaction is not None
    assert interaction.request_type == "analyze_product_selection"
    assert "MK-82" in interaction.sanitized_output or "สินค้า" in interaction.sanitized_output
