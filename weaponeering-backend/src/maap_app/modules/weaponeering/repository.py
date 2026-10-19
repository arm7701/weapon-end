from __future__ import annotations

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.weaponeering.models import (
    AbstractWeaponeeringOption,
    ImportBatch,
    TargetDeploymentAircraftLine,
    TargetDeploymentPlan,
    TargetDeploymentWaypoint,
    TargetWeaponeeringAssessment,
)


class WeaponeeringRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    _DEPLOYMENT_PLAN_COLUMNS = """
        id, scenario_id, target_card_id, wing_id, flying_unit_id,
        takeoff_lat, takeoff_lng, ingress_bearing_deg, ingress_offset_m,
        cruise_altitude_ft, ingress_altitude_ft, target_altitude_ft,
        climb_rate_ft_min, descent_rate_ft_min, return_enabled,
        cruise_speed_kt, climb_speed_kt, descent_speed_kt, ingress_speed_kt,
        bank_angle_deg, turn_mode, auto_toc_tod,
        created_at, updated_at
    """

    def _load_deployment_plan(
        self,
        connection,
        row,
    ) -> TargetDeploymentPlan:
        line_rows = connection.execute(
            """
            SELECT id, plan_id, aircraft_id, aircraft_count, sort_order
            FROM target_weaponeering_deployment_aircraft
            WHERE plan_id = ?
            ORDER BY sort_order ASC, created_at ASC
            """,
            (row["id"],),
        ).fetchall()
        waypoint_rows = connection.execute(
            """
            SELECT id, plan_id, waypoint_type, label, lat, lng, sort_order, altitude_ft
            FROM target_weaponeering_deployment_waypoints
            WHERE plan_id = ?
            ORDER BY sort_order ASC, created_at ASC
            """,
            (row["id"],),
        ).fetchall()
        payload = dict(row)
        payload["aircraft_lines"] = tuple(
            TargetDeploymentAircraftLine(**dict(line_row)) for line_row in line_rows
        )
        payload["waypoints"] = tuple(
            TargetDeploymentWaypoint(**dict(waypoint_row))
            for waypoint_row in waypoint_rows
        )
        if payload.get("ingress_offset_m") is None:
            payload["ingress_offset_m"] = 30000
        if payload.get("cruise_altitude_ft") is None:
            payload["cruise_altitude_ft"] = 25000
        if payload.get("ingress_altitude_ft") is None:
            payload["ingress_altitude_ft"] = 2000
        if payload.get("target_altitude_ft") is None:
            payload["target_altitude_ft"] = 2000
        if payload.get("climb_rate_ft_min") is None:
            payload["climb_rate_ft_min"] = 3000
        if payload.get("descent_rate_ft_min") is None:
            payload["descent_rate_ft_min"] = 2000
        if payload.get("return_enabled") is None:
            payload["return_enabled"] = 1
        payload["return_enabled"] = bool(payload["return_enabled"])
        if payload.get("cruise_speed_kt") is None:
            payload["cruise_speed_kt"] = 420.0
        if payload.get("climb_speed_kt") is None:
            payload["climb_speed_kt"] = 250.0
        if payload.get("descent_speed_kt") is None:
            payload["descent_speed_kt"] = 300.0
        if payload.get("ingress_speed_kt") is None:
            payload["ingress_speed_kt"] = 250.0
        if payload.get("bank_angle_deg") is None:
            payload["bank_angle_deg"] = 20.0
        if payload.get("turn_mode") is None:
            payload["turn_mode"] = "fly_by"
        if payload.get("auto_toc_tod") is None:
            payload["auto_toc_tod"] = 1
        payload["auto_toc_tod"] = bool(payload["auto_toc_tod"])
        return TargetDeploymentPlan(**payload)

    def insert_abstract_option(
        self,
        option_id: str,
        scenario_id: str,
        option_label: str,
        effect_category: str,
        required_capability_band: str,
        resource_token_type: str,
        estimated_effect_score: int,
        risk_score: int,
        logistics_demand_score: int,
        source_module: str,
        review_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO abstract_weaponeering_options (
                    id, scenario_id, option_label, effect_category,
                    required_capability_band, resource_token_type,
                    estimated_effect_score, risk_score, logistics_demand_score,
                    source_module, review_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    option_id,
                    scenario_id,
                    option_label,
                    effect_category,
                    required_capability_band,
                    resource_token_type,
                    estimated_effect_score,
                    risk_score,
                    logistics_demand_score,
                    source_module,
                    review_status,
                ),
            )

    def update_abstract_option(
        self,
        option_id: str,
        option_label: str,
        effect_category: str,
        required_capability_band: str,
        resource_token_type: str,
        estimated_effect_score: int,
        risk_score: int,
        logistics_demand_score: int,
        review_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE abstract_weaponeering_options
                SET option_label = ?, effect_category = ?,
                    required_capability_band = ?, resource_token_type = ?,
                    estimated_effect_score = ?, risk_score = ?,
                    logistics_demand_score = ?, review_status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    option_label,
                    effect_category,
                    required_capability_band,
                    resource_token_type,
                    estimated_effect_score,
                    risk_score,
                    logistics_demand_score,
                    review_status,
                    option_id,
                ),
            )

    def archive_abstract_option(self, option_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE abstract_weaponeering_options
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (option_id,),
            )

    def count_assessments_for_option(self, option_id: str) -> int:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM target_weaponeering_assessments
                WHERE abstract_weaponeering_option_id = ?
                """,
                (option_id,),
            ).fetchone()
        return int(row["count"]) if row else 0

    def list_abstract_options(self, scenario_id: str) -> list[AbstractWeaponeeringOption]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, option_label, effect_category,
                       required_capability_band, resource_token_type,
                       estimated_effect_score, risk_score, logistics_demand_score,
                       source_module, review_status, status
                FROM abstract_weaponeering_options
                WHERE scenario_id = ? AND status = 'active'
                ORDER BY option_label
                """,
                (scenario_id,),
            ).fetchall()
        return [AbstractWeaponeeringOption(**dict(row)) for row in rows]

    def get_abstract_option(self, option_id: str) -> AbstractWeaponeeringOption | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, option_label, effect_category,
                       required_capability_band, resource_token_type,
                       estimated_effect_score, risk_score, logistics_demand_score,
                       source_module, review_status, status
                FROM abstract_weaponeering_options
                WHERE id = ?
                """,
                (option_id,),
            ).fetchone()
        return AbstractWeaponeeringOption(**dict(row)) if row else None

    def find_option_by_label(
        self,
        scenario_id: str,
        option_label: str,
    ) -> AbstractWeaponeeringOption | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, option_label, effect_category,
                       required_capability_band, resource_token_type,
                       estimated_effect_score, risk_score, logistics_demand_score,
                       source_module, review_status, status
                FROM abstract_weaponeering_options
                WHERE scenario_id = ? AND option_label = ? AND status = 'active'
                LIMIT 1
                """,
                (scenario_id, option_label),
            ).fetchone()
        return AbstractWeaponeeringOption(**dict(row)) if row else None

    def insert_assessment(
        self,
        assessment_id: str,
        target_card_id: str,
        abstract_weaponeering_option_id: str,
        suitability_score: int,
        feasibility_score: int,
        risk_score: int,
        rationale: str,
        generated_by: str,
        review_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO target_weaponeering_assessments (
                    id, target_card_id, abstract_weaponeering_option_id,
                    suitability_score, feasibility_score, risk_score,
                    rationale, generated_by, review_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assessment_id,
                    target_card_id,
                    abstract_weaponeering_option_id,
                    suitability_score,
                    feasibility_score,
                    risk_score,
                    rationale,
                    generated_by,
                    review_status,
                ),
            )

    def update_assessment_review_status(
        self,
        assessment_id: str,
        review_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE target_weaponeering_assessments
                SET review_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (review_status, assessment_id),
            )

    def list_assessments_for_target(
        self,
        target_card_id: str,
    ) -> list[TargetWeaponeeringAssessment]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, target_card_id, abstract_weaponeering_option_id,
                       suitability_score, feasibility_score, risk_score,
                       rationale, generated_by, review_status
                FROM target_weaponeering_assessments
                WHERE target_card_id = ?
                ORDER BY created_at DESC
                """,
                (target_card_id,),
            ).fetchall()
        return [TargetWeaponeeringAssessment(**dict(row)) for row in rows]

    def list_assessments_requiring_review(
        self,
        scenario_id: str,
    ) -> list[TargetWeaponeeringAssessment]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT a.id, a.target_card_id, a.abstract_weaponeering_option_id,
                       a.suitability_score, a.feasibility_score, a.risk_score,
                       a.rationale, a.generated_by, a.review_status
                FROM target_weaponeering_assessments a
                JOIN target_cards t ON t.id = a.target_card_id
                WHERE t.scenario_id = ?
                  AND a.review_status = 'requires_review'
                ORDER BY a.created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [TargetWeaponeeringAssessment(**dict(row)) for row in rows]

    def list_approved_assessments_for_scenario(
        self,
        scenario_id: str,
    ) -> list[TargetWeaponeeringAssessment]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT a.id, a.target_card_id, a.abstract_weaponeering_option_id,
                       a.suitability_score, a.feasibility_score, a.risk_score,
                       a.rationale, a.generated_by, a.review_status
                FROM target_weaponeering_assessments a
                JOIN target_cards t ON t.id = a.target_card_id
                WHERE t.scenario_id = ?
                  AND t.status = 'active'
                  AND a.review_status = 'approved'
                """,
                (scenario_id,),
            ).fetchall()
        return [TargetWeaponeeringAssessment(**dict(row)) for row in rows]

    def insert_import_batch(
        self,
        batch_id: str,
        scenario_id: str,
        source_reference: str,
        import_status: str,
        validation_summary: str,
        imported_count: int,
        rejected_count: int,
        created_by: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO weaponeering_import_batches (
                    id, scenario_id, source_reference, import_status,
                    validation_summary, imported_count, rejected_count, created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    scenario_id,
                    source_reference,
                    import_status,
                    validation_summary,
                    imported_count,
                    rejected_count,
                    created_by,
                ),
            )

    def list_deployment_plans_for_scenario(
        self,
        scenario_id: str,
    ) -> list[TargetDeploymentPlan]:
        with self.database.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._DEPLOYMENT_PLAN_COLUMNS}
                FROM target_weaponeering_deployment_plans
                WHERE scenario_id = ?
                ORDER BY updated_at DESC
                """,
                (scenario_id,),
            ).fetchall()
            return [self._load_deployment_plan(connection, row) for row in rows]

    def get_deployment_plan_for_target(
        self,
        target_card_id: str,
    ) -> TargetDeploymentPlan | None:
        with self.database.connect() as connection:
            row = connection.execute(
                f"""
                SELECT {self._DEPLOYMENT_PLAN_COLUMNS}
                FROM target_weaponeering_deployment_plans
                WHERE target_card_id = ?
                """,
                (target_card_id,),
            ).fetchone()
            if row is None:
                return None
            return self._load_deployment_plan(connection, row)

    def upsert_deployment_plan(
        self,
        plan_id: str,
        scenario_id: str,
        target_card_id: str,
        wing_id: str,
        flying_unit_id: str,
        aircraft_lines: list[tuple[str, str, int, int]],
        *,
        takeoff_lat: float | None = None,
        takeoff_lng: float | None = None,
        ingress_bearing_deg: float | None = None,
        ingress_offset_m: int = 5000,
        cruise_altitude_ft: int = 25000,
        ingress_altitude_ft: int = 5000,
        target_altitude_ft: int = 1500,
        climb_rate_ft_min: int = 3000,
        descent_rate_ft_min: int = 2000,
        return_enabled: bool = True,
        cruise_speed_kt: float = 300.0,
        climb_speed_kt: float = 250.0,
        descent_speed_kt: float = 280.0,
        ingress_speed_kt: float = 220.0,
        bank_angle_deg: float = 25.0,
        turn_mode: str = "fly_by",
        auto_toc_tod: bool = True,
        waypoints: list[tuple[str, str, str | None, float, float, int, int | None]] | None = None,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO target_weaponeering_deployment_plans (
                    id, scenario_id, target_card_id, wing_id, flying_unit_id,
                    takeoff_lat, takeoff_lng, ingress_bearing_deg, ingress_offset_m,
                    cruise_altitude_ft, ingress_altitude_ft, target_altitude_ft,
                    climb_rate_ft_min, descent_rate_ft_min, return_enabled,
                    cruise_speed_kt, climb_speed_kt, descent_speed_kt, ingress_speed_kt,
                    bank_angle_deg, turn_mode, auto_toc_tod
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(target_card_id) DO UPDATE SET
                    wing_id = excluded.wing_id,
                    flying_unit_id = excluded.flying_unit_id,
                    takeoff_lat = excluded.takeoff_lat,
                    takeoff_lng = excluded.takeoff_lng,
                    ingress_bearing_deg = excluded.ingress_bearing_deg,
                    ingress_offset_m = excluded.ingress_offset_m,
                    cruise_altitude_ft = excluded.cruise_altitude_ft,
                    ingress_altitude_ft = excluded.ingress_altitude_ft,
                    target_altitude_ft = excluded.target_altitude_ft,
                    climb_rate_ft_min = excluded.climb_rate_ft_min,
                    descent_rate_ft_min = excluded.descent_rate_ft_min,
                    return_enabled = excluded.return_enabled,
                    cruise_speed_kt = excluded.cruise_speed_kt,
                    climb_speed_kt = excluded.climb_speed_kt,
                    descent_speed_kt = excluded.descent_speed_kt,
                    ingress_speed_kt = excluded.ingress_speed_kt,
                    bank_angle_deg = excluded.bank_angle_deg,
                    turn_mode = excluded.turn_mode,
                    auto_toc_tod = excluded.auto_toc_tod,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    plan_id,
                    scenario_id,
                    target_card_id,
                    wing_id,
                    flying_unit_id,
                    takeoff_lat,
                    takeoff_lng,
                    ingress_bearing_deg,
                    ingress_offset_m,
                    cruise_altitude_ft,
                    ingress_altitude_ft,
                    target_altitude_ft,
                    climb_rate_ft_min,
                    descent_rate_ft_min,
                    int(return_enabled),
                    cruise_speed_kt,
                    climb_speed_kt,
                    descent_speed_kt,
                    ingress_speed_kt,
                    bank_angle_deg,
                    turn_mode,
                    int(auto_toc_tod),
                ),
            )
            connection.execute(
                """
                DELETE FROM target_weaponeering_deployment_aircraft
                WHERE plan_id = ?
                """,
                (plan_id,),
            )
            for line_id, aircraft_id, aircraft_count, sort_order in aircraft_lines:
                connection.execute(
                    """
                    INSERT INTO target_weaponeering_deployment_aircraft (
                        id, plan_id, aircraft_id, aircraft_count, sort_order
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (line_id, plan_id, aircraft_id, aircraft_count, sort_order),
                )
            connection.execute(
                """
                DELETE FROM target_weaponeering_deployment_waypoints
                WHERE plan_id = ?
                """,
                (plan_id,),
            )
            for (
                waypoint_id,
                waypoint_type,
                label,
                lat,
                lng,
                sort_order,
                altitude_ft,
            ) in waypoints or []:
                connection.execute(
                    """
                    INSERT INTO target_weaponeering_deployment_waypoints (
                        id, plan_id, waypoint_type, label, lat, lng, sort_order,
                        altitude_ft
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        waypoint_id,
                        plan_id,
                        waypoint_type,
                        label,
                        lat,
                        lng,
                        sort_order,
                        altitude_ft,
                    ),
                )

    def delete_deployment_plan(self, target_card_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                DELETE FROM target_weaponeering_deployment_plans
                WHERE target_card_id = ?
                """,
                (target_card_id,),
            )

    def list_import_batches(self, scenario_id: str) -> list[ImportBatch]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, source_reference, import_status,
                       validation_summary, imported_count, rejected_count,
                       created_by, created_at
                FROM weaponeering_import_batches
                WHERE scenario_id = ?
                ORDER BY created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [ImportBatch(**dict(row)) for row in rows]
