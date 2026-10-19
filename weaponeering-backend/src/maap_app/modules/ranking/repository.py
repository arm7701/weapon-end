from __future__ import annotations

import json

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.ranking.models import RankingItem, RankingRun, ScoringProfile


class RankingRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def insert_scoring_profile(
        self,
        profile_id: str,
        scenario_id: str,
        name: str,
        ruleset_version: str,
        priority_weight: int,
        weaponeering_weight: int,
        logistics_weight: int,
        readiness_weight: int,
        risk_weight: int,
        resource_balance_weight: int,
        is_active: int,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO scoring_profiles (
                    id, scenario_id, name, ruleset_version,
                    priority_weight, weaponeering_weight, logistics_weight,
                    readiness_weight, risk_weight, resource_balance_weight,
                    is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    scenario_id,
                    name,
                    ruleset_version,
                    priority_weight,
                    weaponeering_weight,
                    logistics_weight,
                    readiness_weight,
                    risk_weight,
                    resource_balance_weight,
                    is_active,
                ),
            )

    def update_scoring_profile(
        self,
        profile_id: str,
        name: str,
        priority_weight: int,
        weaponeering_weight: int,
        logistics_weight: int,
        readiness_weight: int,
        risk_weight: int,
        resource_balance_weight: int,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE scoring_profiles
                SET name = ?, priority_weight = ?, weaponeering_weight = ?,
                    logistics_weight = ?, readiness_weight = ?, risk_weight = ?,
                    resource_balance_weight = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    name,
                    priority_weight,
                    weaponeering_weight,
                    logistics_weight,
                    readiness_weight,
                    risk_weight,
                    resource_balance_weight,
                    profile_id,
                ),
            )

    def clear_active_profiles(self, scenario_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE scoring_profiles
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE scenario_id = ?
                """,
                (scenario_id,),
            )

    def set_active_profile(self, profile_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE scoring_profiles
                SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (profile_id,),
            )

    def list_scoring_profiles(self, scenario_id: str) -> list[ScoringProfile]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, name, ruleset_version,
                       priority_weight, weaponeering_weight, logistics_weight,
                       readiness_weight, risk_weight, resource_balance_weight,
                       is_active
                FROM scoring_profiles
                WHERE scenario_id = ?
                ORDER BY is_active DESC, name
                """,
                (scenario_id,),
            ).fetchall()
        return [ScoringProfile(**dict(row)) for row in rows]

    def get_scoring_profile(self, profile_id: str) -> ScoringProfile | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, name, ruleset_version,
                       priority_weight, weaponeering_weight, logistics_weight,
                       readiness_weight, risk_weight, resource_balance_weight,
                       is_active
                FROM scoring_profiles
                WHERE id = ?
                """,
                (profile_id,),
            ).fetchone()
        return ScoringProfile(**dict(row)) if row else None

    def get_active_scoring_profile(self, scenario_id: str) -> ScoringProfile | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, name, ruleset_version,
                       priority_weight, weaponeering_weight, logistics_weight,
                       readiness_weight, risk_weight, resource_balance_weight,
                       is_active
                FROM scoring_profiles
                WHERE scenario_id = ? AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (scenario_id,),
            ).fetchone()
        return ScoringProfile(**dict(row)) if row else None

    def insert_ranking_run(
        self,
        run_id: str,
        scenario_id: str,
        ruleset_version: str,
        scoring_profile_id: str | None,
        generated_by: str,
        run_status: str,
        summary: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO ranking_runs (
                    id, scenario_id, ruleset_version, scoring_profile_id,
                    generated_by, run_status, summary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    scenario_id,
                    ruleset_version,
                    scoring_profile_id,
                    generated_by,
                    run_status,
                    summary,
                ),
            )

    def insert_ranking_item(
        self,
        item_id: str,
        ranking_run_id: str,
        entity_type: str,
        entity_id: str,
        rank_order: int,
        total_score: int,
        confidence_score: int,
        rationale: str,
        breakdown_json: str,
        review_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO ranking_items (
                    id, ranking_run_id, entity_type, entity_id,
                    rank_order, total_score, confidence_score,
                    rationale, breakdown_json, review_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    ranking_run_id,
                    entity_type,
                    entity_id,
                    rank_order,
                    total_score,
                    confidence_score,
                    rationale,
                    breakdown_json,
                    review_status,
                ),
            )

    def get_ranking_run(self, run_id: str) -> RankingRun | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, ruleset_version, scoring_profile_id,
                       generated_by, run_status, summary, created_at
                FROM ranking_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
        return RankingRun(**dict(row)) if row else None

    def list_ranking_runs(self, scenario_id: str) -> list[RankingRun]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, ruleset_version, scoring_profile_id,
                       generated_by, run_status, summary, created_at
                FROM ranking_runs
                WHERE scenario_id = ?
                ORDER BY created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [RankingRun(**dict(row)) for row in rows]

    def get_latest_ranking_run(self, scenario_id: str) -> RankingRun | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, ruleset_version, scoring_profile_id,
                       generated_by, run_status, summary, created_at
                FROM ranking_runs
                WHERE scenario_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (scenario_id,),
            ).fetchone()
        return RankingRun(**dict(row)) if row else None

    def list_ranking_items(self, ranking_run_id: str) -> list[RankingItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT ri.id, ri.ranking_run_id, ri.entity_type, ri.entity_id,
                       ri.rank_order, ri.total_score, ri.confidence_score,
                       ri.rationale, ri.breakdown_json, ri.review_status,
                       ri.override_rank_order, ri.override_notes,
                       tc.label AS entity_label
                FROM ranking_items ri
                LEFT JOIN target_cards tc ON tc.id = ri.entity_id
                    AND ri.entity_type = 'target_card'
                WHERE ri.ranking_run_id = ?
                ORDER BY COALESCE(ri.override_rank_order, ri.rank_order)
                """,
                (ranking_run_id,),
            ).fetchall()
        items: list[RankingItem] = []
        for row in rows:
            data = dict(row)
            items.append(RankingItem(**data))
        return items

    def get_ranking_item(self, item_id: str) -> RankingItem | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT ri.id, ri.ranking_run_id, ri.entity_type, ri.entity_id,
                       ri.rank_order, ri.total_score, ri.confidence_score,
                       ri.rationale, ri.breakdown_json, ri.review_status,
                       ri.override_rank_order, ri.override_notes,
                       tc.label AS entity_label
                FROM ranking_items ri
                LEFT JOIN target_cards tc ON tc.id = ri.entity_id
                    AND ri.entity_type = 'target_card'
                WHERE ri.id = ?
                """,
                (item_id,),
            ).fetchone()
        return RankingItem(**dict(row)) if row else None

    def update_item_review_status(self, item_id: str, review_status: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE ranking_items
                SET review_status = ?
                WHERE id = ?
                """,
                (review_status, item_id),
            )

    def list_items_requiring_review(self, scenario_id: str) -> list[RankingItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT ri.id, ri.ranking_run_id, ri.entity_type, ri.entity_id,
                       ri.rank_order, ri.total_score, ri.confidence_score,
                       ri.rationale, ri.breakdown_json, ri.review_status,
                       ri.override_rank_order, ri.override_notes,
                       tc.label AS entity_label
                FROM ranking_items ri
                JOIN ranking_runs rr ON rr.id = ri.ranking_run_id
                LEFT JOIN target_cards tc ON tc.id = ri.entity_id
                    AND ri.entity_type = 'target_card'
                WHERE rr.scenario_id = ?
                  AND (
                    ri.review_status = 'requires_review'
                    OR ri.override_rank_order IS NOT NULL
                  )
                ORDER BY ri.created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [RankingItem(**dict(row)) for row in rows]

    def apply_ranking_override(
        self,
        item_id: str,
        override_rank_order: int,
        override_notes: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE ranking_items
                SET override_rank_order = ?, override_notes = ?
                WHERE id = ?
                """,
                (override_rank_order, override_notes, item_id),
            )

    def insert_plan_option(
        self,
        plan_id: str,
        scenario_id: str,
        title: str,
        generated_by: str,
        review_status: str,
        rank_order: int | None,
        planning_horizon: str = "",
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO plan_options (
                    id, scenario_id, planning_horizon, title,
                    generated_by, review_status, rank_order
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    scenario_id,
                    planning_horizon,
                    title,
                    generated_by,
                    review_status,
                    rank_order,
                ),
            )

    def insert_plan_assignment(
        self,
        assignment_id: str,
        plan_option_id: str,
        target_card_id: str | None,
        abstract_weaponeering_option_id: str | None,
        assignment_score: int,
        review_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO plan_assignments (
                    id, plan_option_id, target_card_id,
                    abstract_weaponeering_option_id, assignment_score,
                    review_status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    assignment_id,
                    plan_option_id,
                    target_card_id,
                    abstract_weaponeering_option_id,
                    assignment_score,
                    review_status,
                ),
            )

    @staticmethod
    def dumps_breakdown(breakdown: dict) -> str:
        return json.dumps(breakdown)

    @staticmethod
    def loads_breakdown(breakdown_json: str) -> dict:
        try:
            return json.loads(breakdown_json)
        except json.JSONDecodeError:
            return {}
