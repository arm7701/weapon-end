from __future__ import annotations

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.export.models import AarActionItem, ExportPackage


class ExportRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def insert_export_package(
        self,
        package_id: str,
        scenario_id: str,
        export_type: str,
        export_status: str,
        destination_path: str,
        blocked_reason: str,
        created_by: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO export_packages (
                    id, scenario_id, export_type, export_status,
                    destination_path, blocked_reason, created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    package_id,
                    scenario_id,
                    export_type,
                    export_status,
                    destination_path,
                    blocked_reason,
                    created_by,
                ),
            )

    def list_export_packages(self, scenario_id: str) -> list[ExportPackage]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, export_type, export_status,
                       destination_path, blocked_reason, created_by, created_at
                FROM export_packages
                WHERE scenario_id = ?
                ORDER BY created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [ExportPackage(**dict(row)) for row in rows]

    def insert_action_item(
        self,
        item_id: str,
        scenario_id: str,
        source_type: str,
        source_reference: str,
        description: str,
        status: str = "open",
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO aar_action_items (
                    id, scenario_id, source_type, source_reference,
                    description, status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (item_id, scenario_id, source_type, source_reference, description, status),
            )

    def update_action_item_status(self, item_id: str, status: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE aar_action_items
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, item_id),
            )

    def list_action_items(self, scenario_id: str) -> list[AarActionItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, source_type, source_reference,
                       description, status, created_at
                FROM aar_action_items
                WHERE scenario_id = ?
                ORDER BY created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [AarActionItem(**dict(row)) for row in rows]
