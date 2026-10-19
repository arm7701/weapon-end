from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from maap_app.modules.audit.service import AuditService
from maap_app.modules.detection.geometry import square_building_polygon
from maap_app.modules.detection.models import TargetMapDetectionRun
from maap_app.modules.detection.repository import TargetDetectionRepository
from maap_app.modules.detection.risk_direction import (
    RiskDirectionObject,
    calculate_lowest_risk_direction,
)
from maap_app.modules.target.repository import TargetRepository


class TargetDetectionService:
    def __init__(
        self,
        repository: TargetDetectionRepository,
        target_repository: TargetRepository,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.target_repository = target_repository
        self.audit_service = audit_service

    def save_detection_run(
        self,
        *,
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
    ) -> str:
        target = self.target_repository.get_target_card(target_card_id)
        if target is None or target.scenario_id != scenario_id:
            raise ValueError("ไม่พบ Target ใน scenario นี้")

        existing = self.repository.get_run_for_coordinate(
            target_card_id,
            target_coordinate_id,
        )
        run_id = existing.id if existing else str(uuid4())
        persisted_objects = [{**obj, "db_id": str(uuid4())} for obj in objects]
        self.repository.upsert_detection_run(
            run_id=run_id,
            scenario_id=scenario_id,
            target_card_id=target_card_id,
            target_coordinate_id=target_coordinate_id,
            model_name=model_name,
            model_file_name=model_file_name,
            radius_m=radius_m,
            capture_radius_m=capture_radius_m,
            source_image_name=source_image_name,
            detection_message=detection_message,
            objects=persisted_objects,
        )
        saved = self.repository.get_run_for_coordinate(
            target_card_id,
            target_coordinate_id,
        )
        saved_run_id = saved.id if saved is not None else run_id
        self.audit_service.record_event(
            actor="local_user",
            event_type="target_map_detection_saved",
            entity_type="target_map_detection_run",
            entity_id=saved_run_id,
            details={
                "target_card_id": target_card_id,
                "target_coordinate_id": target_coordinate_id,
                "scenario_id": scenario_id,
                "model_name": model_name,
                "object_count": len(objects),
                "radius_m": radius_m,
            },
        )
        return saved_run_id

    def get_run_for_target(self, target_card_id: str) -> TargetMapDetectionRun | None:
        primary_id = self._primary_coordinate_id(target_card_id)
        if primary_id is not None:
            run = self.repository.get_run_for_coordinate(target_card_id, primary_id)
            if run is not None:
                return run
        return self.repository.get_run_for_target(target_card_id)

    def get_run_for_coordinate(
        self,
        target_card_id: str,
        target_coordinate_id: str,
    ) -> TargetMapDetectionRun | None:
        return self.repository.get_run_for_coordinate(
            target_card_id,
            target_coordinate_id,
        )

    def list_runs_for_target(self, target_card_id: str) -> list[TargetMapDetectionRun]:
        return self.repository.list_runs_for_target(target_card_id)

    def list_map_objects_for_scenario(self, scenario_id: str) -> list[dict[str, Any]]:
        runs = self.repository.list_runs_for_scenario(scenario_id)
        objects: list[dict[str, Any]] = []
        for run in runs:
            for obj in run.objects:
                objects.append(self._to_map_object(obj, run))
        return objects

    def list_objects_for_target(self, target_card_id: str) -> list[dict[str, Any]]:
        runs = self.repository.list_runs_for_target(target_card_id)
        objects: list[dict[str, Any]] = []
        for run in runs:
            for obj in run.objects:
                objects.append(self._to_map_object(obj, run))
        return objects

    def build_lowest_risk_direction(
        self,
        *,
        target_card_id: str,
        target_coordinate_id: str | None,
        lat: float,
        lng: float,
        fallback_radius_m: float,
    ) -> dict[str, object]:
        run: TargetMapDetectionRun | None = None
        if target_coordinate_id:
            run = self.repository.get_run_for_coordinate(
                target_card_id,
                target_coordinate_id,
            )
        if run is None:
            run = self.get_run_for_target(target_card_id)
        objects = [
            RiskDirectionObject(
                lat=obj.center_lat,
                lng=obj.center_lng,
                risk_level=obj.risk_level,
                label=obj.object_label,
            )
            for obj in (run.objects if run is not None else [])
        ]
        scan_radius_m = float(run.radius_m) if run is not None else fallback_radius_m
        result = calculate_lowest_risk_direction(
            target_lat=lat,
            target_lng=lng,
            objects=objects,
            scan_radius_m=scan_radius_m,
        )
        return result.to_map_payload()

    def list_objects_for_coordinate(
        self,
        target_card_id: str,
        target_coordinate_id: str,
    ) -> list[dict[str, Any]]:
        run = self.repository.get_run_for_coordinate(
            target_card_id,
            target_coordinate_id,
        )
        if run is None:
            return []
        return [self._to_map_object(obj, run) for obj in run.objects]

    def delete_detection_object(
        self,
        *,
        scenario_id: str,
        target_card_id: str,
        target_coordinate_id: str,
        map_object_id: str,
    ) -> int:
        run = self.repository.get_run_for_coordinate(
            target_card_id,
            target_coordinate_id,
        )
        if run is None:
            raise ValueError("ยังไม่มีผล Detection สำหรับพิกัดนี้")
        remaining = [
            self._to_map_object(obj, run)
            for obj in run.objects
            if obj.map_object_id != map_object_id
        ]
        if len(remaining) == len(run.objects):
            raise ValueError("ไม่พบอาคารที่เลือก")
        self._rewrite_run_objects(
            run=run,
            scenario_id=scenario_id,
            objects=remaining,
            detection_message=(
                f"ลบอาคารแล้ว · เหลือ {len(remaining)} รายการ (คำนวณทิศทางเข้า-ออกใหม่)"
            ),
            event_type="target_map_detection_object_deleted",
        )
        return len(remaining)

    def add_manual_detection_object(
        self,
        *,
        scenario_id: str,
        target_card_id: str,
        target_coordinate_id: str,
        lat: float,
        lng: float,
        risk_level: str = "medium",
        label: str = "Building",
    ) -> str:
        run = self.repository.get_run_for_coordinate(
            target_card_id,
            target_coordinate_id,
        )
        map_object_id = f"{target_card_id}-manual-{uuid4().hex[:8]}"
        polygon = square_building_polygon(lat, lng)
        new_object = {
            "id": map_object_id,
            "targetCardId": target_card_id,
            "label": label,
            "objectType": "building",
            "risk": risk_level,
            "confidence": 1.0,
            "lat": lat,
            "lng": lng,
            "polygon": polygon,
        }
        if run is None:
            self.save_detection_run(
                scenario_id=scenario_id,
                target_card_id=target_card_id,
                target_coordinate_id=target_coordinate_id,
                model_name="Manual",
                model_file_name=None,
                radius_m=120,
                capture_radius_m=120,
                source_image_name=None,
                detection_message="เพิ่มอาคารด้วยตนเอง · คำนวณทิศทางเข้า-ออกใหม่",
                objects=[new_object],
            )
            return map_object_id
        objects = [self._to_map_object(obj, run) for obj in run.objects]
        objects.append(new_object)
        self._rewrite_run_objects(
            run=run,
            scenario_id=scenario_id,
            objects=objects,
            detection_message=(
                f"เพิ่มอาคารด้วยตนเอง · รวม {len(objects)} รายการ"
                " (คำนวณทิศทางเข้า-ออกใหม่)"
            ),
            event_type="target_map_detection_object_added",
        )
        return map_object_id

    def update_detection_object_risk(
        self,
        *,
        scenario_id: str,
        target_card_id: str,
        target_coordinate_id: str,
        map_object_id: str,
        risk_level: str,
    ) -> None:
        run = self.repository.get_run_for_coordinate(
            target_card_id,
            target_coordinate_id,
        )
        if run is None:
            raise ValueError("ยังไม่มีผล Detection สำหรับพิกัดนี้")
        updated: list[dict[str, Any]] = []
        found = False
        for obj in run.objects:
            payload = self._to_map_object(obj, run)
            if obj.map_object_id == map_object_id:
                payload["risk"] = risk_level
                found = True
            updated.append(payload)
        if not found:
            raise ValueError("ไม่พบอาคารที่เลือก")
        self._rewrite_run_objects(
            run=run,
            scenario_id=scenario_id,
            objects=updated,
            detection_message=(
                f"ปรับระดับความเสี่ยงอาคาร · รวม {len(updated)} รายการ"
                " (คำนวณทิศทางเข้า-ออกใหม่)"
            ),
            event_type="target_map_detection_object_updated",
        )

    def _rewrite_run_objects(
        self,
        *,
        run: TargetMapDetectionRun,
        scenario_id: str,
        objects: list[dict[str, Any]],
        detection_message: str,
        event_type: str,
    ) -> None:
        persisted_objects = [{**obj, "db_id": str(uuid4())} for obj in objects]
        self.repository.upsert_detection_run(
            run_id=run.id,
            scenario_id=scenario_id,
            target_card_id=run.target_card_id,
            target_coordinate_id=run.target_coordinate_id,
            model_name=run.model_name,
            model_file_name=run.model_file_name,
            radius_m=run.radius_m,
            capture_radius_m=run.capture_radius_m,
            source_image_name=run.source_image_name,
            detection_message=detection_message,
            objects=persisted_objects,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type=event_type,
            entity_type="target_map_detection_run",
            entity_id=run.id,
            details={
                "target_card_id": run.target_card_id,
                "target_coordinate_id": run.target_coordinate_id,
                "scenario_id": scenario_id,
                "object_count": len(objects),
            },
        )

    def _primary_coordinate_id(self, target_card_id: str) -> str | None:
        detail = self.target_repository.get_target_detail(target_card_id)
        if detail is None or not detail.coordinates:
            return None
        primary = next(
            (coord for coord in detail.coordinates if coord.is_primary),
            detail.coordinates[0],
        )
        return primary.id

    @staticmethod
    def _to_map_object(
        obj: Any,
        run: TargetMapDetectionRun,
    ) -> dict[str, Any]:
        polygon = json.loads(obj.polygon_json)
        return {
            "id": obj.map_object_id,
            "targetCardId": obj.target_card_id,
            "coordinateId": run.target_coordinate_id,
            "label": obj.object_label,
            "objectType": obj.object_type,
            "model": run.model_name,
            "risk": obj.risk_level,
            "confidence": obj.confidence,
            "lat": obj.center_lat,
            "lng": obj.center_lng,
            "polygon": polygon,
        }
