from __future__ import annotations

from pathlib import Path

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.detection.persistence_service import TargetDetectionService
from maap_app.modules.detection.repository import TargetDetectionRepository
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.schemas import CreateTargetCardRequest
from maap_app.modules.target.service import TargetService


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
    target_repository = TargetRepository(database)
    target_service = TargetService(
        repository=target_repository,
        scenario_repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    detection_service = TargetDetectionService(
        repository=TargetDetectionRepository(database),
        target_repository=target_repository,
        audit_service=audit_service,
    )
    return scenario_service, target_service, detection_service


def _sample_objects(target_id: str) -> list[dict]:
    return [
        {
            "id": f"{target_id}-yolo-1",
            "targetCardId": target_id,
            "label": "Building",
            "objectType": "building",
            "model": "Building Detector",
            "risk": "high",
            "confidence": 0.87,
            "lat": 16.01,
            "lng": 100.01,
            "polygon": [[16.011, 100.011], [16.012, 100.012], [16.010, 100.012]],
        },
        {
            "id": f"{target_id}-yolo-2",
            "targetCardId": target_id,
            "label": "Building",
            "objectType": "building",
            "model": "Building Detector",
            "risk": "medium",
            "confidence": 0.62,
            "lat": 16.02,
            "lng": 100.02,
            "polygon": [[16.021, 100.021], [16.022, 100.022], [16.020, 100.022]],
        },
    ]


def test_save_detection_run_links_to_target_and_reloads_for_map(tmp_path: Path) -> None:
    scenario_service, target_service, detection_service = _build_services(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Detection Persistence Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-DET")
    )

    run_id = detection_service.save_detection_run(
        scenario_id=scenario_id,
        target_card_id=target_id,
        target_coordinate_id=f"legacy-{target_id}",
        model_name="Building Detector",
        model_file_name="building-seg.pt",
        radius_m=120,
        capture_radius_m=480,
        source_image_name=f"{target_id}.png",
        detection_message="detected 2 object(s)",
        objects=_sample_objects(target_id),
    )

    saved = detection_service.get_run_for_target(target_id)
    assert saved is not None
    assert saved.id == run_id
    assert saved.target_card_id == target_id
    assert saved.object_count == 2
    assert len(saved.objects) == 2

    map_objects = detection_service.list_map_objects_for_scenario(scenario_id)
    assert len(map_objects) == 2
    assert map_objects[0]["targetCardId"] == target_id
    assert map_objects[0]["label"] == "Building"
    assert len(map_objects[0]["polygon"]) == 3


def test_save_detection_run_replaces_previous_buildings_for_same_coordinate(
    tmp_path: Path,
) -> None:
    scenario_service, target_service, detection_service = _build_services(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Detection Replace Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-REPLACE")
    )

    first_run_id = detection_service.save_detection_run(
        scenario_id=scenario_id,
        target_card_id=target_id,
        target_coordinate_id=f"legacy-{target_id}",
        model_name="Building Detector",
        model_file_name="building-seg.pt",
        radius_m=120,
        capture_radius_m=480,
        source_image_name=f"{target_id}.png",
        detection_message="detected 2 object(s)",
        objects=_sample_objects(target_id),
    )
    second_run_id = detection_service.save_detection_run(
        scenario_id=scenario_id,
        target_card_id=target_id,
        target_coordinate_id=f"legacy-{target_id}",
        model_name="Building Detector",
        model_file_name="building-seg.pt",
        radius_m=120,
        capture_radius_m=480,
        source_image_name=f"{target_id}.png",
        detection_message="detected 1 object(s)",
        objects=[_sample_objects(target_id)[0]],
    )

    assert first_run_id == second_run_id
    saved = detection_service.get_run_for_target(target_id)
    assert saved is not None
    assert saved.object_count == 1
    assert len(saved.objects) == 1

    map_objects = detection_service.list_map_objects_for_scenario(scenario_id)
    assert len(map_objects) == 1
    assert map_objects[0]["id"] == f"{target_id}-yolo-1"


def test_save_detection_run_supports_multiple_coordinates(tmp_path: Path) -> None:
    scenario_service, target_service, detection_service = _build_services(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Detection Multi Coordinate Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-MULTI-DET")
    )
    from maap_app.modules.target.schemas import SaveTargetCoordinatesRequest, TargetCoordinateInput

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
    assert detail is not None
    coord_ids = [coord.id for coord in detail.coordinates]
    assert len(coord_ids) == 2

    detection_service.save_detection_run(
        scenario_id=scenario_id,
        target_card_id=target_id,
        target_coordinate_id=coord_ids[0],
        model_name="Building Detector",
        model_file_name="building-seg.pt",
        radius_m=120,
        capture_radius_m=480,
        source_image_name="p1.png",
        detection_message="detected 2 object(s)",
        objects=_sample_objects(target_id),
    )
    detection_service.save_detection_run(
        scenario_id=scenario_id,
        target_card_id=target_id,
        target_coordinate_id=coord_ids[1],
        model_name="Building Detector",
        model_file_name="building-seg.pt",
        radius_m=120,
        capture_radius_m=480,
        source_image_name="p2.png",
        detection_message="detected 1 object(s)",
        objects=[_sample_objects(target_id)[0]],
    )

    runs = detection_service.list_runs_for_target(target_id)
    assert len(runs) == 2
    assert runs[0].object_count in {1, 2}
    assert sum(run.object_count for run in runs) == 3

    map_objects = detection_service.list_map_objects_for_scenario(scenario_id)
    assert len(map_objects) == 3
    assert {obj["coordinateId"] for obj in map_objects} == set(coord_ids)


def test_save_detection_run_rejects_target_from_other_scenario(tmp_path: Path) -> None:
    scenario_service, target_service, detection_service = _build_services(tmp_path)
    scenario_a = scenario_service.create_scenario(
        CreateScenarioRequest(name="Scenario A")
    )
    scenario_b = scenario_service.create_scenario(
        CreateScenarioRequest(name="Scenario B")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_a, label="TGT-A")
    )

    try:
        detection_service.save_detection_run(
            scenario_id=scenario_b,
            target_card_id=target_id,
            target_coordinate_id=f"legacy-{target_id}",
            model_name="Building Detector",
            model_file_name="building-seg.pt",
            radius_m=120,
            capture_radius_m=480,
            source_image_name=f"{target_id}.png",
            detection_message="detected 1 object(s)",
            objects=[_sample_objects(target_id)[0]],
        )
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_manual_detection_object_add_and_delete(tmp_path: Path) -> None:
    scenario_service, target_service, detection_service = _build_services(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Manual Detection Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-MANUAL")
    )
    coordinate_id = f"legacy-{target_id}"

    detection_service.save_detection_run(
        scenario_id=scenario_id,
        target_card_id=target_id,
        target_coordinate_id=coordinate_id,
        model_name="Building Detector",
        model_file_name="building-seg.pt",
        radius_m=120,
        capture_radius_m=480,
        source_image_name=f"{target_id}.png",
        detection_message="detected 1 object(s)",
        objects=[_sample_objects(target_id)[0]],
    )

    added_id = detection_service.add_manual_detection_object(
        scenario_id=scenario_id,
        target_card_id=target_id,
        target_coordinate_id=coordinate_id,
        lat=16.03,
        lng=100.03,
        risk_level="low",
    )
    objects = detection_service.list_objects_for_coordinate(target_id, coordinate_id)
    assert len(objects) == 2
    assert any(item["id"] == added_id for item in objects)

    remaining = detection_service.delete_detection_object(
        scenario_id=scenario_id,
        target_card_id=target_id,
        target_coordinate_id=coordinate_id,
        map_object_id=added_id,
    )
    assert remaining == 1
    assert len(detection_service.list_objects_for_coordinate(target_id, coordinate_id)) == 1
