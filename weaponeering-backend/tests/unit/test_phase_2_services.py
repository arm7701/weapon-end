from __future__ import annotations

from pathlib import Path

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.profile_fields import TargetProfileFields
from maap_app.modules.target.schemas import (
    CreateRecognitionResultRequest,
    CreateTargetCardRequest,
    LinkTargetMapNodeRequest,
    SaveTargetCoordinatesRequest,
    TargetCoordinateInput,
    TargetFilterParams,
    UpdateTargetCardRequest,
)
from maap_app.modules.target.service import TargetService


def build_target_service(tmp_path: Path) -> tuple[ScenarioService, TargetService]:
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
    target_service = TargetService(
        repository=TargetRepository(database),
        scenario_repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    return scenario_service, target_service


def test_target_card_recognition_and_map_link(tmp_path: Path) -> None:
    scenario_service, target_service = build_target_service(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Phase 2 Scenario")
    )

    target_id = target_service.create_target_card(
        CreateTargetCardRequest(
            scenario_id=scenario_id,
            label="TGT-001",
            priority_score=4,
            complexity_score=3,
        )
    )
    target_service.create_recognition_result(
        CreateRecognitionResultRequest(
            target_card_id=target_id,
            source_type="manual",
            recognition_summary="Synthetic training target summary.",
            recognition_confidence_score=72,
            missing_data_notes=["No imagery attached"],
        )
    )
    node_id = target_service.link_target_to_map(
        LinkTargetMapNodeRequest(
            target_card_id=target_id,
            scenario_id=scenario_id,
            map_lat=16.81,
            map_lng=100.12,
        )
    )

    items = target_service.list_target_cards(scenario_id)
    detail = target_service.get_target_detail(target_id)
    markers = target_service.list_map_markers(scenario_id)

    assert len(items) == 1
    assert items[0].card.label == "TGT-001"
    assert items[0].recognition_confidence == 72
    assert detail is not None
    assert detail.map_node_label is not None
    assert len(detail.warnings) >= 1
    assert markers[0]["targetCardId"] == target_id
    assert markers[0]["mapNodeId"] == node_id
    assert markers[0]["radiusM"] == 0.0

    target_service.update_target_card(
        UpdateTargetCardRequest(
            target_card_id=target_id,
            label="TGT-001",
            priority_score=4,
            complexity_score=3,
            profile=TargetProfileFields(coordinate_error_m=250.0),
        )
    )
    markers = target_service.list_map_markers(scenario_id)
    assert markers[0]["radiusM"] == 250.0


def test_target_card_persists_detail_fields(tmp_path: Path) -> None:
    scenario_service, target_service = build_target_service(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Target Detail Fields")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(
            scenario_id=scenario_id,
            label="TGT-DETAIL",
            profile=TargetProfileFields(
                target_type="BUNKER",
                target_subtype="HARDENED BUNKER",
                material_class="REINFORCED CONCRETE",
                target_description="Underground C2 node near runway",
            ),
        )
    )

    detail = target_service.get_target_detail(target_id)
    assert detail is not None
    assert detail.card.target_type == "BUNKER"
    assert detail.card.target_subtype == "HARDENED BUNKER"
    assert detail.card.material_class == "REINFORCED CONCRETE"
    assert detail.card.target_description == "Underground C2 node near runway"

    target_service.update_target_card(
        UpdateTargetCardRequest(
            target_card_id=target_id,
            label="TGT-DETAIL",
            priority_score=3,
            complexity_score=3,
            profile=TargetProfileFields(
                target_type="TANK",
                target_subtype="MAIN BATTLE TANK",
                material_class="STEEL",
                target_description="Updated notes",
            ),
        )
    )
    updated = target_service.get_target_detail(target_id)
    assert updated is not None
    assert updated.card.target_type == "TANK"
    assert updated.card.target_subtype == "MAIN BATTLE TANK"
    assert updated.card.material_class == "STEEL"
    assert updated.card.target_description == "Updated notes"


def test_target_card_supports_multiple_coordinates(tmp_path: Path) -> None:
    scenario_service, target_service = build_target_service(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Multi Coordinate Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(
            scenario_id=scenario_id,
            label="TGT-001",
        )
    )
    target_service.save_target_coordinates(
        SaveTargetCoordinatesRequest(
            target_card_id=target_id,
            scenario_id=scenario_id,
            coordinates=[
                TargetCoordinateInput(
                    label="P1",
                    map_lat=14.0,
                    map_lng=100.0,
                    is_primary=True,
                ),
                TargetCoordinateInput(
                    label="P2",
                    map_lat=14.1,
                    map_lng=100.2,
                    is_primary=False,
                ),
            ],
        )
    )

    detail = target_service.get_target_detail(target_id)
    markers = target_service.list_map_markers(scenario_id)

    assert detail is not None
    assert len(detail.coordinates) == 2
    assert detail.map_lat == 14.0
    assert detail.map_lng == 100.0
    assert len(markers) == 2
    assert markers[0]["isPrimary"] is True
    assert markers[1]["pointCount"] == 2


def test_target_search_and_guardrail_block(tmp_path: Path) -> None:
    scenario_service, target_service = build_target_service(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Filter Scenario")
    )
    target_service.create_target_card(
        CreateTargetCardRequest(
            scenario_id=scenario_id,
            label="Support Node",
        )
    )

    filtered = target_service.list_target_cards(
        scenario_id,
        TargetFilterParams(search_text="support"),
    )
    assert len(filtered) == 1

    try:
        target_service.create_target_card(
            CreateTargetCardRequest(
                scenario_id=scenario_id,
                label="real target nomination",
            )
        )
        blocked = False
    except ValueError:
        blocked = True
    assert blocked
