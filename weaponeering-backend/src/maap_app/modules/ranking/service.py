from __future__ import annotations

from uuid import uuid4

from maap_app.modules.audit.service import AuditService
from maap_app.modules.common import ReviewStatus, clamp_score
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.logistics.scoring import READINESS_SCORES
from maap_app.modules.ranking.models import RankingRunResult
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.ranking.schemas import (
    CreateScoringProfileRequest,
    OverrideRankingRequest,
    RunRankingRequest,
)
from maap_app.modules.ranking.scoring import (
    RankingComponentScores,
    RankingWeights,
    calculate_ranking_score,
)
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.weaponeering.repository import WeaponeeringRepository


class RankingService:
    def __init__(
        self,
        repository: RankingRepository,
        target_repository: TargetRepository,
        weaponeering_repository: WeaponeeringRepository,
        logistics_repository: LogisticsRepository,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.target_repository = target_repository
        self.weaponeering_repository = weaponeering_repository
        self.logistics_repository = logistics_repository
        self.audit_service = audit_service

    def ensure_default_scoring_profile(self, scenario_id: str) -> str:
        active = self.repository.get_active_scoring_profile(scenario_id)
        if active:
            return active.id
        profiles = self.repository.list_scoring_profiles(scenario_id)
        if profiles:
            self.repository.clear_active_profiles(scenario_id)
            self.repository.set_active_profile(profiles[0].id)
            return profiles[0].id

        profile_id = str(uuid4())
        self.repository.insert_scoring_profile(
            profile_id=profile_id,
            scenario_id=scenario_id,
            name="Default Phase 4 Profile",
            ruleset_version="phase-1-baseline",
            priority_weight=20,
            weaponeering_weight=20,
            logistics_weight=20,
            readiness_weight=15,
            risk_weight=15,
            resource_balance_weight=10,
            is_active=1,
        )
        self.audit_service.record_event(
            actor="system",
            event_type="scoring_profile_created",
            entity_type="scoring_profile",
            entity_id=profile_id,
            details={"name": "Default Phase 4 Profile"},
        )
        return profile_id

    def create_scoring_profile(self, request: CreateScoringProfileRequest) -> str:
        profile_id = str(uuid4())
        self.repository.insert_scoring_profile(
            profile_id=profile_id,
            scenario_id=request.scenario_id,
            name=request.name,
            ruleset_version="phase-1-baseline",
            priority_weight=clamp_score(request.priority_weight, minimum=0, maximum=100),
            weaponeering_weight=clamp_score(
                request.weaponeering_weight, minimum=0, maximum=100
            ),
            logistics_weight=clamp_score(request.logistics_weight, minimum=0, maximum=100),
            readiness_weight=clamp_score(request.readiness_weight, minimum=0, maximum=100),
            risk_weight=clamp_score(request.risk_weight, minimum=0, maximum=100),
            resource_balance_weight=clamp_score(
                request.resource_balance_weight, minimum=0, maximum=100
            ),
            is_active=0,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="scoring_profile_created",
            entity_type="scoring_profile",
            entity_id=profile_id,
            details={"name": request.name},
        )
        return profile_id

    def set_active_scoring_profile(self, profile_id: str) -> None:
        profile = self.repository.get_scoring_profile(profile_id)
        if profile is None:
            raise ValueError("Scoring profile not found.")
        self.repository.clear_active_profiles(profile.scenario_id)
        self.repository.set_active_profile(profile_id)
        self.audit_service.record_event(
            actor="local_user",
            event_type="scoring_profile_updated",
            entity_type="scoring_profile",
            entity_id=profile_id,
            details={"is_active": True},
        )

    def list_scoring_profiles(self, scenario_id: str):
        return self.repository.list_scoring_profiles(scenario_id)

    def run_ranking(self, request: RunRankingRequest) -> RankingRunResult:
        profile_id = request.scoring_profile_id
        if profile_id is None:
            profile_id = self.ensure_default_scoring_profile(request.scenario_id)
        profile = self.repository.get_scoring_profile(profile_id)
        if profile is None:
            raise ValueError("Scoring profile not found.")

        logistics_score = self.logistics_repository.get_latest_plan_score(
            request.scenario_id
        )
        logistics_feasibility = (
            logistics_score.logistics_feasibility if logistics_score else None
        )

        platforms = self.logistics_repository.list_simulated_platforms(request.scenario_id)
        if platforms:
            readiness_values = [
                READINESS_SCORES.get(p.readiness_status, 50) for p in platforms
            ]
            readiness_score = sum(readiness_values) // len(readiness_values)
        else:
            readiness_score = None

        tokens = self.logistics_repository.list_resource_tokens(request.scenario_id)
        if tokens:
            token_avg = min(
                100,
                sum(min(100, t.quantity * 10) for t in tokens) // len(tokens),
            )
            resource_balance = token_avg
        else:
            resource_balance = None

        approved_assessments = (
            self.weaponeering_repository.list_approved_assessments_for_scenario(
                request.scenario_id
            )
        )
        assessments_by_target: dict[str, list] = {}
        for assessment in approved_assessments:
            assessments_by_target.setdefault(assessment.target_card_id, []).append(
                assessment
            )

        targets = self.target_repository.list_active_target_cards(request.scenario_id)
        run_id = str(uuid4())
        computed_items: list[tuple[str, int, int, str, dict, list[str]]] = []

        for target in targets:
            target_assessments = assessments_by_target.get(target.id, [])
            if target_assessments:
                best = max(
                    target_assessments,
                    key=lambda a: (a.suitability_score + a.feasibility_score) // 2,
                )
                weaponeering_fit = (
                    best.suitability_score + best.feasibility_score
                ) // 2
                risk_indicator = max(1, min(100, 100 - best.risk_score))
            else:
                weaponeering_fit = None
                risk_indicator = max(1, min(100, 100 - target.complexity_score))

            if resource_balance is None:
                resource_balance_target = max(
                    1, min(100, 100 - target.complexity_score)
                )
            else:
                resource_balance_target = resource_balance

            components = RankingComponentScores(
                priority_alignment=target.priority_score,
                weaponeering_fit=weaponeering_fit,
                logistics_feasibility=logistics_feasibility,
                readiness=readiness_score,
                resource_balance=resource_balance_target,
                risk_indicator=risk_indicator,
            )
            weights = RankingWeights(
                priority_weight=profile.priority_weight,
                weaponeering_weight=profile.weaponeering_weight,
                logistics_weight=profile.logistics_weight,
                readiness_weight=profile.readiness_weight,
                risk_weight=profile.risk_weight,
                resource_balance_weight=profile.resource_balance_weight,
            )
            total_score, confidence, rationale, breakdown, warnings = (
                calculate_ranking_score(components, weights)
            )
            breakdown["warnings"] = warnings
            computed_items.append(
                (target.id, total_score, confidence, rationale, breakdown, warnings)
            )

        computed_items.sort(key=lambda item: item[1], reverse=True)

        self.repository.insert_ranking_run(
            run_id=run_id,
            scenario_id=request.scenario_id,
            ruleset_version=request.ruleset_version,
            scoring_profile_id=profile_id,
            generated_by="local_user",
            run_status=ReviewStatus.REQUIRES_REVIEW,
            summary=f"Ranked {len(computed_items)} target card(s).",
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="ranking_run_created",
            entity_type="ranking_run",
            entity_id=run_id,
            details={"item_count": len(computed_items)},
        )

        for rank_order, (target_id, total_score, confidence, rationale, breakdown, _) in (
            enumerate(computed_items, start=1)
        ):
            item_id = str(uuid4())
            self.repository.insert_ranking_item(
                item_id=item_id,
                ranking_run_id=run_id,
                entity_type="target_card",
                entity_id=target_id,
                rank_order=rank_order,
                total_score=total_score,
                confidence_score=confidence,
                rationale=rationale,
                breakdown_json=self.repository.dumps_breakdown(breakdown),
                review_status=ReviewStatus.REQUIRES_REVIEW,
            )
            self.audit_service.record_event(
                actor="system",
                event_type="ranking_item_created",
                entity_type="ranking_item",
                entity_id=item_id,
                details={"target_card_id": target_id, "rank_order": rank_order},
            )

        run = self.repository.get_latest_ranking_run(request.scenario_id)
        assert run is not None
        items = self.repository.list_ranking_items(run.id)
        return RankingRunResult(run=run, items=items)

    def get_ranking_item(self, item_id: str):
        return self.repository.get_ranking_item(item_id)

    def get_latest_ranking(self, scenario_id: str) -> RankingRunResult | None:
        run = self.repository.get_latest_ranking_run(scenario_id)
        if run is None:
            return None
        items = self.repository.list_ranking_items(run.id)
        return RankingRunResult(run=run, items=items)

    def override_ranking_item(self, request: OverrideRankingRequest) -> None:
        item = self.repository.get_ranking_item(request.ranking_item_id)
        if item is None:
            raise ValueError("Ranking item not found.")

        run = self.repository.get_ranking_run(item.ranking_run_id)
        if run is None:
            raise ValueError("Ranking run not found.")

        self.repository.apply_ranking_override(
            item_id=request.ranking_item_id,
            override_rank_order=request.new_rank_order,
            override_notes=request.notes,
        )
        record_id = str(uuid4())
        self.target_repository.insert_review_record(
            record_id=record_id,
            scenario_id=run.scenario_id,
            entity_type="ranking_item",
            entity_id=request.ranking_item_id,
            reviewer=request.reviewer,
            decision="override",
            notes=request.notes,
        )
        self.audit_service.record_event(
            actor=request.reviewer,
            event_type="ranking_override_applied",
            entity_type="ranking_item",
            entity_id=request.ranking_item_id,
            details={
                "new_rank_order": request.new_rank_order,
                "original_rank_order": item.rank_order,
            },
        )

    def create_plan_draft_from_item(self, ranking_item_id: str) -> str:
        item = self.repository.get_ranking_item(ranking_item_id)
        if item is None:
            raise ValueError("Ranking item not found.")
        run = self.repository.get_ranking_run(item.ranking_run_id)
        if run is None:
            raise ValueError("Ranking run not found.")

        label = item.entity_label or item.entity_id
        plan_id = str(uuid4())
        self.repository.insert_plan_option(
            plan_id=plan_id,
            scenario_id=run.scenario_id,
            title=f"Draft plan for {label}",
            generated_by="local_user",
            review_status=ReviewStatus.DRAFT,
            rank_order=item.override_rank_order or item.rank_order,
        )

        option_id = None
        if item.entity_type == "target_card":
            assessments = self.weaponeering_repository.list_approved_assessments_for_scenario(
                run.scenario_id
            )
            for assessment in assessments:
                if assessment.target_card_id == item.entity_id:
                    option_id = assessment.abstract_weaponeering_option_id
                    break

        assignment_id = str(uuid4())
        self.repository.insert_plan_assignment(
            assignment_id=assignment_id,
            plan_option_id=plan_id,
            target_card_id=item.entity_id if item.entity_type == "target_card" else None,
            abstract_weaponeering_option_id=option_id,
            assignment_score=item.total_score,
            review_status=ReviewStatus.DRAFT,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="plan_option_draft_created",
            entity_type="plan_option",
            entity_id=plan_id,
            details={"ranking_item_id": ranking_item_id},
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="plan_assignment_draft_created",
            entity_type="plan_assignment",
            entity_id=assignment_id,
            details={"plan_option_id": plan_id},
        )
        return plan_id
