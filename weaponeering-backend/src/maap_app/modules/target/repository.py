from __future__ import annotations

import json

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.target.models import (
    HumanReviewRecord,
    TargetCard,
    TargetCardDetail,
    TargetCoordinate,
    TargetRecognitionResult,
)
from maap_app.modules.target.profile_fields import TargetProfileFields

_TARGET_CARD_SELECT = """
    SELECT id, scenario_id, label, priority_score, complexity_score,
           map_node_id, review_status, status,
           target_type, target_subtype, material_class, target_description, floor_count,
           width_m, length_m, height_m, desired_model_result,
           coordinate_error_m, data_source, cep, target_pk, reference_pk,
           resistance, capacity, damage_fit, model_version, selected_product_id,
           created_at, updated_at
    FROM target_cards
"""


class TargetRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def insert_target_card(
        self,
        target_id: str,
        scenario_id: str,
        label: str,
        priority_score: int,
        complexity_score: int,
        review_status: str,
        profile: TargetProfileFields,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO target_cards (
                    id, scenario_id, label,
                    priority_score, complexity_score, review_status,
                    target_type, target_subtype, material_class, target_description, floor_count,
                    width_m, length_m, height_m, desired_model_result,
                    coordinate_error_m, data_source, cep, target_pk, reference_pk,
                    resistance, capacity, damage_fit, model_version, selected_product_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    target_id,
                    scenario_id,
                    label,
                    priority_score,
                    complexity_score,
                    review_status,
                    *profile.as_db_tuple(),
                ),
            )

    def update_target_card(
        self,
        target_id: str,
        label: str,
        priority_score: int,
        complexity_score: int,
        review_status: str,
        profile: TargetProfileFields,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE target_cards
                SET label = ?, priority_score = ?, complexity_score = ?,
                    review_status = ?,
                    target_type = ?, target_subtype = ?, material_class = ?, target_description = ?,
                    floor_count = ?,
                    width_m = ?, length_m = ?, height_m = ?, desired_model_result = ?,
                    coordinate_error_m = ?, data_source = ?, cep = ?,
                    target_pk = ?, reference_pk = ?,
                    resistance = ?, capacity = ?, damage_fit = ?, model_version = ?,
                    selected_product_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    label,
                    priority_score,
                    complexity_score,
                    review_status,
                    *profile.as_db_tuple(),
                    target_id,
                ),
            )

    def update_review_status(self, target_id: str, review_status: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE target_cards
                SET review_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (review_status, target_id),
            )

    def delete_target_card(self, target_id: str) -> bool:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT map_node_id FROM target_cards WHERE id = ?",
                (target_id,),
            ).fetchone()
            map_node_id = row["map_node_id"] if row else None
            cursor = connection.execute(
                "DELETE FROM target_cards WHERE id = ?",
                (target_id,),
            )
            deleted = cursor.rowcount > 0
            if deleted and map_node_id:
                connection.execute(
                    "DELETE FROM map_nodes WHERE id = ?",
                    (map_node_id,),
                )
        return deleted

    def delete_target_card(self, target_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "DELETE FROM target_cards WHERE id = ?",
                (target_id,),
            )

    def get_target_card(self, target_id: str) -> TargetCard | None:
        with self.database.connect() as connection:
            row = connection.execute(
                f"{_TARGET_CARD_SELECT} WHERE id = ?",
                (target_id,),
            ).fetchone()
        return TargetCard(**dict(row)) if row else None

    def list_active_target_cards(self, scenario_id: str) -> list[TargetCard]:
        with self.database.connect() as connection:
            rows = connection.execute(
                f"""
                {_TARGET_CARD_SELECT}
                WHERE scenario_id = ? AND status = 'active'
                ORDER BY created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [TargetCard(**dict(row)) for row in rows]

    def get_target_by_map_node(self, map_node_id: str) -> TargetCard | None:
        with self.database.connect() as connection:
            row = connection.execute(
                f"""
                {_TARGET_CARD_SELECT}
                WHERE map_node_id = ? AND status = 'active'
                """,
                (map_node_id,),
            ).fetchone()
        return TargetCard(**dict(row)) if row else None

    def set_target_map_node(self, target_id: str, map_node_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE target_cards
                SET map_node_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (map_node_id, target_id),
            )

    def insert_recognition_result(
        self,
        result_id: str,
        target_card_id: str,
        source_type: str,
        recognition_summary: str,
        recognition_confidence_score: int,
        missing_data_json: str,
        generated_by: str,
        review_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO target_recognition_results (
                    id, target_card_id, source_type, recognition_summary,
                    recognition_confidence_score, missing_data_json,
                    generated_by, review_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    target_card_id,
                    source_type,
                    recognition_summary,
                    recognition_confidence_score,
                    missing_data_json,
                    generated_by,
                    review_status,
                ),
            )

    def update_recognition_result(
        self,
        result_id: str,
        recognition_summary: str,
        recognition_confidence_score: int,
        missing_data_json: str,
        review_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE target_recognition_results
                SET recognition_summary = ?,
                    recognition_confidence_score = ?,
                    missing_data_json = ?,
                    review_status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    recognition_summary,
                    recognition_confidence_score,
                    missing_data_json,
                    review_status,
                    result_id,
                ),
            )

    def get_recognition_by_id(self, result_id: str) -> TargetRecognitionResult | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, target_card_id, source_type, recognition_summary,
                       recognition_confidence_score, missing_data_json,
                       generated_by, review_status, created_at, updated_at
                FROM target_recognition_results
                WHERE id = ?
                """,
                (result_id,),
            ).fetchone()
        return TargetRecognitionResult(**dict(row)) if row else None

    def get_latest_recognition(self, target_card_id: str) -> TargetRecognitionResult | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, target_card_id, source_type, recognition_summary,
                       recognition_confidence_score, missing_data_json,
                       generated_by, review_status, created_at, updated_at
                FROM target_recognition_results
                WHERE target_card_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (target_card_id,),
            ).fetchone()
        return TargetRecognitionResult(**dict(row)) if row else None

    def list_target_coordinates(self, target_card_id: str) -> list[TargetCoordinate]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, target_card_id, label, map_lat, map_lng,
                       sort_order, is_primary, selected_product_id, created_at
                FROM target_coordinates
                WHERE target_card_id = ?
                ORDER BY sort_order ASC, created_at ASC
                """,
                (target_card_id,),
            ).fetchall()
        return [
            TargetCoordinate(
                id=row["id"],
                target_card_id=row["target_card_id"],
                label=row["label"] or "",
                map_lat=float(row["map_lat"]),
                map_lng=float(row["map_lng"]),
                sort_order=int(row["sort_order"]),
                is_primary=bool(row["is_primary"]),
                selected_product_id=row["selected_product_id"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_target_coordinate(self, coordinate_id: str) -> TargetCoordinate | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, target_card_id, label, map_lat, map_lng,
                       sort_order, is_primary, selected_product_id, created_at
                FROM target_coordinates
                WHERE id = ?
                """,
                (coordinate_id,),
            ).fetchone()
        if row is None:
            return None
        return TargetCoordinate(
            id=row["id"],
            target_card_id=row["target_card_id"],
            label=row["label"] or "",
            map_lat=float(row["map_lat"]),
            map_lng=float(row["map_lng"]),
            sort_order=int(row["sort_order"]),
            is_primary=bool(row["is_primary"]),
            selected_product_id=row["selected_product_id"],
            created_at=row["created_at"],
        )

    def update_coordinate_product(
        self,
        coordinate_id: str,
        selected_product_id: str | None,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE target_coordinates
                SET selected_product_id = ?
                WHERE id = ?
                """,
                (selected_product_id, coordinate_id),
            )

    def replace_target_coordinates(
        self,
        target_card_id: str,
        coordinates: list[tuple[str, str, float, float, int, bool, str | None]],
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "DELETE FROM target_coordinates WHERE target_card_id = ?",
                (target_card_id,),
            )
            for (
                coord_id,
                label,
                lat,
                lng,
                sort_order,
                is_primary,
                selected_product_id,
            ) in coordinates:
                connection.execute(
                    """
                    INSERT INTO target_coordinates (
                        id, target_card_id, label, map_lat, map_lng,
                        sort_order, is_primary, selected_product_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        coord_id,
                        target_card_id,
                        label,
                        lat,
                        lng,
                        sort_order,
                        1 if is_primary else 0,
                        selected_product_id,
                    ),
                )

    def get_target_detail(self, target_id: str) -> TargetCardDetail | None:
        card = self.get_target_card(target_id)
        if card is None:
            return None

        recognition = self.get_latest_recognition(target_id)
        coordinates = self.list_target_coordinates(target_id)
        map_node_label = None
        map_lat = None
        map_lng = None

        if coordinates:
            primary = next(
                (coord for coord in coordinates if coord.is_primary),
                coordinates[0],
            )
            map_lat = primary.map_lat
            map_lng = primary.map_lng
            map_node_label = primary.label or card.label
        elif card.map_node_id:
            with self.database.connect() as connection:
                node = connection.execute(
                    """
                    SELECT label, map_lat, map_lng
                    FROM map_nodes
                    WHERE id = ?
                    """,
                    (card.map_node_id,),
                ).fetchone()
            if node:
                map_node_label = node["label"]
                map_lat = node["map_lat"]
                map_lng = node["map_lng"]

        return TargetCardDetail(
            card=card,
            recognition=recognition,
            map_node_label=map_node_label,
            map_lat=map_lat,
            map_lng=map_lng,
            coordinates=coordinates,
        )

    def list_review_records(self, scenario_id: str) -> list[dict]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, entity_type, entity_id, reviewer,
                       decision, notes, created_at
                FROM human_review_records
                WHERE scenario_id = ?
                ORDER BY created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_review_record(
        self,
        record_id: str,
        scenario_id: str,
        entity_type: str,
        entity_id: str,
        reviewer: str,
        decision: str,
        notes: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO human_review_records (
                    id, scenario_id, entity_type, entity_id,
                    reviewer, decision, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    scenario_id,
                    entity_type,
                    entity_id,
                    reviewer,
                    decision,
                    notes,
                ),
            )

    @staticmethod
    def parse_missing_data(missing_data_json: str) -> list[str]:
        try:
            data = json.loads(missing_data_json)
        except json.JSONDecodeError:
            return []
        if isinstance(data, list):
            return [str(item) for item in data]
        return []
