from __future__ import annotations

import json
from typing import Any

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.detection.models import TargetMapDetectionObject, TargetMapDetectionRun

_RUN_SELECT = """
    SELECT id, scenario_id, target_card_id, target_coordinate_id, model_name,
           model_file_name, radius_m, capture_radius_m, source_image_name,
           object_count, detection_message, created_at, updated_at
    FROM target_map_detection_runs
"""


class TargetDetectionRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def _load_run(self, row) -> TargetMapDetectionRun:
        with self.database.connect() as connection:
            object_rows = connection.execute(
                """
                SELECT id, run_id, target_card_id, map_object_id, object_label,
                       object_type, risk_level, confidence, center_lat, center_lng,
                       polygon_json, sort_order
                FROM target_map_detection_objects
                WHERE run_id = ?
                ORDER BY sort_order ASC, object_label ASC
                """,
                (row["id"],),
            ).fetchall()
        payload = dict(row)
        payload["objects"] = tuple(
            TargetMapDetectionObject(**dict(object_row)) for object_row in object_rows
        )
        return TargetMapDetectionRun(**payload)

    def get_run_for_coordinate(
        self,
        target_card_id: str,
        target_coordinate_id: str,
    ) -> TargetMapDetectionRun | None:
        with self.database.connect() as connection:
            row = connection.execute(
                f"""
                {_RUN_SELECT}
                WHERE target_card_id = ? AND target_coordinate_id = ?
                """,
                (target_card_id, target_coordinate_id),
            ).fetchone()
        return self._load_run(row) if row else None

    def get_run_for_target(self, target_card_id: str) -> TargetMapDetectionRun | None:
        runs = self.list_runs_for_target(target_card_id)
        return runs[0] if runs else None

    def list_runs_for_target(self, target_card_id: str) -> list[TargetMapDetectionRun]:
        with self.database.connect() as connection:
            rows = connection.execute(
                f"""
                {_RUN_SELECT}
                WHERE target_card_id = ?
                ORDER BY
                    CASE
                        WHEN target_coordinate_id LIKE 'legacy-%' THEN 1
                        ELSE 0
                    END,
                    updated_at DESC,
                    created_at DESC
                """,
                (target_card_id,),
            ).fetchall()
        return [self._load_run(row) for row in rows]

    def list_runs_for_scenario(self, scenario_id: str) -> list[TargetMapDetectionRun]:
        with self.database.connect() as connection:
            rows = connection.execute(
                f"""
                {_RUN_SELECT}
                WHERE scenario_id = ?
                ORDER BY updated_at DESC, created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [self._load_run(row) for row in rows]

    def upsert_detection_run(
        self,
        run_id: str,
        scenario_id: str,
        target_card_id: str,
        target_coordinate_id: str,
        model_name: str,
        model_file_name: str | None,
        radius_m: int,
        capture_radius_m: int,
        source_image_name: str | None,
        detection_message: str | None,
        objects: list[dict[str, Any]],
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO target_map_detection_runs (
                    id, scenario_id, target_card_id, target_coordinate_id,
                    model_name, model_file_name, radius_m, capture_radius_m,
                    source_image_name, object_count, detection_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(target_card_id, target_coordinate_id) DO UPDATE SET
                    model_name = excluded.model_name,
                    model_file_name = excluded.model_file_name,
                    radius_m = excluded.radius_m,
                    capture_radius_m = excluded.capture_radius_m,
                    source_image_name = excluded.source_image_name,
                    object_count = excluded.object_count,
                    detection_message = excluded.detection_message,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    run_id,
                    scenario_id,
                    target_card_id,
                    target_coordinate_id,
                    model_name,
                    model_file_name,
                    radius_m,
                    capture_radius_m,
                    source_image_name,
                    len(objects),
                    detection_message,
                ),
            )
            resolved_run_id = connection.execute(
                """
                SELECT id
                FROM target_map_detection_runs
                WHERE target_card_id = ? AND target_coordinate_id = ?
                """,
                (target_card_id, target_coordinate_id),
            ).fetchone()["id"]
            connection.execute(
                """
                DELETE FROM target_map_detection_objects
                WHERE run_id = ?
                """,
                (resolved_run_id,),
            )
            for sort_order, obj in enumerate(objects):
                connection.execute(
                    """
                    INSERT INTO target_map_detection_objects (
                        id, run_id, target_card_id, map_object_id, object_label,
                        object_type, risk_level, confidence, center_lat, center_lng,
                        polygon_json, sort_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        obj["db_id"],
                        resolved_run_id,
                        target_card_id,
                        str(obj.get("id", "")),
                        str(obj.get("label", "")),
                        str(obj.get("objectType", "")),
                        str(obj.get("risk", "low")),
                        float(obj.get("confidence", 0.0)),
                        float(obj["lat"]),
                        float(obj["lng"]),
                        json.dumps(obj.get("polygon", [])),
                        sort_order,
                    ),
                )
