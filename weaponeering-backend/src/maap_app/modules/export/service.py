from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from maap_app.modules.ai.repository import AiRepository
from maap_app.modules.ai.validator import validate_output
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.export.formatters import to_csv, to_json_package, to_markdown
from maap_app.modules.export.models import (
    AarActionItem,
    ExportPackage,
    ExportReadinessResult,
    RankingComparisonResult,
    RankingComparisonRow,
    ReplayDifference,
    ReplayResult,
    SIMULATION_LABEL,
)
from maap_app.modules.export.repository import ExportRepository
from maap_app.modules.export.schemas import (
    EXPORT_FORMATS,
    EXPORT_TYPES,
    RANKING_EXPORT_TYPES,
    CompareRankingRequest,
    CreateExportRequest,
    ExportReadinessRequest,
    ReplayRankingRequest,
    UpdateActionItemRequest,
)
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.ranking.schemas import RunRankingRequest
from maap_app.modules.ranking.service import RankingService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.weaponeering.repository import WeaponeeringRepository


class ExportService:
    def __init__(
        self,
        repository: ExportRepository,
        scenario_repository: ScenarioRepository,
        target_repository: TargetRepository,
        weaponeering_repository: WeaponeeringRepository,
        logistics_repository: LogisticsRepository,
        ranking_repository: RankingRepository,
        ranking_service: RankingService,
        ai_repository: AiRepository,
        audit_repository: AuditRepository,
        guardrail_repository: GuardrailRepository,
        guardrail_service: GuardrailService,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.scenario_repository = scenario_repository
        self.target_repository = target_repository
        self.weaponeering_repository = weaponeering_repository
        self.logistics_repository = logistics_repository
        self.ranking_repository = ranking_repository
        self.ranking_service = ranking_service
        self.ai_repository = ai_repository
        self.audit_repository = audit_repository
        self.guardrail_repository = guardrail_repository
        self.guardrail_service = guardrail_service
        self.audit_service = audit_service

    def check_readiness(self, request: ExportReadinessRequest) -> ExportReadinessResult:
        blockers: list[str] = []
        warnings: list[str] = []

        if request.export_type not in EXPORT_TYPES:
            blockers.append(f"Unsupported export type: {request.export_type}")

        scenario = self.scenario_repository.get_scenario(request.scenario_id)
        if scenario is None:
            blockers.append("Scenario not found.")

        pending_ai = [
            i
            for i in self.ai_repository.list_interactions(request.scenario_id)
            if i.review_status == "requires_review"
        ]
        if pending_ai and request.export_type in ("full_package", "aar_summary"):
            blockers.append(
                f"{len(pending_ai)} AI interaction(s) still require review."
            )

        blocked_ai = [
            i
            for i in self.ai_repository.list_interactions(request.scenario_id)
            if i.review_status == "blocked_by_guardrail"
        ]
        if blocked_ai:
            warnings.append(
                f"{len(blocked_ai)} guardrail-blocked AI record(s) will be excluded."
            )

        blocked_targets = [
            c
            for c in self.target_repository.list_active_target_cards(request.scenario_id)
            if c.review_status == "blocked_by_guardrail"
        ]
        if blocked_targets:
            warnings.append(
                f"{len(blocked_targets)} guardrail-blocked target(s) will be excluded."
            )

        if request.export_type in RANKING_EXPORT_TYPES:
            run = self.ranking_repository.get_latest_ranking_run(request.scenario_id)
            if run is None:
                blockers.append("No ranking run exists for ranking export.")

        if not scenario and "Scenario not found" not in blockers:
            pass
        elif scenario and not self.target_repository.list_active_target_cards(
            request.scenario_id
        ):
            warnings.append("No active Target Cards in scenario.")

        self.audit_service.record_event(
            actor="local_user",
            event_type="export_readiness_checked",
            entity_type="scenario",
            entity_id=request.scenario_id,
            details={"export_type": request.export_type, "ready": not blockers},
        )
        return ExportReadinessResult(
            ready=not blockers,
            blockers=blockers,
            warnings=warnings,
        )

    def create_export(self, request: CreateExportRequest) -> ExportPackage:
        package_id = str(uuid4())
        readiness = self.check_readiness(
            ExportReadinessRequest(
                scenario_id=request.scenario_id,
                export_type=request.export_type,
            )
        )
        if not readiness.ready:
            reason = "; ".join(readiness.blockers)
            self.repository.insert_export_package(
                package_id=package_id,
                scenario_id=request.scenario_id,
                export_type=request.export_type,
                export_status="blocked",
                destination_path="",
                blocked_reason=reason,
                created_by=request.created_by,
            )
            self.guardrail_service.validate_training_text(
                text=reason,
                entity_type="export_package",
                entity_id=package_id,
            )
            self.audit_service.record_event(
                actor="local_user",
                event_type="export_blocked",
                entity_type="export_package",
                entity_id=package_id,
                details={"reason": reason},
            )
            return self._get_package(package_id)

        if request.export_format not in EXPORT_FORMATS:
            raise ValueError(f"Unsupported export format: {request.export_format}")

        scenario = self.scenario_repository.get_scenario(request.scenario_id)
        assert scenario is not None
        ranking_run = self._resolve_ranking_run(request)
        sections = self._gather_sections(request.scenario_id, ranking_run)
        selected = self._select_sections(request.export_type, sections)

        content_text = self._render_content(
            request.export_type,
            request.export_format,
            scenario.name,
            selected,
            manifest_base={
                "package_id": package_id,
                "scenario_id": request.scenario_id,
                "scenario_name": scenario.name,
                "export_type": request.export_type,
                "export_format": request.export_format,
                "ruleset_version": scenario.ruleset_version,
                "ranking_run_id": ranking_run.id if ranking_run else None,
                "review_gate_status": "passed" if readiness.ready else "blocked",
                "guardrail_validation": "passed",
                "created_by": request.created_by,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        allowed, validator_result = validate_output(content_text)
        if not allowed:
            self.repository.insert_export_package(
                package_id=package_id,
                scenario_id=request.scenario_id,
                export_type=request.export_type,
                export_status="blocked",
                destination_path="",
                blocked_reason=validator_result,
                created_by=request.created_by,
            )
            self.audit_service.record_event(
                actor="system",
                event_type="export_blocked",
                entity_type="export_package",
                entity_id=package_id,
                details={"reason": validator_result},
            )
            return self._get_package(package_id)

        request.destination_dir.mkdir(parents=True, exist_ok=True)
        filename = self._build_filename(
            scenario.name,
            request.export_type,
            ranking_run.id if ranking_run else None,
            request.export_format,
        )
        destination = request.destination_dir / filename
        if destination.exists():
            destination = request.destination_dir / f"{destination.stem}_dup{destination.suffix}"

        if request.export_type == "full_package":
            destination.mkdir(exist_ok=True)
            files_written: list[str] = []
            for section_name, section_data in selected.items():
                section_path = destination / f"{section_name}.md"
                section_path.write_text(
                    to_markdown(section_name, {section_name: section_data}),
                    encoding="utf-8",
                )
                files_written.append(section_path.name)
            manifest_path = destination / "manifest.json"
            manifest = {
                "package_id": package_id,
                "scenario_id": request.scenario_id,
                "scenario_name": scenario.name,
                "export_type": request.export_type,
                "export_format": "json",
                "ruleset_version": scenario.ruleset_version,
                "ranking_run_id": ranking_run.id if ranking_run else None,
                "review_gate_status": "passed",
                "guardrail_validation": validator_result,
                "simulation_label": SIMULATION_LABEL,
                "files": files_written,
            }
            manifest_path.write_text(
                to_json_package(manifest, selected),
                encoding="utf-8",
            )
            destination_path = str(destination)
        else:
            destination.write_text(content_text, encoding="utf-8")
            destination_path = str(destination)

        self.repository.insert_export_package(
            package_id=package_id,
            scenario_id=request.scenario_id,
            export_type=request.export_type,
            export_status="exported",
            destination_path=destination_path,
            blocked_reason="",
            created_by=request.created_by,
        )
        self.audit_service.record_event(
            actor=request.created_by,
            event_type="export_completed",
            entity_type="export_package",
            entity_id=package_id,
            details={"path": destination_path, "type": request.export_type},
        )
        return self._get_package(package_id)

    def list_exports(self, scenario_id: str) -> list[ExportPackage]:
        return self.repository.list_export_packages(scenario_id)

    def compare_ranking_runs(
        self,
        request: CompareRankingRequest,
    ) -> RankingComparisonResult:
        items_a = {
            i.entity_id: i
            for i in self.ranking_repository.list_ranking_items(request.run_a_id)
        }
        items_b = {
            i.entity_id: i
            for i in self.ranking_repository.list_ranking_items(request.run_b_id)
        }
        entity_ids = sorted(set(items_a) | set(items_b))
        rows: list[RankingComparisonRow] = []
        changed = 0
        for entity_id in entity_ids:
            a = items_a.get(entity_id)
            b = items_b.get(entity_id)
            rank_a = (a.override_rank_order or a.rank_order) if a else None
            rank_b = (b.override_rank_order or b.rank_order) if b else None
            score_a = a.total_score if a else None
            score_b = b.total_score if b else None
            rank_delta = (rank_b - rank_a) if rank_a is not None and rank_b is not None else None
            score_delta = (score_b - score_a) if score_a is not None and score_b is not None else None
            if rank_delta not in (None, 0) or score_delta not in (None, 0):
                changed += 1
            label = (a.entity_label if a else None) or (b.entity_label if b else entity_id)
            rows.append(
                RankingComparisonRow(
                    entity_id=entity_id,
                    entity_label=label or entity_id,
                    run_a_rank=rank_a,
                    run_b_rank=rank_b,
                    run_a_score=score_a,
                    run_b_score=score_b,
                    score_delta=score_delta,
                    rank_delta=rank_delta,
                )
            )
        summary = f"Compared {len(rows)} entities; {changed} changed rank or score."
        self.audit_service.record_event(
            actor="local_user",
            event_type="ranking_run_compared",
            entity_type="ranking_run",
            entity_id=request.run_a_id,
            details={"run_b_id": request.run_b_id, "changed": changed},
        )
        return RankingComparisonResult(
            run_a_id=request.run_a_id,
            run_b_id=request.run_b_id,
            rows=rows,
            summary=summary,
        )

    def replay_ranking(self, request: ReplayRankingRequest) -> ReplayResult:
        original = self.ranking_repository.get_ranking_run(request.ranking_run_id)
        if original is None:
            raise ValueError("Ranking run not found.")

        replay = self.ranking_service.run_ranking(
            RunRankingRequest(
                scenario_id=request.scenario_id,
                scoring_profile_id=original.scoring_profile_id,
                ruleset_version=original.ruleset_version,
            )
        )
        original_items = {
            i.entity_id: i
            for i in self.ranking_repository.list_ranking_items(original.id)
        }
        replay_items = {i.entity_id: i for i in replay.items}
        differences: list[ReplayDifference] = []
        for entity_id, orig in original_items.items():
            new = replay_items.get(entity_id)
            if new is None:
                differences.append(
                    ReplayDifference(
                        entity_id=entity_id,
                        entity_label=orig.entity_label or entity_id,
                        original_rank=orig.override_rank_order or orig.rank_order,
                        replay_rank=-1,
                        original_score=orig.total_score,
                        replay_score=-1,
                        explanation="Entity missing from replay run.",
                    )
                )
                continue
            orig_rank = orig.override_rank_order or orig.rank_order
            new_rank = new.override_rank_order or new.rank_order
            if orig_rank != new_rank or orig.total_score != new.total_score:
                explanation = self._replay_explanation(orig, new)
                differences.append(
                    ReplayDifference(
                        entity_id=entity_id,
                        entity_label=orig.entity_label or entity_id,
                        original_rank=orig_rank,
                        replay_rank=new_rank,
                        original_score=orig.total_score,
                        replay_score=new.total_score,
                        explanation=explanation,
                    )
                )
        summary = (
            f"Replay produced {len(replay.items)} items; "
            f"{len(differences)} difference(s) from original run."
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="ranking_replay_executed",
            entity_type="ranking_run",
            entity_id=original.id,
            details={"replay_run_id": replay.run.id, "differences": len(differences)},
        )
        return ReplayResult(
            original_run_id=original.id,
            replay_run_id=replay.run.id,
            differences=differences,
            summary=summary,
        )

    def generate_aar(self, scenario_id: str) -> tuple[str, list[AarActionItem]]:
        sections = self._gather_sections(scenario_id, None)
        aar_sections = {
            "Scenario Overview": sections.get("scenario_brief", {}),
            "Target Recognition": sections.get("target_list", []),
            "Weaponeering": sections.get("weaponeering_summary", []),
            "Logistics": sections.get("logistics_summary", {}),
            "Ranking": sections.get("ranking_table", []),
            "Instructor Notes": sections.get("instructor_notes", []),
            "Audit Summary": sections.get("audit_summary", []),
            "AI Interactions": [
                {
                    "request_type": i.request_type,
                    "review_status": i.review_status,
                }
                for i in self.ai_repository.list_interactions(scenario_id)[:10]
            ],
            "Guardrail Events": sections.get("guardrail_summary", []),
            "Export History": [
                {"type": p.export_type, "status": p.export_status}
                for p in self.repository.list_export_packages(scenario_id)[:10]
            ],
        }
        text = to_markdown("After-Action Review Summary", aar_sections)
        action_items = self._generate_action_items(scenario_id, sections)
        self.audit_service.record_event(
            actor="local_user",
            event_type="aar_generated",
            entity_type="scenario",
            entity_id=scenario_id,
            details={"action_items": len(action_items)},
        )
        return text, action_items

    def list_action_items(self, scenario_id: str) -> list[AarActionItem]:
        return self.repository.list_action_items(scenario_id)

    def update_action_item(self, request: UpdateActionItemRequest) -> None:
        if request.status not in ("open", "accepted", "dismissed"):
            raise ValueError("Invalid action item status.")
        self.repository.update_action_item_status(request.action_item_id, request.status)

    def _get_package(self, package_id: str) -> ExportPackage:
        with self.repository.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, export_type, export_status,
                       destination_path, blocked_reason, created_by, created_at
                FROM export_packages WHERE id = ?
                """,
                (package_id,),
            ).fetchone()
        if row is None:
            raise ValueError("Export package not found.")
        return ExportPackage(**dict(row))

    def _resolve_ranking_run(self, request: CreateExportRequest):
        if request.ranking_run_id:
            return self.ranking_repository.get_ranking_run(request.ranking_run_id)
        return self.ranking_repository.get_latest_ranking_run(request.scenario_id)

    def _gather_sections(self, scenario_id: str, ranking_run) -> dict:
        scenario = self.scenario_repository.get_scenario(scenario_id)
        objectives = self.scenario_repository.list_learning_objectives(scenario_id)
        targets = []
        for card in self.target_repository.list_active_target_cards(scenario_id):
            if card.review_status == "blocked_by_guardrail":
                continue
            recognition = self.target_repository.get_latest_recognition(card.id)
            targets.append(
                {
                    "label": card.label,
                    "priority_score": card.priority_score,
                    "complexity_score": card.complexity_score,
                    "recognition_confidence": (
                        recognition.recognition_confidence_score if recognition else None
                    ),
                    "review_status": card.review_status,
                    "missing_data_warnings": (
                        TargetRepository.parse_missing_data(recognition.missing_data_json)
                        if recognition
                        else ["No recognition result"]
                    ),
                }
            )

        weaponeering_rows = []
        for option in self.weaponeering_repository.list_abstract_options(scenario_id):
            weaponeering_rows.append(
                {
                    "option_label": option.option_label,
                    "effect_category": option.effect_category,
                    "capability_band": option.required_capability_band,
                    "abstract_effect_score": option.estimated_effect_score,
                    "risk_score": option.risk_score,
                    "logistics_demand_score": option.logistics_demand_score,
                    "review_status": option.review_status,
                }
            )
        for assessment in self.weaponeering_repository.list_assessments_requiring_review(
            scenario_id
        ):
            if assessment.review_status == "blocked_by_guardrail":
                continue
            weaponeering_rows.append(
                {
                    "assessment_id": assessment.id[:8],
                    "suitability_score": assessment.suitability_score,
                    "feasibility_score": assessment.feasibility_score,
                    "risk_score": assessment.risk_score,
                    "rationale": assessment.rationale[:120],
                    "review_status": assessment.review_status,
                }
            )

        plan_score = self.logistics_repository.get_latest_plan_score(scenario_id)
        logistics = {
            "organization_count": len(
                self.logistics_repository.list_organizations(scenario_id)
            ),
            "platform_count": len(
                self.logistics_repository.list_simulated_platforms(scenario_id)
            ),
            "depot_count": len(self.logistics_repository.list_depots(scenario_id)),
            "logistics_feasibility": (
                plan_score.logistics_feasibility if plan_score else None
            ),
            "logistics_rationale": plan_score.rationale if plan_score else "",
        }

        ranking_rows = []
        scorecard_rows = []
        if ranking_run:
            profile = None
            if ranking_run.scoring_profile_id:
                profile = self.ranking_repository.get_scoring_profile(
                    ranking_run.scoring_profile_id
                )
            for item in self.ranking_repository.list_ranking_items(ranking_run.id):
                if item.review_status == "blocked_by_guardrail":
                    continue
                rank = item.override_rank_order or item.rank_order
                ranking_rows.append(
                    {
                        "rank_order": rank,
                        "label": item.entity_label or item.entity_id,
                        "total_score": item.total_score,
                        "confidence_score": item.confidence_score,
                        "rationale": item.rationale[:160],
                        "review_status": item.review_status,
                        "ruleset_version": ranking_run.ruleset_version,
                        "scoring_profile": profile.name if profile else "",
                    }
                )
                breakdown = RankingRepository.loads_breakdown(item.breakdown_json)
                scorecard_rows.append(
                    {
                        "label": item.entity_label or item.entity_id,
                        "priority_alignment": breakdown.get("priority_alignment"),
                        "weaponeering_fit": breakdown.get("weaponeering_fit"),
                        "logistics_feasibility": breakdown.get("logistics_feasibility"),
                        "readiness": breakdown.get("readiness"),
                        "resource_balance": breakdown.get("resource_balance"),
                        "risk_indicator": breakdown.get("risk_indicator"),
                        "total_score": item.total_score,
                        "rationale": item.rationale[:160],
                    }
                )

        instructor_notes = [
            {
                "entity_type": r["entity_type"],
                "entity_id": r["entity_id"][:8],
                "reviewer": r["reviewer"],
                "decision": r["decision"],
                "notes": r["notes"][:160],
                "created_at": r["created_at"],
            }
            for r in self.target_repository.list_review_records(scenario_id)
        ]

        audit_rows = [
            {
                "event_type": e.event_type,
                "entity_type": e.entity_type,
                "actor": e.actor,
                "created_at": e.created_at,
            }
            for e in self.audit_repository.list_for_scenario(scenario_id)
        ]
        guardrail_rows = [
            {
                "event_type": g["event_type"],
                "decision": g["decision"],
                "summary": g["sanitized_summary"],
            }
            for g in self.guardrail_repository.list_recent(50)
        ]

        return {
            "scenario_brief": {
                "name": scenario.name if scenario else "",
                "description": scenario.description if scenario else "",
                "ruleset_version": scenario.ruleset_version if scenario else "",
                "learning_objectives": [label for _, label, _ in objectives],
                "simulation_label": SIMULATION_LABEL,
            },
            "target_list": targets,
            "weaponeering_summary": weaponeering_rows,
            "logistics_summary": logistics,
            "ranking_table": ranking_rows,
            "scorecard": scorecard_rows,
            "instructor_notes": instructor_notes,
            "audit_summary": audit_rows,
            "guardrail_summary": guardrail_rows,
        }

    def _select_sections(self, export_type: str, sections: dict) -> dict:
        if export_type == "full_package":
            return {k: v for k, v in sections.items() if k != "guardrail_summary"}
        if export_type == "aar_summary":
            return {
                k: sections[k]
                for k in (
                    "scenario_brief",
                    "target_list",
                    "weaponeering_summary",
                    "logistics_summary",
                    "ranking_table",
                    "instructor_notes",
                    "audit_summary",
                )
            }
        if export_type in sections:
            return {export_type: sections[export_type]}
        return {export_type: {}}

    def _render_content(
        self,
        export_type: str,
        export_format: str,
        scenario_name: str,
        sections: dict,
        manifest_base: dict,
    ) -> str:
        if export_format == "json":
            manifest_base["files"] = list(sections.keys())
            return to_json_package(manifest_base, sections)
        if export_format == "csv":
            for value in sections.values():
                if isinstance(value, list):
                    return to_csv(value)
            return to_csv([sections])
        return to_markdown(f"{scenario_name} — {export_type}", sections)

    @staticmethod
    def _build_filename(
        scenario_name: str,
        export_type: str,
        ranking_run_id: str | None,
        export_format: str,
    ) -> str:
        safe_name = re.sub(r"[^\w\-]+", "_", scenario_name.strip())[:40] or "scenario"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_part = f"_{ranking_run_id[:8]}" if ranking_run_id else ""
        ext = "md" if export_format == "markdown" else export_format
        if export_type == "full_package":
            return f"{safe_name}_{export_type}{run_part}_{timestamp}"
        return f"{safe_name}_{export_type}{run_part}_{timestamp}.{ext}"

    @staticmethod
    def _replay_explanation(orig, new) -> str:
        parts = []
        if orig.total_score != new.total_score:
            parts.append(
                f"Total score changed {orig.total_score} -> {new.total_score}."
            )
        orig_rank = orig.override_rank_order or orig.rank_order
        new_rank = new.override_rank_order or new.rank_order
        if orig_rank != new_rank:
            parts.append(f"Rank changed {orig_rank} -> {new_rank}.")
        orig_bd = RankingRepository.loads_breakdown(orig.breakdown_json)
        new_bd = RankingRepository.loads_breakdown(new.breakdown_json)
        for key in orig_bd:
            if key == "warnings":
                continue
            if orig_bd.get(key) != new_bd.get(key):
                parts.append(
                    f"{key.replace('_', ' ')}: {orig_bd.get(key)} -> {new_bd.get(key)}."
                )
        return " ".join(parts) if parts else "No component-level explanation available."

    def _generate_action_items(
        self,
        scenario_id: str,
        sections: dict,
    ) -> list[AarActionItem]:
        items: list[AarActionItem] = []
        for target in sections.get("target_list", []):
            for warning in target.get("missing_data_warnings", []):
                item_id = str(uuid4())
                desc = f"Resolve missing data for {target['label']}: {warning}"
                self.repository.insert_action_item(
                    item_id=item_id,
                    scenario_id=scenario_id,
                    source_type="missing_data",
                    source_reference=target["label"],
                    description=desc,
                )
                items.append(
                    AarActionItem(
                        id=item_id,
                        scenario_id=scenario_id,
                        source_type="missing_data",
                        source_reference=target["label"],
                        description=desc,
                        status="open",
                    )
                )
        for note in sections.get("instructor_notes", []):
            if note["decision"] in ("reject", "needs_revision"):
                item_id = str(uuid4())
                desc = f"Follow up review decision '{note['decision']}' for {note['entity_type']}."
                self.repository.insert_action_item(
                    item_id=item_id,
                    scenario_id=scenario_id,
                    source_type="review_decision",
                    source_reference=note["entity_id"],
                    description=desc,
                )
                items.append(
                    AarActionItem(
                        id=item_id,
                        scenario_id=scenario_id,
                        source_type="review_decision",
                        source_reference=note["entity_id"],
                        description=desc,
                        status="open",
                    )
                )
        return items
