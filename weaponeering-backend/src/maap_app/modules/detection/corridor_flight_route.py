from __future__ import annotations

from typing import Any

from maap_app.modules.weaponeering.flight_path import (
    FlightPathResult,
    FlightProfileSettings,
    FlightWaypointSpec,
    compute_flight_profile,
    distance_m,
    format_distance_km,
    format_duration_min,
)
from maap_app.modules.weaponeering.mission_defaults import SIM_FLIGHT_DEFAULTS
from maap_app.modules.weaponeering.models import TargetDeploymentPlan


def _crossing_coords(crossing: dict[str, object] | None) -> tuple[float, float] | None:
    if not crossing:
        return None
    lat = crossing.get("lat")
    lng = crossing.get("lng")
    if lat is None or lng is None:
        return None
    return float(lat), float(lng)


def _default_flight_profile() -> FlightProfileSettings:
    defaults = SIM_FLIGHT_DEFAULTS
    return FlightProfileSettings(
        cruise_altitude_ft=defaults.cruise_altitude_ft,
        ingress_altitude_ft=defaults.ingress_altitude_ft,
        target_altitude_ft=defaults.fly_through_altitude_ft,
        climb_rate_ft_min=defaults.climb_rate_ft_min,
        descent_rate_ft_min=defaults.descent_rate_ft_min,
        return_enabled=defaults.rtb_enabled,
        cruise_speed_kt=defaults.cruise_speed_kt,
        climb_speed_kt=defaults.climb_speed_kt,
        descent_speed_kt=defaults.descent_speed_kt,
        ingress_speed_kt=defaults.ingress_speed_kt,
        bank_angle_deg=defaults.ingress_bank_deg,
        turn_mode=defaults.turn_mode,
        auto_toc_tod=defaults.auto_toc_tod,
    )


def _flight_profile_from_plan(plan: TargetDeploymentPlan) -> FlightProfileSettings:
    return FlightProfileSettings(
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
    )


def _resolve_ingress_bearing(
    border_route: dict[str, object],
    *,
    override: float | None = None,
) -> float | None:
    if override is not None:
        return float(override)
    ingress = border_route.get("ingressBearingDeg")
    if ingress is not None:
        return float(ingress)
    approach = border_route.get("approachBearingDeg")
    if approach is not None:
        return float(approach)
    return None


def _near_point(
    point: tuple[float, float],
    candidates: list[FlightWaypointSpec],
    *,
    threshold_m: float = 2_000.0,
) -> bool:
    lat, lng = point
    return any(
        distance_m(lat, lng, waypoint.lat, waypoint.lng) <= threshold_m
        for waypoint in candidates
    )


def _append_border_waypoints(
    *,
    approach_waypoints: list[FlightWaypointSpec],
    return_waypoints: list[FlightWaypointSpec],
    entry_coords: tuple[float, float] | None,
    exit_coords: tuple[float, float] | None,
    rank: int,
    outbound_waypoints: list[FlightWaypointSpec],
) -> None:
    if entry_coords is not None and not _near_point(
        entry_coords,
        outbound_waypoints + approach_waypoints,
    ):
        approach_waypoints.append(
            FlightWaypointSpec(
                lat=entry_coords[0],
                lng=entry_coords[1],
                label=f"เข้า #{rank}",
                waypoint_type="fly_through",
            )
        )
    if exit_coords is not None and not _near_point(exit_coords, return_waypoints):
        return_waypoints.append(
            FlightWaypointSpec(
                lat=exit_coords[0],
                lng=exit_coords[1],
                label=f"ออก #{rank}",
                waypoint_type="return",
            )
        )


def _merge_outbound_waypoints(
    outbound_waypoints: list[FlightWaypointSpec],
    approach_waypoints: list[FlightWaypointSpec],
) -> list[FlightWaypointSpec]:
    return list(outbound_waypoints) + list(approach_waypoints)


def _build_unified_path3d(
    flight_path: FlightPathResult,
    *,
    recovery_lat: float,
    recovery_lng: float,
) -> list[list[float]]:
    unified: list[tuple[float, float, float]] = list(flight_path.path3d)
    if flight_path.return_path3d:
        unified.extend(flight_path.return_path3d[1:])
    if unified:
        last_alt = unified[-1][2] if len(unified[-1]) > 2 else 0.0
        unified[-1] = (recovery_lat, recovery_lng, last_alt)
    return [[lat, lng, alt_m] for lat, lng, alt_m in unified]


def _route_payload(
    *,
    flight_path: FlightPathResult,
    link_id: str,
    target_card_id: str,
    coordinate_id: str | None,
    rank: int,
    wing_id: str,
    wing_name: str,
    wing_lat: float,
    wing_lng: float,
    target_lat: float,
    target_lng: float,
    target_label: str,
    summary_parts: list[str],
    route_source: str,
    route_color: str,
    ingress_bearing_deg: float | None,
    ingress_offset_m: int,
    profile: FlightProfileSettings,
    entry_coords: tuple[float, float] | None,
    exit_coords: tuple[float, float] | None,
    unified_route: bool = False,
) -> dict[str, Any]:
    outbound_route = [[lat, lng] for lat, lng in flight_path.outbound_route]
    return_route = [[lat, lng] for lat, lng in flight_path.return_route]
    route_markers = [
        marker
        for marker in flight_path.route_markers
        if str(marker.get("routeCode") or "") not in {"TOC", "TOD"}
    ]

    outbound_distance_m = (
        flight_path.trajectory_samples[-1]["distanceM"]
        if flight_path.trajectory_samples
        else flight_path.total_distance_m
    )
    return_distance_m = max(flight_path.total_distance_m - outbound_distance_m, 0.0)

    recovery_lat, recovery_lng = wing_lat, wing_lng
    if flight_path.return_route:
        recovery_lat, recovery_lng = flight_path.return_route[-1]

    if return_route:
        return_route = list(return_route[:-1]) + [[recovery_lat, recovery_lng]]

    payload: dict[str, Any] = {
        "linkId": link_id,
        "targetCardId": target_card_id,
        "coordinateId": coordinate_id,
        "rank": rank,
        "wingId": wing_id,
        "label": f"{wing_name} → {target_label} (#{rank})",
        "origin": [wing_lat, wing_lng],
        "destination": [target_lat, target_lng],
        "outboundRoute": outbound_route,
        "returnRoute": return_route,
        "showReturnRoute": len(return_route) >= 2 and not unified_route,
        "routeMarkers": route_markers,
        "path3d": [[lat, lng, alt_m] for lat, lng, alt_m in flight_path.path3d],
        "returnPath3d": [
            [lat, lng, alt_m] for lat, lng, alt_m in flight_path.return_path3d
        ],
        "trajectoryRoute": list(flight_path.trajectory_samples),
        "ingressBearingDeg": ingress_bearing_deg,
        "ingressOffsetM": ingress_offset_m,
        "bankAngleDeg": profile.bank_angle_deg,
        "turnMode": profile.turn_mode,
        "totalDistanceM": round(flight_path.total_distance_m, 1),
        "totalDurationMin": round(flight_path.total_duration_min, 1),
        "finalApproachBearingDeg": flight_path.final_approach_bearing_deg,
        "summary": " · ".join(summary_parts),
        "outboundDistanceKm": round(outbound_distance_m / 1000.0, 1),
        "returnDistanceKm": round(return_distance_m / 1000.0, 1),
        "routeStyle": "curved_fly_by",
        "routeSource": route_source,
        "routeColor": route_color,
        "hasBorderEntry": entry_coords is not None,
        "hasBorderExit": exit_coords is not None,
    }
    if unified_route:
        payload["unifiedRoute"] = True
        payload["unifiedPath3d"] = _build_unified_path3d(
            flight_path,
            recovery_lat=recovery_lat,
            recovery_lng=recovery_lng,
        )
    return payload


def _fly_through_specs_from_edit(
    waypoints: list[dict[str, object]] | None,
) -> list[FlightWaypointSpec]:
    if not waypoints:
        return []
    specs: list[FlightWaypointSpec] = []
    for waypoint in waypoints:
        specs.append(
            FlightWaypointSpec(
                lat=float(waypoint["lat"]),
                lng=float(waypoint["lng"]),
                label=str(waypoint.get("label") or ""),
                waypoint_type="fly_through",
                altitude_ft=(
                    int(waypoint["altitudeFt"])
                    if waypoint.get("altitudeFt") is not None
                    else None
                ),
            )
        )
    return specs


def attach_route_edit_metadata(
    payload: dict[str, Any],
    *,
    editable_waypoints: list[dict[str, object]],
    selected_waypoint_id: str | None = None,
    route_edit_enabled: bool = True,
    show_waypoints: bool = True,
    show_waypoint_labels: bool = False,
) -> dict[str, Any]:
    payload["editableWaypoints"] = list(editable_waypoints)
    payload["routeEditEnabled"] = route_edit_enabled
    payload["showWaypoints"] = show_waypoints
    payload["showWaypointLabels"] = show_waypoint_labels
    if selected_waypoint_id:
        payload["selectedWaypointId"] = selected_waypoint_id
    return payload


def build_waypoint_sketch_route(
    *,
    wing_lat: float,
    wing_lng: float,
    wing_name: str,
    wing_id: str,
    target_lat: float,
    target_lng: float,
    target_label: str,
    target_card_id: str,
    coordinate_id: str | None,
    rank: int,
    fly_through_waypoints: list[dict[str, object]] | None = None,
) -> dict[str, Any]:
    """Straight geodesic segments through user waypoints — no fly-by curves or ingress IP."""
    waypoints = list(fly_through_waypoints or [])
    route_points: list[tuple[float, float]] = [(wing_lat, wing_lng)]
    for waypoint in waypoints:
        route_points.append((float(waypoint["lat"]), float(waypoint["lng"])))

    outbound_route = [[lat, lng] for lat, lng in route_points]
    outbound_distance_m = sum(
        distance_m(
            route_points[index][0],
            route_points[index][1],
            route_points[index + 1][0],
            route_points[index + 1][1],
        )
        for index in range(len(route_points) - 1)
    )

    route_markers: list[dict[str, object]] = [
        {
            "lat": wing_lat,
            "lng": wing_lng,
            "label": wing_name,
            "pointType": "takeoff",
            "routeCode": "TO",
            "altitudeFt": 0,
        },
        {
            "lat": target_lat,
            "lng": target_lng,
            "label": target_label,
            "pointType": "target",
            "routeCode": "TGT",
            "altitudeFt": 0,
        },
    ]

    summary_parts = [
        f"ร่างเส้นทาง · {len(waypoints)} จุด",
        f"ระยะ {format_distance_km(outbound_distance_m)}",
        "เส้นตรงตาม Waypoint",
        "เป้าหมายแยก — จัดทางเข้าทีหลัง",
    ]

    return {
        "linkId": f"sketch-{target_card_id}-{coordinate_id or 'primary'}-{rank}",
        "targetCardId": target_card_id,
        "coordinateId": coordinate_id,
        "rank": rank,
        "wingId": wing_id,
        "label": f"{wing_name} → {target_label} (ร่าง)",
        "origin": [wing_lat, wing_lng],
        "destination": [target_lat, target_lng],
        "outboundRoute": outbound_route,
        "returnRoute": [],
        "showReturnRoute": False,
        "routeMarkers": route_markers,
        "summary": " · ".join(summary_parts),
        "outboundDistanceKm": round(outbound_distance_m / 1000.0, 1),
        "returnDistanceKm": 0.0,
        "routeStyle": "waypoint_polyline",
        "routeSource": "waypoint_sketch",
        "routeColor": "#38bdf8",
        "totalDistanceM": round(outbound_distance_m, 1),
        "fitToRoute": False,
        "showWaypoints": True,
    }


def build_deployment_plan_corridor_route(
    *,
    plan: TargetDeploymentPlan,
    wing_lat: float,
    wing_lng: float,
    wing_name: str,
    wing_id: str,
    target_lat: float,
    target_lng: float,
    target_label: str,
    target_card_id: str,
    coordinate_id: str | None,
    rank: int,
    border_route: dict[str, object],
    fly_through_waypoints_override: list[dict[str, object]] | None = None,
) -> dict[str, Any] | None:
    if not border_route.get("available"):
        return None

    takeoff_lat = float(plan.takeoff_lat if plan.takeoff_lat is not None else wing_lat)
    takeoff_lng = float(plan.takeoff_lng if plan.takeoff_lng is not None else wing_lng)
    entry_coords = _crossing_coords(
        border_route.get("entry") if isinstance(border_route.get("entry"), dict) else None
    )
    exit_coords = _crossing_coords(
        border_route.get("exit") if isinstance(border_route.get("exit"), dict) else None
    )

    outbound_waypoints = (
        _fly_through_specs_from_edit(fly_through_waypoints_override)
        if fly_through_waypoints_override is not None
        else [
            FlightWaypointSpec(
                lat=waypoint.lat,
                lng=waypoint.lng,
                label=waypoint.label or "",
                waypoint_type=waypoint.waypoint_type,
                altitude_ft=waypoint.altitude_ft,
            )
            for waypoint in plan.waypoints
            if waypoint.waypoint_type == "fly_through"
        ]
    )
    return_waypoints = [
        FlightWaypointSpec(
            lat=waypoint.lat,
            lng=waypoint.lng,
            label=waypoint.label or "",
            waypoint_type="return",
            altitude_ft=waypoint.altitude_ft,
        )
        for waypoint in plan.waypoints
        if waypoint.waypoint_type == "return"
    ]
    approach_waypoints: list[FlightWaypointSpec] = []
    _append_border_waypoints(
        approach_waypoints=approach_waypoints,
        return_waypoints=return_waypoints,
        entry_coords=entry_coords,
        exit_coords=exit_coords,
        rank=rank,
        outbound_waypoints=outbound_waypoints,
    )

    profile = _flight_profile_from_plan(plan)
    flight_path = compute_flight_profile(
        takeoff=(takeoff_lat, takeoff_lng),
        destination=(target_lat, target_lng),
        outbound_waypoints=_merge_outbound_waypoints(
            outbound_waypoints,
            approach_waypoints,
        ),
        return_waypoints=return_waypoints,
        ingress_bearing_deg=plan.ingress_bearing_deg,
        ingress_offset_m=plan.ingress_offset_m,
        profile=profile,
        recovery=(takeoff_lat, takeoff_lng),
    )

    waypoint_count = len(outbound_waypoints) + len(return_waypoints)
    summary_parts = [
        f"{wing_name} → {target_label}",
        f"แผน Weaponeering ({waypoint_count} จุด)",
        f"ไป {format_distance_km(flight_path.trajectory_samples[-1]['distanceM'] if flight_path.trajectory_samples else flight_path.total_distance_m)}",
        f"~{format_duration_min(flight_path.total_duration_min)}",
        "เส้นทางโค้ง fly-by",
        "แสดงขาเข้า",
    ]
    if entry_coords is not None:
        summary_parts.insert(1, "ผ่านทางเข้าชายแดน")

    return _route_payload(
        flight_path=flight_path,
        link_id=f"corridor-plan-{target_card_id}-{coordinate_id or 'primary'}-{rank}",
        target_card_id=target_card_id,
        coordinate_id=coordinate_id,
        rank=rank,
        wing_id=wing_id,
        wing_name=wing_name,
        wing_lat=takeoff_lat,
        wing_lng=takeoff_lng,
        target_lat=target_lat,
        target_lng=target_lng,
        target_label=target_label,
        summary_parts=summary_parts,
        route_source="weaponeering_plan",
        route_color="#38bdf8",
        ingress_bearing_deg=plan.ingress_bearing_deg,
        ingress_offset_m=plan.ingress_offset_m,
        profile=profile,
        entry_coords=entry_coords,
        exit_coords=exit_coords,
    )


def build_ingress_corridor_flight_route(
    *,
    wing_lat: float,
    wing_lng: float,
    wing_name: str,
    wing_id: str,
    target_lat: float,
    target_lng: float,
    target_label: str,
    target_card_id: str,
    coordinate_id: str | None,
    rank: int,
    border_route: dict[str, object],
    flight_profile: FlightProfileSettings | None = None,
    ingress_bearing_deg: float | None = None,
    ingress_offset_m: int = 15_000,
    fly_through_waypoints_override: list[dict[str, object]] | None = None,
    return_fly_through_waypoints_override: list[dict[str, object]] | None = None,
    recovery_point: tuple[float, float] | None = None,
    unified_route: bool = False,
) -> dict[str, Any] | None:
    if not border_route.get("available"):
        return None

    entry_coords = _crossing_coords(
        border_route.get("entry") if isinstance(border_route.get("entry"), dict) else None
    )
    exit_coords = _crossing_coords(
        border_route.get("exit") if isinstance(border_route.get("exit"), dict) else None
    )
    resolved_ingress = _resolve_ingress_bearing(
        border_route,
        override=ingress_bearing_deg,
    )

    approach_waypoints: list[FlightWaypointSpec] = []
    return_waypoints: list[FlightWaypointSpec] = []
    outbound_waypoints = _fly_through_specs_from_edit(
        fly_through_waypoints_override
    )
    terrain_return_specs = [
        FlightWaypointSpec(
            lat=spec.lat,
            lng=spec.lng,
            label=spec.label or "",
            waypoint_type="return",
            altitude_ft=spec.altitude_ft,
        )
        for spec in _fly_through_specs_from_edit(return_fly_through_waypoints_override)
    ]
    _append_border_waypoints(
        approach_waypoints=approach_waypoints,
        return_waypoints=return_waypoints,
        entry_coords=entry_coords,
        exit_coords=exit_coords,
        rank=rank,
        outbound_waypoints=outbound_waypoints,
    )
    if terrain_return_specs:
        return_waypoints = return_waypoints + terrain_return_specs

    profile = flight_profile or _default_flight_profile()
    resolved_recovery = recovery_point or (wing_lat, wing_lng)
    flight_path = compute_flight_profile(
        takeoff=(wing_lat, wing_lng),
        destination=(target_lat, target_lng),
        outbound_waypoints=_merge_outbound_waypoints(
            outbound_waypoints,
            approach_waypoints,
        ),
        return_waypoints=return_waypoints,
        ingress_bearing_deg=None,
        ingress_offset_m=0,
        profile=profile,
        recovery=resolved_recovery,
    )

    leg_parts = [f"{wing_name} →"]
    if entry_coords is not None:
        leg_parts.append("เข้าประเทศ →")
    leg_parts.append(f"{target_label}")
    summary_parts = [
        " ".join(leg_parts),
        "เส้นทางอัตโนมัติ (บันทึกแผน Weaponeering เพื่อความละเอียด)",
        f"ไป {format_distance_km(flight_path.trajectory_samples[-1]['distanceM'] if flight_path.trajectory_samples else flight_path.total_distance_m)}",
        f"~{format_duration_min(flight_path.total_duration_min)}",
        "เส้นทางโค้ง fly-by",
        "แสดงขาเข้า",
    ]
    if resolved_ingress is not None:
        summary_parts.append(f"เข้า {resolved_ingress:.0f}°")

    return _route_payload(
        flight_path=flight_path,
        link_id=f"corridor-{target_card_id}-{coordinate_id or 'primary'}-{rank}",
        target_card_id=target_card_id,
        coordinate_id=coordinate_id,
        rank=rank,
        wing_id=wing_id,
        wing_name=wing_name,
        wing_lat=wing_lat,
        wing_lng=wing_lng,
        target_lat=target_lat,
        target_lng=target_lng,
        target_label=target_label,
        summary_parts=summary_parts,
        route_source="corridor_auto",
        route_color="#f59e0b",
        ingress_bearing_deg=resolved_ingress,
        ingress_offset_m=ingress_offset_m,
        profile=profile,
        entry_coords=entry_coords,
        exit_coords=exit_coords,
        unified_route=unified_route,
    )
