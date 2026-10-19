from __future__ import annotations

from uuid import uuid4

from maap_app.modules.ai.repository import AiRepository
from maap_app.modules.ai.models import AiInteraction
from maap_app.modules.audit.service import AuditService
from maap_app.modules.common import ReviewStatus
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.review.models import ReviewQueueItem
from maap_app.modules.review.schemas import ReviewActionRequest
from maap_app.modules.target.models import TargetCard
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.weaponeering.repository import WeaponeeringRepository


DECISION_TO_STATUS = {
    "approve": ReviewStatus.APPROVED,
    "reject": ReviewStatus.REJECTED,
    "needs_revision": ReviewStatus.REQUIRES_REVIEW,
}


class HumanReviewService:
    def __init__(
        self,
        target_repository: TargetRepository,
        ai_repository: AiRepository,
        weaponeering_repository: WeaponeeringRepository,
        ranking_repository: RankingRepository,
        audit_service: AuditService,
    ) -> None:
        self.target_repository = target_repository
        self.ai_repository = ai_repository
        self.weaponeering_repository = weaponeering_repository
        self.ranking_repository = ranking_repository
        self.audit_service = audit_service

    def list_queue(self, scenario_id: str) -> list[ReviewQueueItem]:
        items: list[ReviewQueueItem] = []

        for interaction in self.ai_repository.list_pending_review(scenario_id):
            items.append(
                ReviewQueueItem(
                    entity_type="ai_interaction",
                    entity_id=interaction.id,
                    source=interaction.request_type,
                    label=interaction.request_type.replace("_", " "),
                    review_status=interaction.review_status,
                    created_at=interaction.created_at or "",
                    is_blocked=interaction.review_status
                    == ReviewStatus.BLOCKED_BY_GUARDRAIL,
                )
            )

        for assessment in self.weaponeering_repository.list_assessments_requiring_review(
            scenario_id
        ):
            items.append(
                ReviewQueueItem(
                    entity_type="target_weaponeering_assessment",
                    entity_id=assessment.id,
                    source=assessment.generated_by,
                    label=f"Assessment {assessment.id[:8]}",
                    review_status=assessment.review_status,
                    created_at="",
                )
            )

        for ranking_item in self.ranking_repository.list_items_requiring_review(
            scenario_id
        ):
            label = ranking_item.entity_label or ranking_item.entity_id[:8]
            if ranking_item.override_rank_order:
                label += " (override)"
            items.append(
                ReviewQueueItem(
                    entity_type="ranking_item",
                    entity_id=ranking_item.id,
                    source="ranking_engine",
                    label=label,
                    review_status=ranking_item.review_status,
                    created_at="",
                )
            )

        return items

    def list_targets(self, scenario_id: str) -> list[TargetCard]:
        return self.target_repository.list_active_target_cards(scenario_id)

    def list_ai_interactions(
        self,
        scenario_id: str,
        target_id: str | None = None,
    ) -> list[AiInteraction]:
        interactions = self.ai_repository.list_interactions(scenario_id)
        if target_id:
            interactions = [
                item
                for item in interactions
                if item.entity_type == "target_card" and item.entity_id == target_id
            ]
        else:
            interactions = [item for item in interactions if not item.entity_id]
        return interactions

    def list_all_ai_interactions(self, scenario_id: str) -> list[AiInteraction]:
        """All interactions for a scenario across every thread, ordered chronologically."""
        return self.ai_repository.list_all_interactions_for_scenario(scenario_id)

    def get_ai_interaction(self, interaction_id: str) -> AiInteraction | None:
        return self.ai_repository.get_interaction(interaction_id)

    def apply_review_action(self, request: ReviewActionRequest) -> str:
        if request.decision == "needs_revision" and not request.notes.strip():
            raise ValueError("Reviewer notes are required for revision requests.")

        review_status = DECISION_TO_STATUS.get(request.decision)
        if review_status is None:
            raise ValueError(f"Unsupported review decision: {request.decision}")

        record_id = str(uuid4())
        self.target_repository.insert_review_record(
            record_id=record_id,
            scenario_id=request.scenario_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            reviewer=request.reviewer,
            decision=request.decision,
            notes=request.notes,
        )

        if request.entity_type == "ai_interaction":
            self.ai_repository.update_review_status(request.entity_id, review_status)
        elif request.entity_type == "target_weaponeering_assessment":
            self.weaponeering_repository.update_assessment_review_status(
                request.entity_id,
                review_status,
            )
        elif request.entity_type == "target_card":
            card = self.target_repository.get_target_card(request.entity_id)
            if card:
                self.target_repository.update_review_status(
                    request.entity_id,
                    review_status,
                )
        elif request.entity_type == "ranking_item":
            self.ranking_repository.update_item_review_status(
                request.entity_id,
                review_status,
            )

        self.audit_service.record_event(
            actor=request.reviewer,
            event_type="ai_review_decision_recorded",
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            details={"decision": request.decision},
        )
        return record_id

    def get_item_detail(self, entity_type: str, entity_id: str) -> str:
        if entity_type == "ai_interaction":
            item = self.ai_repository.get_interaction(entity_id)
            if item:
                return item.sanitized_output or item.sanitized_prompt
        elif entity_type == "target_weaponeering_assessment":
            with self.weaponeering_repository.database.connect() as connection:
                row = connection.execute(
                    """
                    SELECT rationale, suitability_score, feasibility_score, risk_score,
                           review_status
                    FROM target_weaponeering_assessments
                    WHERE id = ?
                    """,
                    (entity_id,),
                ).fetchone()
            if row:
                return (
                    f"Rationale: {row['rationale']}\n"
                    f"Suitability: {row['suitability_score']} | "
                    f"Feasibility: {row['feasibility_score']} | "
                    f"Risk: {row['risk_score']}\n"
                    f"Status: {row['review_status']}"
                )
        elif entity_type == "ranking_item":
            item = self.ranking_repository.get_ranking_item(entity_id)
            if item:
                return f"{item.rationale}\nScore: {item.total_score}/100"
        return "No detail available."
