from __future__ import annotations

import asyncio
import tempfile
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from maap_app.modules.detection.risk_direction import (
    RiskDirectionObject,
    calculate_lowest_risk_direction,
)
from maap_app.modules.detection.service import (
    DETECTION_ZOOM_DEFAULT,
    DETECTION_ZOOM_MAX,
    DETECTION_ZOOM_MIN,
    MODEL_FILES,
    YoloDetectionService,
    detection_capture_radius_m,
)
from weaponeering_api.models import User
from weaponeering_api.models.target import TargetCard, TargetCoordinate
from weaponeering_api.schemas.detection import (
    DetectionObjectIn,
    DetectionRunOut,
    DetectionRunUpsert,
)
from weaponeering_api.services import detection_service

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(
    __import__("os").environ.get(
        "WEAPONEERING_DATA_DIR",
        str(PROJECT_ROOT / "data"),
    )
)


def available_model_names() -> list[str]:
    return list(MODEL_FILES.keys())


def resolve_project_root() -> Path:
    return PROJECT_ROOT


def build_risk_direction_payload(
    *,
    lat: float,
    lng: float,
    objects: list[dict],
    scan_radius_m: float,
) -> dict:
    risk_objects = [
        RiskDirectionObject(
            lat=float(obj["lat"]),
            lng=float(obj["lng"]),
            risk_level=str(obj.get("risk") or obj.get("risk_level") or "medium"),
            label=str(obj.get("label") or obj.get("object_label") or "object"),
        )
        for obj in objects
        if obj.get("lat") is not None and obj.get("lng") is not None
    ]
    result = calculate_lowest_risk_direction(
        target_lat=lat,
        target_lng=lng,
        objects=risk_objects,
        scan_radius_m=float(scan_radius_m),
    )
    return result.to_map_payload()


def _yolo_objects_to_upsert(objects: list[dict]) -> list[DetectionObjectIn]:
    items: list[DetectionObjectIn] = []
    for index, obj in enumerate(objects):
        items.append(
            DetectionObjectIn(
                map_object_id=str(obj.get("id") or f"yolo-{index + 1}"),
                object_label=str(obj.get("label") or "Object"),
                object_type=str(obj.get("objectType") or "object"),
                risk_level=str(obj.get("risk") or "medium"),
                confidence=float(obj.get("confidence") or 0.0),
                center_lat=float(obj["lat"]),
                center_lng=float(obj["lng"]),
                polygon_json=obj.get("polygon") or [],
                sort_order=index,
            )
        )
    return items


def run_yolo_on_bytes(
    *,
    image_bytes: bytes,
    image_suffix: str,
    target_card_id: str,
    lat: float,
    lng: float,
    model_name: str,
    radius_m: int,
    zoom_level: int,
) -> tuple[list[dict], str, str | None, int]:
    """Sync YOLO inference. Returns (objects, message, model_file_name, capture_radius_m)."""
    zoom = max(DETECTION_ZOOM_MIN, min(DETECTION_ZOOM_MAX, zoom_level))
    capture_radius = detection_capture_radius_m(radius_m, zoom)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    source_dir = DATA_DIR / "detection_sources"
    source_dir.mkdir(parents=True, exist_ok=True)

    suffix = image_suffix if image_suffix.startswith(".") else f".{image_suffix or 'png'}"
    with tempfile.NamedTemporaryFile(
        dir=source_dir,
        prefix=f"{target_card_id}_",
        suffix=suffix,
        delete=False,
    ) as handle:
        handle.write(image_bytes)
        temp_path = Path(handle.name)

    # Keep a stable copy for desktop-style fallback paths.
    stable_path = source_dir / f"{target_card_id}{suffix}"
    stable_path.write_bytes(image_bytes)

    service = YoloDetectionService(data_dir=DATA_DIR, project_root=PROJECT_ROOT)
    result = service.run_on_image_path(
        target={
            "targetCardId": target_card_id,
            "lat": lat,
            "lng": lng,
        },
        model_name=model_name,
        radius_m=radius_m,
        capture_radius_m=capture_radius,
        image_path=temp_path,
    )
    try:
        temp_path.unlink(missing_ok=True)
    except OSError:
        pass

    if not result.ok:
        raise RuntimeError(result.message or "Detection failed")

    model_file = result.model_path.name if result.model_path else None
    return result.objects, result.message, model_file, capture_radius


async def execute_detection_run(
    db: AsyncSession,
    *,
    user: User,
    scenario_id: uuid.UUID,
    target_card_id: uuid.UUID,
    target_coordinate_id: uuid.UUID,
    model_name: str,
    radius_m: int,
    zoom_level: int,
    image_bytes: bytes,
    image_filename: str,
) -> dict:
    target = await db.get(TargetCard, target_card_id)
    if target is None or target.scenario_id != scenario_id:
        raise ValueError("ไม่พบ Target ใน scenario นี้")

    coord = await db.get(TargetCoordinate, target_coordinate_id)
    if coord is None or coord.target_card_id != target_card_id:
        raise ValueError("ไม่พบพิกัดของเป้าหมาย")

    if model_name not in MODEL_FILES:
        raise ValueError(
            f"ไม่รู้จักโมเดล {model_name}. ใช้ได้: {', '.join(MODEL_FILES)}"
        )

    suffix = Path(image_filename or "capture.png").suffix or ".png"
    objects, message, model_file, capture_radius = await asyncio.to_thread(
        run_yolo_on_bytes,
        image_bytes=image_bytes,
        image_suffix=suffix,
        target_card_id=str(target_card_id),
        lat=coord.map_lat,
        lng=coord.map_lng,
        model_name=model_name,
        radius_m=radius_m,
        zoom_level=zoom_level,
    )

    # Check for existing scenario detections within radius_m of the new coordinate
    # (e.g. when placing a new point near a previous circle)
    existing_runs = await detection_service.list_detection_runs(
        db, scenario_id=scenario_id
    )
    for er in existing_runs:
        if er.target_card_id == target_card_id and er.target_coordinate_id == target_coordinate_id:
            continue
        for obj in er.objects:
            obj_lat = float(obj.center_lat)
            obj_lng = float(obj.center_lng)
            dist_to_new_target = YoloDetectionService._distance_m(
                coord.map_lat, coord.map_lng, obj_lat, obj_lng
            )
            if dist_to_new_target <= radius_m:
                duplicate = any(
                    YoloDetectionService._distance_m(
                        float(o["lat"]), float(o["lng"]), obj_lat, obj_lng
                    ) < 8.0
                    for o in objects
                )
                if not duplicate:
                    objects.append(
                        {
                            "id": f"carryover-{obj.id}",
                            "label": obj.object_label,
                            "objectType": obj.object_type,
                            "confidence": float(obj.confidence or 0.8),
                            "lat": obj_lat,
                            "lng": obj_lng,
                            "polygon": obj.polygon_json if isinstance(obj.polygon_json, list) else [],
                        }
                    )

    # Recalculate distance and damage risk relative to the new target coordinate for ALL objects
    for obj in objects:
        dist = YoloDetectionService._distance_m(
            coord.map_lat, coord.map_lng, float(obj["lat"]), float(obj["lng"])
        )
        calculated_risk = YoloDetectionService._risk_for_distance(dist, radius_m)
        obj["risk"] = calculated_risk
        obj["risk_level"] = calculated_risk
        obj["distance_m"] = round(dist, 1)

    message = f"พบ {len(objects)} อาคารในรัศมี {radius_m} ม. (คำนวณระดับความเสี่ยงตามระยะจุดเป้าหมายใหม่แล้ว)"

    body = DetectionRunUpsert(
        scenario_id=scenario_id,
        target_card_id=target_card_id,
        target_coordinate_id=target_coordinate_id,
        model_name=model_name,
        model_file_name=model_file,
        radius_m=radius_m,
        capture_radius_m=capture_radius,
        source_image_name=image_filename or f"{target_card_id}{suffix}",
        detection_message=message,
        objects=_yolo_objects_to_upsert(objects),
    )
    run = await detection_service.upsert_detection_run(db, body, user)
    risk = build_risk_direction_payload(
        lat=coord.map_lat,
        lng=coord.map_lng,
        objects=objects,
        scan_radius_m=radius_m,
    )
    return {
        "run": DetectionRunOut.model_validate(run),
        "lowestRiskDirection": risk,
        "message": message,
        "objectCount": len(objects),
        "captureRadiusM": capture_radius,
        "zoomLevel": max(DETECTION_ZOOM_MIN, min(DETECTION_ZOOM_MAX, zoom_level)),
        "modelName": model_name,
        "defaults": {
            "zoomDefault": DETECTION_ZOOM_DEFAULT,
            "models": available_model_names(),
        },
    }


async def risk_direction_for_coordinate(
    db: AsyncSession,
    *,
    target_card_id: uuid.UUID,
    target_coordinate_id: uuid.UUID,
) -> dict:
    target = await db.get(TargetCard, target_card_id)
    if target is None:
        raise ValueError("ไม่พบ Target")

    coord = await db.get(TargetCoordinate, target_coordinate_id)
    if coord is None or coord.target_card_id != target_card_id:
        raise ValueError("ไม่พบพิกัดของเป้าหมาย")

    run = await detection_service.get_detection_run_for_coordinate(
        db, target_card_id, target_coordinate_id
    )
    objects = []
    radius_m = 120.0
    if run is not None and run.objects:
        radius_m = float(run.radius_m)
        for obj in run.objects:
            dist = YoloDetectionService._distance_m(
                coord.map_lat, coord.map_lng, float(obj.center_lat), float(obj.center_lng)
            )
            objects.append(
                {
                    "lat": obj.center_lat,
                    "lng": obj.center_lng,
                    "risk": YoloDetectionService._risk_for_distance(dist, int(radius_m)),
                    "label": obj.object_label,
                }
            )
    else:
        # Fallback for targets near existing scenario detections
        all_runs = await detection_service.list_detection_runs(
            db, scenario_id=target.scenario_id
        )
        seen = set()
        for r in all_runs:
            for obj in r.objects:
                key = (round(obj.center_lat, 6), round(obj.center_lng, 6))
                if key in seen:
                    continue
                seen.add(key)
                dist = YoloDetectionService._distance_m(
                    coord.map_lat, coord.map_lng, float(obj.center_lat), float(obj.center_lng)
                )
                if dist <= radius_m:
                    objects.append(
                        {
                            "lat": obj.center_lat,
                            "lng": obj.center_lng,
                            "risk": YoloDetectionService._risk_for_distance(dist, int(radius_m)),
                            "label": obj.object_label,
                        }
                    )
    return build_risk_direction_payload(
        lat=coord.map_lat,
        lng=coord.map_lng,
        objects=objects,
        scan_radius_m=radius_m,
    )
