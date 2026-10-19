from __future__ import annotations

from pathlib import Path

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateMapNodeRequest, CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService


def build_service(tmp_path: Path) -> ScenarioService:
    settings = AppSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.sqlite3",
    )
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    audit_service = AuditService(AuditRepository(database))
    guardrail_service = GuardrailService(GuardrailRepository(database), audit_service)
    return ScenarioService(
        repository=ScenarioRepository(database),
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )


def test_create_scenario_and_map_node(tmp_path: Path) -> None:
    service = build_service(tmp_path)

    scenario_id = service.create_scenario(
        CreateScenarioRequest(name="Synthetic Training Scenario")
    )
    node_id = service.create_map_node(
        CreateMapNodeRequest(
            scenario_id=scenario_id,
            label="Synthetic Node A",
            map_lat=13.75,
            map_lng=100.5,
        )
    )

    scenarios = service.list_scenarios()
    nodes = service.list_map_nodes(scenario_id)

    assert scenarios[0].id == scenario_id
    assert nodes[0].id == node_id
    assert nodes[0].label == "Synthetic Node A"

