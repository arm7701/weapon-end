from __future__ import annotations

import json
from uuid import uuid4

from maap_app.config.ai_settings import AiSettings
from maap_app.modules.ai.adapter import create_adapter
from maap_app.modules.ai.classifier import classify_input, is_allowed_classifier_result
from maap_app.modules.ai.context import ContextBundle, ContextBundleBuilder
from maap_app.modules.ai.models import AiInteraction
from maap_app.modules.ai.repository import AiRepository
from maap_app.modules.ai.schemas import REQUEST_TYPES, AiRequest, AiResponsePayload
from maap_app.modules.ai.validator import validate_output
from maap_app.modules.audit.service import AuditService
from maap_app.modules.common import ReviewStatus
from maap_app.modules.guardrail.service import GuardrailService

_SIMULATION_FOOTER = "SIMULATION-ONLY TRAINING OUTPUT"


def _strip_simulation_footer(text: str) -> str:
    """Remove the simulation footer from stored assistant text before feeding it back as memory."""
    cleaned = text
    while cleaned.endswith(_SIMULATION_FOOTER):
        cleaned = cleaned[: -len(_SIMULATION_FOOTER)].rstrip()
    return cleaned


class AiAssistantService:
    def __init__(
        self,
        repository: AiRepository,
        context_builder: ContextBundleBuilder,
        guardrail_service: GuardrailService,
        audit_service: AuditService,
        ai_settings: AiSettings,
    ) -> None:
        self.repository = repository
        self.context_builder = context_builder
        self.guardrail_service = guardrail_service
        self.audit_service = audit_service
        self.ai_settings = ai_settings
        self._adapter = create_adapter(ai_settings)

    @property
    def adapter_mode(self) -> str:
        return self.ai_settings.adapter_mode

    def set_adapter_mode(self, mode: str, data_dir=None) -> None:
        self.ai_settings.adapter_mode = mode
        self.ai_settings.save(data_dir)
        self._adapter = create_adapter(self.ai_settings)

    def update_settings(self, settings: AiSettings, data_dir=None) -> None:
        self.ai_settings = settings
        self.ai_settings.save(data_dir)
        self._adapter = create_adapter(self.ai_settings)

    def toggle_guardrail(self, data_dir=None) -> bool:
        self.ai_settings.guardrail_enabled = not self.ai_settings.guardrail_enabled
        self.ai_settings.save(data_dir)
        return self.ai_settings.guardrail_enabled

    def toggle_chain_of_thought(self, data_dir=None) -> bool:
        self.ai_settings.enable_chain_of_thought = not self.ai_settings.enable_chain_of_thought
        self.ai_settings.save(data_dir)
        return self.ai_settings.enable_chain_of_thought

    def test_connection(self, settings: AiSettings) -> tuple[bool, str]:
        if settings.adapter_mode == "disabled":
            return False, "AI is disabled."
        if settings.adapter_mode == "rule_based":
            return True, "Rule-based local AI helper is available."
        adapter = create_adapter(settings)
        payload = adapter.generate(
            "generate_review_questions",
            ContextBundle(
                scenario={"name": "AI connection test"},
                missing_data=[],
            ),
            "สวัสดี",
        )
        if payload is None:
            return False, "AI adapter did not return a response."
        text = payload.to_text().strip()
        if "AI adapter request failed:" in text:
            return False, text
        return True, text[:500] or "AI adapter responded successfully."

    def is_enabled(self) -> bool:
        return self.ai_settings.adapter_mode != "disabled"

    def process_request(
        self,
        request: AiRequest,
        *,
        bundle_override: ContextBundle | None = None,
    ) -> AiInteraction | None:
        if request.request_type not in REQUEST_TYPES:
            raise ValueError(f"Unsupported AI request type: {request.request_type}")

        interaction_id = str(uuid4())
        self.audit_service.record_event(
            actor="local_user",
            event_type="ai_request_submitted",
            entity_type="ai_interaction",
            entity_id=interaction_id,
            details={"request_type": request.request_type},
        )

        if not self.is_enabled():
            return None

        classifier_input = f"{request.request_type}\n{request.user_prompt}"
        classifier_result = classify_input(classifier_input)
        if self.ai_settings.guardrail_enabled and not is_allowed_classifier_result(classifier_result):
            self.guardrail_service.validate_training_text(
                text=classifier_input,
                entity_type="ai_request",
                entity_id=interaction_id,
            )
            self.repository.insert_interaction(
                interaction_id=interaction_id,
                scenario_id=request.scenario_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                request_type=request.request_type,
                sanitized_prompt=classifier_input[:500],
                sanitized_output="",
                classifier_result=classifier_result,
                validator_result="blocked_input",
                review_status=ReviewStatus.BLOCKED_BY_GUARDRAIL,
            )
            self.audit_service.record_event(
                actor="system",
                event_type="ai_output_blocked",
                entity_type="ai_interaction",
                entity_id=interaction_id,
                details={"reason": "classifier_blocked"},
            )
            return self.repository.get_interaction(interaction_id)

        if bundle_override is not None:
            bundle = bundle_override
        else:
            target_id = request.entity_id if request.entity_type == "target_card" else None
            ranking_id = request.entity_id if request.entity_type == "ranking_item" else None
            bundle = self.context_builder.build(
                request.scenario_id,
                target_card_id=target_id,
                ranking_item_id=ranking_id,
            )

        if self.ai_settings.guardrail_enabled and not self.guardrail_service.validate_training_text(
            text=bundle.to_json(),
            entity_type="ai_context_bundle",
            entity_id=interaction_id,
        ):
            self.repository.insert_interaction(
                interaction_id=interaction_id,
                scenario_id=request.scenario_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                request_type=request.request_type,
                sanitized_prompt=bundle.to_json()[:500],
                sanitized_output="",
                classifier_result=classifier_result,
                validator_result="blocked_context",
                review_status=ReviewStatus.BLOCKED_BY_GUARDRAIL,
            )
            self.audit_service.record_event(
                actor="system",
                event_type="ai_output_blocked",
                entity_type="ai_interaction",
                entity_id=interaction_id,
                details={"reason": "context_guardrail"},
            )
            return self.repository.get_interaction(interaction_id)

        sanitized_prompt = json.dumps(
            {
                "request_type": request.request_type,
                "user_prompt": request.user_prompt[:1600],
            },
            ensure_ascii=False,
        )

        payload = self._adapter.generate(
            request.request_type,
            bundle,
            request.user_prompt,
        )
        if payload is None:
            return None

        output_text = payload.to_text()
        allowed, validator_result = validate_output(output_text)
        if self.ai_settings.guardrail_enabled and not allowed:
            self.guardrail_service.validate_training_text(
                text=output_text,
                entity_type="ai_output",
                entity_id=interaction_id,
            )
            self.repository.insert_interaction(
                interaction_id=interaction_id,
                scenario_id=request.scenario_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                request_type=request.request_type,
                sanitized_prompt=sanitized_prompt,
                sanitized_output="",
                classifier_result=classifier_result,
                validator_result=validator_result,
                review_status=ReviewStatus.BLOCKED_BY_GUARDRAIL,
            )
            self.audit_service.record_event(
                actor="system",
                event_type="ai_output_blocked",
                entity_type="ai_interaction",
                entity_id=interaction_id,
                details={"reason": validator_result},
            )
            return self.repository.get_interaction(interaction_id)

        review_status = (
            ReviewStatus.REQUIRES_REVIEW if payload.review_required else ReviewStatus.DRAFT
        )
        self.repository.insert_interaction(
            interaction_id=interaction_id,
            scenario_id=request.scenario_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            request_type=request.request_type,
            sanitized_prompt=sanitized_prompt,
            sanitized_output=output_text[:4000],
            classifier_result=classifier_result,
            validator_result=validator_result,
            review_status=review_status,
        )
        self.audit_service.record_event(
            actor="system",
            event_type="ai_output_stored",
            entity_type="ai_interaction",
            entity_id=interaction_id,
            details={"request_type": request.request_type},
        )
        if review_status == ReviewStatus.REQUIRES_REVIEW:
            self.audit_service.record_event(
                actor="system",
                event_type="ai_output_queued_for_review",
                entity_type="ai_interaction",
                entity_id=interaction_id,
                details={},
            )
        return self.repository.get_interaction(interaction_id)

    def chat_with_context(
        self,
        scenario_id: str,
        message: str,
        *,
        target_card_id: str | None = None,
        memory_limit: int = 8,
    ) -> AiInteraction | None:
        clean_message = message.strip()
        if not clean_message:
            raise ValueError("Chat message is required.")

        if target_card_id is None:
            char_limit = (
                8_000 if self.ai_settings.adapter_mode == "local_model" else 40_000
            )
            memory = self._build_cross_thread_memory(scenario_id, char_limit=char_limit)
            bundle_override = self.context_builder.build_for_scenario_chat(scenario_id)
        else:
            memory = self._build_chat_memory(
                scenario_id,
                target_card_id=target_card_id,
                limit=memory_limit,
            )
            bundle_override = None

        prompt_parts = ["Current user message:\n" + clean_message]
        if memory:
            prompt_parts.append(
                "Conversation memory from previous local interactions:\n" + memory
            )
        return self.process_request(
            AiRequest(
                scenario_id=scenario_id,
                request_type="chat_with_context",
                entity_type="target_card" if target_card_id else "",
                entity_id=target_card_id or "",
                user_prompt="\n\n".join(prompt_parts),
            ),
            bundle_override=bundle_override,
        )

    def clear_scenario_memory(self, scenario_id: str) -> None:
        self.repository.delete_by_scenario(scenario_id)

    def clear_chat_memory(self, scenario_id: str, target_card_id: str | None = None) -> None:
        entity_id = target_card_id if target_card_id else ""
        self.repository.delete_by_entity(scenario_id, entity_id)

    def record_target_deleted_event(
        self,
        scenario_id: str,
        target_label: str,
    ) -> None:
        """Inject a system notification into scenario chat history when a target is deleted."""
        try:
            active_cards = self.context_builder.target_repository.list_active_target_cards(
                scenario_id
            )
            remaining_labels = [c.label for c in active_cards]
        except Exception:
            remaining_labels = []
        remaining = ", ".join(remaining_labels) if remaining_labels else "none"
        sanitized_prompt = json.dumps(
            {
                "request_type": "system_event",
                "user_prompt": "Current user message:\n[System] Target card deleted",
            },
            ensure_ascii=False,
        )
        sanitized_output = (
            f"[System] Target '{target_label}' has been deleted from this scenario."
            f" Currently active targets: {remaining}."
            f"\n{_SIMULATION_FOOTER}"
        )
        self.repository.insert_interaction(
            interaction_id=str(uuid4()),
            scenario_id=scenario_id,
            entity_type="",
            entity_id="",
            request_type="system_event",
            sanitized_prompt=sanitized_prompt,
            sanitized_output=sanitized_output,
            classifier_result="safe_training",
            validator_result="pass",
            review_status=ReviewStatus.DRAFT,
        )

    def _build_cross_thread_memory(
        self,
        scenario_id: str,
        char_limit: int = 40_000,
    ) -> str:
        """Load ALL interactions for a scenario across all threads, tagged by origin."""
        id_to_label: dict[str, str] = {}
        try:
            for card in self.context_builder.target_repository.list_active_target_cards(scenario_id):
                id_to_label[card.id] = card.label
        except Exception:
            pass

        interactions = self.repository.list_all_interactions_for_scenario(scenario_id)

        memory_lines: list[str] = []
        for item in interactions:
            if item.entity_type == "target_card" and item.entity_id and item.entity_id not in id_to_label:
                continue
            if item.entity_type == "target_card" and item.entity_id:
                target_label = id_to_label.get(item.entity_id, item.entity_id[:8])
                thread_tag = f"[Thread: Target {target_label}]"
            else:
                thread_tag = "[Thread: Scenario Chat]"

            user_text = self._extract_clean_user_message(item.sanitized_prompt)
            assistant_text = _strip_simulation_footer(item.sanitized_output.strip())
            if not user_text or not assistant_text:
                continue

            ts = item.created_at or item.request_type
            memory_lines.append(f"[{ts}] User: {thread_tag} {user_text[:500]}")
            memory_lines.append(f"[{ts}] Assistant: {thread_tag} {assistant_text[:700]}")

        full_text = "\n".join(memory_lines)
        if len(full_text) > char_limit:
            return full_text[-char_limit:]
        return full_text

    def _build_chat_memory(
        self,
        scenario_id: str,
        *,
        target_card_id: str | None,
        limit: int,
    ) -> str:
        interactions = self.repository.list_interactions(scenario_id)
        if target_card_id:
            interactions = [
                item
                for item in interactions
                if item.entity_type == "target_card" and item.entity_id == target_card_id
            ]
        else:
            interactions = [item for item in interactions if not item.entity_id]

        memory_lines: list[str] = []
        for item in reversed(interactions[:limit]):
            user_text = self._extract_clean_user_message(item.sanitized_prompt)
            assistant_text = _strip_simulation_footer(item.sanitized_output.strip())
            if not user_text or not assistant_text:
                continue
            label = item.created_at or item.request_type
            memory_lines.append(f"[{label}] User: {user_text[:500] or item.request_type}")
            memory_lines.append(f"[{label}] Assistant: {assistant_text[:700]}")
        return "\n".join(memory_lines)[-6000:]

    def _extract_clean_user_message(self, sanitized_prompt: str) -> str:
        """Extract only the actual user question, stripping embedded old memory."""
        raw = self._extract_user_prompt(sanitized_prompt)
        marker = "Current user message:"
        if marker in raw:
            raw = raw.split(marker, 1)[1].strip()
            memory_marker = "Conversation memory from previous local interactions:"
            if memory_marker in raw:
                raw = raw.split(memory_marker, 1)[0].strip()
        return raw

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

    def summarize_target(self, scenario_id: str, target_card_id: str) -> AiInteraction | None:
        return self.process_request(
            AiRequest(
                scenario_id=scenario_id,
                request_type="summarize_target",
                entity_type="target_card",
                entity_id=target_card_id,
            )
        )

    def identify_missing_data(
        self,
        scenario_id: str,
        target_card_id: str | None = None,
    ) -> AiInteraction | None:
        return self.process_request(
            AiRequest(
                scenario_id=scenario_id,
                request_type="identify_missing_data",
                entity_type="target_card" if target_card_id else "",
                entity_id=target_card_id or "",
            )
        )

    def suggest_abstract_option(
        self,
        scenario_id: str,
        target_card_id: str,
    ) -> AiInteraction | None:
        return self.process_request(
            AiRequest(
                scenario_id=scenario_id,
                request_type="suggest_abstract_option",
                entity_type="target_card",
                entity_id=target_card_id,
            )
        )

    def explain_ranking(
        self,
        scenario_id: str,
        ranking_item_id: str,
    ) -> AiInteraction | None:
        return self.process_request(
            AiRequest(
                scenario_id=scenario_id,
                request_type="explain_ranking",
                entity_type="ranking_item",
                entity_id=ranking_item_id,
            )
        )

    def draft_plan_summary(
        self,
        scenario_id: str,
        ranking_item_id: str,
    ) -> AiInteraction | None:
        return self.process_request(
            AiRequest(
                scenario_id=scenario_id,
                request_type="draft_plan_summary",
                entity_type="ranking_item",
                entity_id=ranking_item_id,
            )
        )

    def generate_review_questions(self, scenario_id: str) -> AiInteraction | None:
        return self.process_request(
            AiRequest(
                scenario_id=scenario_id,
                request_type="generate_review_questions",
            )
        )

    def analyze_product_selection(
        self,
        scenario_id: str,
        target_card_id: str,
        *,
        analysis_prompt: str,
    ) -> AiInteraction | None:
        return self.process_request(
            AiRequest(
                scenario_id=scenario_id,
                request_type="analyze_product_selection",
                entity_type="target_card",
                entity_id=target_card_id,
                user_prompt=analysis_prompt,
            )
        )

    def get_interaction(self, interaction_id: str) -> AiInteraction | None:
        return self.repository.get_interaction(interaction_id)

    def list_interactions(self, scenario_id: str) -> list[AiInteraction]:
        return self.repository.list_interactions(scenario_id)

    @staticmethod
    def parse_output_payload(text: str) -> AiResponsePayload:
        return AiResponsePayload(summary=text)
