from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from maap_app.modules.audit.service import AuditService
from maap_app.modules.common import ReviewStatus, clamp_score
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.weaponeering.repository import WeaponeeringRepository
from maap_app.modules.weaponeering.schemas import (
    EFFECT_CATEGORIES,
    CreateAbstractOptionRequest,
    CreateAssessmentRequest,
    UpsertDeploymentPlanRequest,
)
from maap_app.modules.weaponeering.flight_path import (
    FlightProfileSettings,
    FlightWaypointSpec,
    compute_flight_profile,
    format_distance_km,
    format_duration_min,
)
from maap_app.modules.wing_data.repository import WingDataRepository


@dataclass(frozen=True)
class ImportResult:
    batch_id: str
    imported_count: int
    rejected_count: int
    validation_summary: str


class WeaponeeringService:
    def __init__(
        self,
        repository: WeaponeeringRepository,
        target_repository: TargetRepository,
        wing_data_repository: WingDataRepository,
        guardrail_service: GuardrailService,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.target_repository = target_repository
        self.wing_data_repository = wing_data_repository
        self.guardrail_service = guardrail_service
        self.audit_service = audit_service

    def create_abstract_option(self, request: CreateAbstractOptionRequest) -> str:
        if request.effect_category not in EFFECT_CATEGORIES:
            raise ValueError(f"Unsupported effect category: {request.effect_category}")

        option_id = str(uuid4())
        text = (
            f"{request.option_label}\n{request.effect_category}\n"
            f"{request.required_capability_band}\n{request.resource_token_type}"
        )
        if not self.guardrail_service.validate_training_text(
            text=text,
            entity_type="abstract_weaponeering_option",
            entity_id=option_id,
        ):
            raise ValueError("Abstract option text was blocked by guardrail validation.")

        self.repository.insert_abstract_option(
            option_id=option_id,
            scenario_id=request.scenario_id,
            option_label=request.option_label,
            effect_category=request.effect_category,
            required_capability_band=request.required_capability_band,
            resource_token_type=request.resource_token_type,
            estimated_effect_score=clamp_score(request.estimated_effect_score),
            risk_score=clamp_score(request.risk_score),
            logistics_demand_score=clamp_score(request.logistics_demand_score),
            source_module="manual",
            review_status=ReviewStatus.DRAFT,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="abstract_option_created",
            entity_type="abstract_weaponeering_option",
            entity_id=option_id,
            details={"label": request.option_label},
        )
        return option_id

    def archive_abstract_option(self, option_id: str) -> None:
        if self.repository.count_assessments_for_option(option_id) > 0:
            raise ValueError("Cannot archive option referenced by assessments.")
        self.repository.archive_abstract_option(option_id)
        self.audit_service.record_event(
            actor="local_user",
            event_type="abstract_option_archived",
            entity_type="abstract_weaponeering_option",
            entity_id=option_id,
            details={},
        )

    def create_assessment(self, request: CreateAssessmentRequest) -> str:
        assessment_id = str(uuid4())
        if not self.guardrail_service.validate_training_text(
            text=request.rationale,
            entity_type="target_weaponeering_assessment",
            entity_id=assessment_id,
        ):
            raise ValueError("Assessment rationale was blocked by guardrail validation.")

        self.repository.insert_assessment(
            assessment_id=assessment_id,
            target_card_id=request.target_card_id,
            abstract_weaponeering_option_id=request.abstract_weaponeering_option_id,
            suitability_score=clamp_score(request.suitability_score),
            feasibility_score=clamp_score(request.feasibility_score),
            risk_score=clamp_score(request.risk_score),
            rationale=request.rationale,
            generated_by="local_user",
            review_status=ReviewStatus.REQUIRES_REVIEW,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="assessment_created",
            entity_type="target_weaponeering_assessment",
            entity_id=assessment_id,
            details={"target_card_id": request.target_card_id},
        )
        return assessment_id

    def approve_assessment(self, assessment_id: str) -> None:
        self.repository.update_assessment_review_status(
            assessment_id,
            ReviewStatus.APPROVED,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="assessment_updated",
            entity_type="target_weaponeering_assessment",
            entity_id=assessment_id,
            details={"review_status": ReviewStatus.APPROVED},
        )

    def list_abstract_options(self, scenario_id: str):
        return self.repository.list_abstract_options(scenario_id)

    def list_assessments_for_target(self, target_card_id: str):
        return self.repository.list_assessments_for_target(target_card_id)

    def get_deployment_plan_for_target(self, target_card_id: str):
        return self.repository.get_deployment_plan_for_target(target_card_id)

    def list_map_deployment_links(self, scenario_id: str) -> list[dict]:
        links: list[dict] = []
        for plan in self.repository.list_deployment_plans_for_scenario(scenario_id):
            wing = self.wing_data_repository.get_wing(plan.wing_id)
            target = self.target_repository.get_target_detail(plan.target_card_id)
            if wing is None or wing.map_lat is None or wing.map_lng is None:
                continue
            if target is None or target.map_lat is None or target.map_lng is None:
                continue

            takeoff_lat = (
                plan.takeoff_lat if plan.takeoff_lat is not None else wing.map_lat
            )
            takeoff_lng = (
                plan.takeoff_lng if plan.takeoff_lng is not None else wing.map_lng
            )
            outbound_waypoints = [
                FlightWaypointSpec(
                    lat=wp.lat,
                    lng=wp.lng,
                    label=wp.label or "",
                    waypoint_type=wp.waypoint_type,
                    altitude_ft=wp.altitude_ft,
                )
                for wp in plan.waypoints
                if wp.waypoint_type == "fly_through"
            ]
            return_waypoints = [
                FlightWaypointSpec(
                    lat=wp.lat,
                    lng=wp.lng,
                    label=wp.label or "",
                    waypoint_type="return",
                    altitude_ft=wp.altitude_ft,
                )
                for wp in plan.waypoints
                if wp.waypoint_type == "return"
            ]
            flight_path = compute_flight_profile(
                takeoff=(takeoff_lat, takeoff_lng),
                destination=(target.map_lat, target.map_lng),
                outbound_waypoints=outbound_waypoints,
                return_waypoints=return_waypoints,
                ingress_bearing_deg=plan.ingress_bearing_deg,
                ingress_offset_m=plan.ingress_offset_m,
                profile=FlightProfileSettings(
                    cruise_altitude_ft=plan.cruise_altitude_ft,
                    ingress_altitude_ft=plan.ingress_altitude_ft,
                    target_altitude_ft=plan.target_altitude_ft,
                    climb_rate_ft_min=plan.climb_rate_ft_min,
                    descent_rate_ft_min=plan.descent_rate_ft_min,
                    return_enabled=plan.return_enabled,
                    cruise_speed_kt=plan.cruise_speed_kt,
                    climb_speed_kt=plan.climb_speed_kt,
                    descent_speed_kt=plan.descent_speed_kt,
                    ingress_speed_kt=plan.ingress_speed_kt,
                    bank_angle_deg=plan.bank_angle_deg,
                    turn_mode=plan.turn_mode,
                    auto_toc_tod=plan.auto_toc_tod,
                ),
            )
            path_points = [
                {
                    "lat": point.lat,
                    "lng": point.lng,
                    "label": point.label,
                    "pointType": point.point_type,
                    "altitudeFt": round(point.altitude_ft),
                    "phase": point.phase,
                }
                for point in flight_path.points
            ]
            links.append(
                {
                    "linkId": plan.id,
                    "targetCardId": plan.target_card_id,
                    "wingId": plan.wing_id,
                    "label": f"{wing.wing_name} → {target.card.label}",
                    "origin": [takeoff_lat, takeoff_lng],
                    "destination": [target.map_lat, target.map_lng],
                    "path": [[lat, lng] for lat, lng in flight_path.outbound_route],
                    "outboundRoute": [
                        [lat, lng] for lat, lng in flight_path.outbound_route
                    ],
                    "returnRoute": [
                        [lat, lng] for lat, lng in flight_path.return_route
                    ],
                    "routeMarkers": list(flight_path.route_markers),
                    "path3d": [
                        [lat, lng, alt_m]
                        for lat, lng, alt_m in flight_path.path3d
                    ],
                    "returnPath3d": [
                        [lat, lng, alt_m]
                        for lat, lng, alt_m in flight_path.return_path3d
                    ],
                    "waypoints": path_points,
                    "ingressBearingDeg": plan.ingress_bearing_deg,
                    "ingressOffsetM": plan.ingress_offset_m,
                    "cruiseAltitudeFt": plan.cruise_altitude_ft,
                    "ingressAltitudeFt": plan.ingress_altitude_ft,
                    "targetAltitudeFt": plan.target_altitude_ft,
                    "returnEnabled": plan.return_enabled,
                    "trajectoryRoute": list(flight_path.trajectory_samples),
                    "cruiseSpeedKt": plan.cruise_speed_kt,
                    "bankAngleDeg": plan.bank_angle_deg,
                    "turnMode": plan.turn_mode,
                    "totalDistanceM": round(flight_path.total_distance_m, 1),
                    "totalDistanceLabel": format_distance_km(
                        flight_path.total_distance_m
                    ),
                    "totalDurationMin": round(flight_path.total_duration_min, 1),
                    "totalDurationLabel": format_duration_min(
                        flight_path.total_duration_min
                    ),
                    "finalApproachBearingDeg": flight_path.final_approach_bearing_deg,
                    "profileSegments": list(flight_path.profile_segments),
                    "legs": [
                        {
                            "fromIndex": leg.from_index,
                            "toIndex": leg.to_index,
                            "distanceM": round(leg.distance_m, 1),
                            "bearingDeg": round(leg.bearing_deg, 1),
                            "startAltFt": round(leg.start_altitude_ft),
                            "endAltFt": round(leg.end_altitude_ft),
                            "phase": leg.phase,
                            "durationMin": round(leg.duration_min, 1),
                        }
                        for leg in flight_path.legs
                    ],
                    "aircraftCount": plan.total_aircraft_count,
                }
            )
        return links

    def upsert_deployment_plan(self, request: UpsertDeploymentPlanRequest) -> str:
        if not request.aircraft_lines:
            raise ValueError("ต้องระบุเครื่องบินอย่างน้อย 1 รายการ")

        target = self.target_repository.get_target_card(request.target_card_id)
        if target is None or target.scenario_id != request.scenario_id:
            raise ValueError("ไม่พบ Target ใน scenario นี้")

        wing = self.wing_data_repository.get_wing(request.wing_id)
        if wing is None or wing.scenario_id != request.scenario_id:
            raise ValueError("ไม่พบกองบินที่เลือก")

        unit = self.wing_data_repository.get_flying_unit(request.flying_unit_id)
        if unit is None or unit.wing_id != request.wing_id:
            raise ValueError("หน่วยบินต้องอยู่ภายใต้กองบินที่เลือก")

        seen_aircraft: set[str] = set()
        aircraft_lines: list[tuple[str, str, int, int]] = []
        total_count = 0
        for sort_order, line in enumerate(request.aircraft_lines):
            if line.aircraft_count < 1:
                raise ValueError("จำนวนเครื่องบินแต่ละรายการต้องอย่างน้อย 1 ลำ")
            if line.aircraft_id in seen_aircraft:
                raise ValueError("ไม่สามารถเลือกเครื่องบินซ้ำในแผนเดียวกัน")
            seen_aircraft.add(line.aircraft_id)

            aircraft = self.wing_data_repository.get_aircraft(line.aircraft_id)
            if aircraft is None or aircraft.wing_id != request.wing_id:
                raise ValueError("เครื่องบินต้องอยู่ภายใต้กองบินที่เลือก")
            if aircraft.flying_unit_id != request.flying_unit_id:
                raise ValueError("เครื่องบินต้องอยู่ในหน่วยบินที่เลือก")

            aircraft_lines.append(
                (str(uuid4()), line.aircraft_id, line.aircraft_count, sort_order)
            )
            total_count += line.aircraft_count

        if request.takeoff_lat is not None and request.takeoff_lng is None:
            raise ValueError("ต้องระบุ Takeoff LNG คู่กับ Takeoff LAT")
        if request.takeoff_lng is not None and request.takeoff_lat is None:
            raise ValueError("ต้องระบุ Takeoff LAT คู่กับ Takeoff LNG")
        if request.ingress_bearing_deg is not None and not (
            0 <= request.ingress_bearing_deg < 360
        ):
            raise ValueError("ทิศทางเข้าพื้นที่ต้องอยู่ระหว่าง 0–359°")
        if request.ingress_offset_m < 0:
            raise ValueError("ระยะ Ingress ต้องไม่ติดลบ")
        if request.cruise_altitude_ft < 500:
            raise ValueError("ความสูง Cruise ต้องอย่างน้อย 500 ft")
        if request.climb_rate_ft_min < 500 or request.descent_rate_ft_min < 500:
            raise ValueError("อัตราขึ้น/ลง ต้องอย่างน้อย 500 ft/min")

        waypoint_rows: list[
            tuple[str, str, str | None, float, float, int, int | None]
        ] = []
        for sort_order, waypoint in enumerate(request.waypoints):
            waypoint_rows.append(
                (
                    str(uuid4()),
                    waypoint.waypoint_type,
                    waypoint.label or None,
                    waypoint.lat,
                    waypoint.lng,
                    sort_order,
                    waypoint.altitude_ft,
                )
            )

        existing = self.repository.get_deployment_plan_for_target(request.target_card_id)
        plan_id = existing.id if existing else str(uuid4())
        self.repository.upsert_deployment_plan(
            plan_id,
            request.scenario_id,
            request.target_card_id,
            request.wing_id,
            request.flying_unit_id,
            aircraft_lines,
            takeoff_lat=request.takeoff_lat,
            takeoff_lng=request.takeoff_lng,
            ingress_bearing_deg=request.ingress_bearing_deg,
            ingress_offset_m=request.ingress_offset_m,
            cruise_altitude_ft=request.cruise_altitude_ft,
            ingress_altitude_ft=request.ingress_altitude_ft,
            target_altitude_ft=request.target_altitude_ft,
            climb_rate_ft_min=request.climb_rate_ft_min,
            descent_rate_ft_min=request.descent_rate_ft_min,
            return_enabled=request.return_enabled,
            cruise_speed_kt=request.cruise_speed_kt,
            climb_speed_kt=request.climb_speed_kt,
            descent_speed_kt=request.descent_speed_kt,
            ingress_speed_kt=request.ingress_speed_kt,
            bank_angle_deg=request.bank_angle_deg,
            turn_mode=request.turn_mode,
            auto_toc_tod=request.auto_toc_tod,
            waypoints=waypoint_rows,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="deployment_plan_upserted",
            entity_type="target_weaponeering_deployment_plan",
            entity_id=plan_id,
            details={
                "target_card_id": request.target_card_id,
                "wing_id": request.wing_id,
                "aircraft_line_count": len(aircraft_lines),
                "aircraft_count": total_count,
                "waypoint_count": len(waypoint_rows),
                "ingress_bearing_deg": request.ingress_bearing_deg,
                "cruise_altitude_ft": request.cruise_altitude_ft,
                "return_enabled": request.return_enabled,
            },
        )
        return plan_id

    def delete_deployment_plan(self, target_card_id: str) -> None:
        self.repository.delete_deployment_plan(target_card_id)
        self.audit_service.record_event(
            actor="local_user",
            event_type="deployment_plan_deleted",
            entity_type="target_weaponeering_deployment_plan",
            entity_id=target_card_id,
            details={},
        )

    def list_import_batches(self, scenario_id: str):
        return self.repository.list_import_batches(scenario_id)

    def import_from_file(self, scenario_id: str, file_path: Path) -> ImportResult:
        batch_id = str(uuid4())
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            rows = self._parse_json_rows(file_path)
        elif suffix == ".csv":
            rows = self._parse_csv_rows(file_path)
        else:
            raise ValueError("Supported import formats: JSON and CSV.")

        imported = 0
        rejected = 0
        rejection_notes: list[str] = []

        for index, row in enumerate(rows, start=1):
            row_text = json.dumps(row, ensure_ascii=True)
            if not self.guardrail_service.validate_import_payload(
                text=row_text,
                entity_type="weaponeering_import_row",
                entity_id=f"{batch_id}:{index}",
            ):
                rejected += 1
                rejection_notes.append(f"Row {index}: guardrail blocked.")
                self.audit_service.record_event(
                    actor="system",
                    event_type="import_row_rejected",
                    entity_type="weaponeering_import_batch",
                    entity_id=batch_id,
                    details={"row": index, "reason": "guardrail"},
                )
                continue

            target_id = str(row.get("target_card_id", "")).strip()
            option_label = str(row.get("abstract_option_label", "")).strip()
            if not target_id or not option_label:
                rejected += 1
                rejection_notes.append(f"Row {index}: missing target or option label.")
                continue

            target = self.target_repository.get_target_card(target_id)
            if target is None or target.scenario_id != scenario_id:
                rejected += 1
                rejection_notes.append(f"Row {index}: target not in scenario.")
                continue

            option = self.repository.find_option_by_label(scenario_id, option_label)
            if option is None:
                effect_category = str(
                    row.get("effect_category", "abstract_support")
                ).strip()
                if effect_category not in EFFECT_CATEGORIES:
                    effect_category = "abstract_support"
                option_id = str(uuid4())
                self.repository.insert_abstract_option(
                    option_id=option_id,
                    scenario_id=scenario_id,
                    option_label=option_label,
                    effect_category=effect_category,
                    required_capability_band=str(
                        row.get("capability_band", "medium")
                    ).strip()
                    or "medium",
                    resource_token_type="",
                    estimated_effect_score=clamp_score(
                        self._safe_int(row.get("abstract_effect_score"), 50)
                    ),
                    risk_score=clamp_score(self._safe_int(row.get("risk_score"), 50)),
                    logistics_demand_score=clamp_score(
                        self._safe_int(row.get("logistics_demand_score"), 50)
                    ),
                    source_module="import",
                    review_status=ReviewStatus.REQUIRES_REVIEW,
                )
                option = self.repository.get_abstract_option(option_id)
                assert option is not None

            rationale = str(row.get("rationale", "")).strip()
            if rationale and not self.guardrail_service.validate_training_text(
                text=rationale,
                entity_type="target_weaponeering_assessment",
                entity_id=str(uuid4()),
            ):
                rejected += 1
                rejection_notes.append(f"Row {index}: rationale blocked.")
                continue

            assessment_id = str(uuid4())
            self.repository.insert_assessment(
                assessment_id=assessment_id,
                target_card_id=target_id,
                abstract_weaponeering_option_id=option.id,
                suitability_score=clamp_score(
                    self._safe_int(row.get("option_suitability_score"), 50)
                ),
                feasibility_score=clamp_score(
                    self._safe_int(row.get("option_feasibility_score"), 50)
                ),
                risk_score=clamp_score(self._safe_int(row.get("risk_score"), 50)),
                rationale=rationale,
                generated_by="import",
                review_status=ReviewStatus.REQUIRES_REVIEW,
            )
            imported += 1

        status = "completed" if imported else "rejected"
        summary = (
            f"Imported {imported}, rejected {rejected}. "
            + "; ".join(rejection_notes[:5])
        )
        self.repository.insert_import_batch(
            batch_id=batch_id,
            scenario_id=scenario_id,
            source_reference=file_path.name,
            import_status=status,
            validation_summary=summary[:500],
            imported_count=imported,
            rejected_count=rejected,
            created_by="local_user",
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="import_batch_created",
            entity_type="weaponeering_import_batch",
            entity_id=batch_id,
            details={"imported": imported, "rejected": rejected},
        )
        return ImportResult(
            batch_id=batch_id,
            imported_count=imported,
            rejected_count=rejected,
            validation_summary=summary,
        )

    @staticmethod
    def _parse_json_rows(file_path: Path) -> list[dict]:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict) and "rows" in payload:
            rows = payload["rows"]
            return [row for row in rows if isinstance(row, dict)]
        raise ValueError("JSON import must be a list of row objects.")

    @staticmethod
    def _safe_int(value: object, default: int) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_csv_rows(file_path: Path) -> list[dict]:
        with file_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader]
