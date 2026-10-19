from __future__ import annotations

from pathlib import Path

import pytest

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.team_marker.repository import TeamMarkerRepository
from maap_app.modules.team_marker.service import TeamMarkerService


def _build_services(tmp_path: Path):
    settings = AppSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.sqlite3",
    )
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    audit_service = AuditService(AuditRepository(database))
    guardrail_service = GuardrailService(GuardrailRepository(database), audit_service)
    scenario_repository = ScenarioRepository(database)
    scenario_service = ScenarioService(
        repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    team_marker_service = TeamMarkerService(
        repository=TeamMarkerRepository(database),
        scenario_repository=scenario_repository,
        audit_service=audit_service,
    )
    return scenario_service, team_marker_service


def test_create_and_list_team_markers(tmp_path: Path) -> None:
    scenario_service, team_marker_service = _build_services(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Team Marker Scenario")
    )

    blue_id = team_marker_service.create_marker(
        scenario_id=scenario_id,
        side="blue",
        label="Alpha",
        map_lat=13.75,
        map_lng=100.50,
    )
    red_id = team_marker_service.create_marker(
        scenario_id=scenario_id,
        side="red",
        unit_type="radar",
        label="Hostile-1",
        map_lat=13.80,
        map_lng=100.55,
        radius_m=30_000,
    )

    markers = team_marker_service.list_map_markers(scenario_id)
    assert len(markers) == 2
    assert {item["id"] for item in markers} == {blue_id, red_id}
    assert any(item["side"] == "blue" and item["label"] == "Alpha" for item in markers)
    radar_marker = next(item for item in markers if item["id"] == red_id)
    assert radar_marker["unitType"] == "radar"
    assert radar_marker["radiusM"] == 30_000

    team_marker_service.delete_marker(blue_id)
    assert len(team_marker_service.list_map_markers(scenario_id)) == 1


def test_radar_requires_valid_radius(tmp_path: Path) -> None:
    scenario_service, team_marker_service = _build_services(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Radar Radius Scenario")
    )
    with pytest.raises(ValueError, match="รัศมีเรดาร์"):
        team_marker_service.create_marker(
            scenario_id=scenario_id,
            side="blue",
            unit_type="radar",
            label="RADAR-1",
            map_lat=13.0,
            map_lng=100.0,
            radius_m=10,
        )


def test_default_marker_name_by_unit_type(tmp_path: Path) -> None:
    _, team_marker_service = _build_services(tmp_path)
    assert (
        team_marker_service.default_marker_name("blue", "radar", 0) == "RADAR-BLUE-01"
    )
    assert team_marker_service.default_marker_name("red", "tank", 2) == "TANK-RED-03"
    assert team_marker_service.default_marker_name("blue", "generic", 0) == "BLUE-01"
