from __future__ import annotations

from pathlib import Path

from maap_app.modules.detection.service import YoloDetectionService


def test_yolo_detection_requires_local_model_weight(tmp_path: Path) -> None:
    service = YoloDetectionService(tmp_path, project_root=tmp_path)

    result = service.run(
        target={"targetCardId": "TGT-001", "lat": 16.0, "lng": 100.0},
        model_name="Vehicle Detector",
        radius_m=250,
    )

    assert result.ok is False
    assert result.objects == []
    assert "YOLO model weight not found" in result.message


def test_resolve_model_missing_when_trained_slot_not_installed(tmp_path: Path) -> None:
    service = YoloDetectionService(tmp_path, project_root=tmp_path)

    model_path = service._resolve_model_path("Building Detector")

    assert model_path is None


def test_resolve_model_uses_project_root_building_model(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    project_model = project_root / "building-seg.pt"
    project_model.write_bytes(b"project-model")

    legacy_models = tmp_path / "models"
    legacy_models.mkdir()
    (legacy_models / "building-seg.pt").write_bytes(b"legacy-model")

    service = YoloDetectionService(tmp_path, project_root=project_root)
    model_path = service._resolve_model_path("Building Detector")

    assert model_path == project_model.resolve()


def test_pixel_polygon_to_lat_lng_uses_target_center_and_radius(tmp_path: Path) -> None:
    service = YoloDetectionService(tmp_path)

    polygon = service._pixel_polygon_to_lat_lng(
        [[50, 50], [150, 50], [150, 150], [50, 150]],
        image_w=200,
        image_h=200,
        center_lat=16.0,
        center_lng=100.0,
        radius_m=100,
    )

    assert len(polygon) == 4
    assert polygon[0][0] > 16.0
    assert polygon[0][1] < 100.0
    assert polygon[2][0] < 16.0
    assert polygon[2][1] > 100.0


def test_polygon_min_distance_supports_radius_filter(tmp_path: Path) -> None:
    service = YoloDetectionService(tmp_path)
    near_polygon = service._pixel_polygon_to_lat_lng(
        [[95, 95], [105, 95], [105, 105], [95, 105]],
        image_w=200,
        image_h=200,
        center_lat=16.0,
        center_lng=100.0,
        radius_m=60,
    )
    far_polygon = service._pixel_polygon_to_lat_lng(
        [[180, 95], [190, 95], [190, 105], [180, 105]],
        image_w=200,
        image_h=200,
        center_lat=16.0,
        center_lng=100.0,
        radius_m=60,
    )

    assert service._polygon_min_distance_m(16.0, 100.0, near_polygon) < 20
    assert service._polygon_min_distance_m(16.0, 100.0, far_polygon) > 20


def test_detection_capture_radius_scales_with_zoom() -> None:
    from maap_app.modules.detection.service import detection_capture_radius_m

    assert detection_capture_radius_m(120, 4) == 150
    assert detection_capture_radius_m(120, 1) == 240
    assert detection_capture_radius_m(120, 4) < detection_capture_radius_m(120, 1)
    assert detection_capture_radius_m(80, 4) >= 100
