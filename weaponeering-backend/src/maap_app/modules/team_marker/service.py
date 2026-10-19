from __future__ import annotations

from uuid import uuid4

from maap_app.modules.audit.service import AuditService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.team_marker.constants import (
    DEFAULT_RADAR_RADIUS_M,
    MAX_RADAR_RADIUS_M,
    MIN_RADAR_RADIUS_M,
    UNIT_TYPE_PREFIXES,
    VALID_UNIT_TYPES,
)
from maap_app.modules.team_marker.models import ScenarioTeamMarker
from maap_app.modules.team_marker.repository import TeamMarkerRepository

_VALID_SIDES = frozenset({"blue", "red"})


class TeamMarkerService:
    def __init__(
        self,
        repository: TeamMarkerRepository,
        scenario_repository: ScenarioRepository,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.scenario_repository = scenario_repository
        self.audit_service = audit_service

    def create_marker(
        self,
        *,
        scenario_id: str,
        side: str,
        unit_type: str = "generic",
        label: str,
        map_lat: float,
        map_lng: float,
        radius_m: float | None = None,
    ) -> str:
        normalized_side = side.strip().lower()
        if normalized_side not in _VALID_SIDES:
            raise ValueError("ฝ่ายต้องเป็น blue หรือ red")
        normalized_unit_type = unit_type.strip().lower() or "generic"
        if normalized_unit_type not in VALID_UNIT_TYPES:
            raise ValueError("ประเภทหน่วยไม่ถูกต้อง")
        clean_label = label.strip()
        if not clean_label:
            raise ValueError("กรุณาระบุชื่อหน่วย")
        normalized_radius = self._normalize_radius(
            normalized_unit_type,
            radius_m,
        )
        if self.scenario_repository.get_scenario(scenario_id) is None:
            raise ValueError("ไม่พบ scenario นี้")

        marker_id = str(uuid4())
        self.repository.insert_marker(
            marker_id=marker_id,
            scenario_id=scenario_id,
            side=normalized_side,
            unit_type=normalized_unit_type,
            label=clean_label,
            map_lat=map_lat,
            map_lng=map_lng,
            radius_m=normalized_radius,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="scenario_team_marker_created",
            entity_type="scenario_team_marker",
            entity_id=marker_id,
            details={
                "scenario_id": scenario_id,
                "side": normalized_side,
                "unit_type": normalized_unit_type,
                "label": clean_label,
                "map_lat": map_lat,
                "map_lng": map_lng,
                "radius_m": normalized_radius,
            },
        )
        return marker_id

    @staticmethod
    def _normalize_radius(unit_type: str, radius_m: float | None) -> float | None:
        if unit_type != "radar":
            return None
        value = DEFAULT_RADAR_RADIUS_M if radius_m is None else float(radius_m)
        if value < MIN_RADAR_RADIUS_M or value > MAX_RADAR_RADIUS_M:
            raise ValueError(
                f"รัศมีเรดาร์ต้องอยู่ระหว่าง {MIN_RADAR_RADIUS_M:.0f}–"
                f"{MAX_RADAR_RADIUS_M:.0f} เมตร"
            )
        return value

    def list_markers(self, scenario_id: str) -> list[ScenarioTeamMarker]:
        return self.repository.list_markers(scenario_id)

    def list_map_markers(self, scenario_id: str) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for marker in self.repository.list_markers(scenario_id):
            payload: dict[str, object] = {
                "id": marker.id,
                "side": marker.side,
                "unitType": marker.unit_type,
                "label": marker.label,
                "lat": marker.map_lat,
                "lng": marker.map_lng,
            }
            if marker.radius_m is not None:
                payload["radiusM"] = marker.radius_m
            items.append(payload)
        return items

    @staticmethod
    def default_marker_name(side: str, unit_type: str, existing_count: int) -> str:
        normalized_side = side.strip().lower()
        normalized_unit_type = unit_type.strip().lower() or "generic"
        side_prefix = "BLUE" if normalized_side == "blue" else "RED"
        unit_prefix = UNIT_TYPE_PREFIXES.get(normalized_unit_type, "")
        if unit_prefix:
            return f"{unit_prefix}-{side_prefix}-{existing_count + 1:02d}"
        return f"{side_prefix}-{existing_count + 1:02d}"

    def delete_marker(self, marker_id: str) -> None:
        if not self.repository.delete_marker(marker_id):
            raise ValueError("ไม่พบหน่วยบนแผนที่")
        self.audit_service.record_event(
            actor="local_user",
            event_type="scenario_team_marker_deleted",
            entity_type="scenario_team_marker",
            entity_id=marker_id,
            details={},
        )
