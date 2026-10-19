from __future__ import annotations

from typing import Any

from maap_app.modules.detection.corridor_flight_route import (
    attach_route_edit_metadata,
    build_ingress_corridor_flight_route,
)
from maap_app.modules.flight_route.border_corridor_planner import build_waypoint_connector_paths
from maap_app.modules.flight_route.params import (
    AiRoutePlannerParams,
    MAX_FLIGHT_ALTITUDE_FT,
    MIN_FLIGHT_ALTITUDE_FT,
    RouteStyle,
)
from maap_app.modules.flight_route.segment_planner import plan_three_segment_waypoints
from maap_app.modules.weaponeering.flight_path import (
    FlightProfileSettings,
    format_distance_km,
    format_duration_min,
)
from maap_app.modules.weaponeering.mission_defaults import SIM_FLIGHT_DEFAULTS


def _agl_to_ft(agl_m: int) -> int:
    return max(int(round(agl_m * 3.28084)), 200)


def profile_for_ai_params(params: AiRoutePlannerParams) -> FlightProfileSettings:
    defaults = SIM_FLIGHT_DEFAULTS
    cruise_ft = max(
        MIN_FLIGHT_ALTITUDE_FT,
        min(int(params.cruise_altitude_ft), MAX_FLIGHT_ALTITUDE_FT),
    )
    target_low_ft = _agl_to_ft(params.pref_agl_m)
    if params.route_style == RouteStyle.CRUISE:
        return FlightProfileSettings(
            cruise_altitude_ft=cruise_ft,
            ingress_altitude_ft=cruise_ft,
            target_altitude_ft=target_low_ft,
            climb_rate_ft_min=defaults.climb_rate_ft_min,
            descent_rate_ft_min=defaults.descent_rate_ft_min,
            return_enabled=True,
            cruise_speed_kt=float(params.cruise_kts),
            climb_speed_kt=defaults.climb_speed_kt,
            descent_speed_kt=defaults.descent_speed_kt,
            ingress_speed_kt=defaults.ingress_speed_kt,
            bank_angle_deg=defaults.cruise_bank_deg,
            turn_mode=defaults.turn_mode,
            auto_toc_tod=defaults.auto_toc_tod,
        )
    enroute_ft = max(cruise_ft, target_low_ft)
    return FlightProfileSettings(
        cruise_altitude_ft=enroute_ft,
        ingress_altitude_ft=enroute_ft,
        target_altitude_ft=target_low_ft,
        climb_rate_ft_min=defaults.climb_rate_ft_min,
        descent_rate_ft_min=defaults.descent_rate_ft_min,
        return_enabled=True,
        cruise_speed_kt=float(params.cruise_kts),
        climb_speed_kt=defaults.climb_speed_kt,
        descent_speed_kt=defaults.descent_speed_kt,
        ingress_speed_kt=float(params.cruise_kts),
        bank_angle_deg=defaults.ingress_bank_deg,
        turn_mode=defaults.turn_mode,
        auto_toc_tod=False,
    )


def extract_editable_fly_through_waypoints(route: dict[str, Any]) -> list[dict[str, object]]:
    waypoints: list[dict[str, object]] = []
    for marker in route.get("routeMarkers") or []:
        point_type = str(marker.get("pointType") or "")
        if point_type not in {"fly_through", "ingress", "return"}:
            continue
        route_code = str(marker.get("routeCode") or marker.get("label") or "")
        if route_code in {"TOC", "TOD"}:
            continue
        waypoints.append(
            {
                "id": str(marker.get("id") or route_code or "WP"),
                "lat": float(marker["lat"]),
                "lng": float(marker["lng"]),
                "label": str(marker.get("label") or route_code or "WP"),
                "altitudeFt": int(
                    marker.get("altitudeFt") or SIM_FLIGHT_DEFAULTS.fly_through_altitude_ft
                ),
            }
        )
    return waypoints


def split_ai_route_waypoints(
    waypoints: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    outbound: list[dict[str, object]] = []
    return_waypoints: list[dict[str, object]] = []
    for waypoint in waypoints:
        waypoint_id = str(waypoint.get("id") or "")
        label = str(waypoint.get("label") or "")
        if waypoint_id.startswith("AI-RTB") or label.startswith("AI-RTB"):
            return_waypoints.append(waypoint)
        else:
            outbound.append(waypoint)
    return outbound, return_waypoints


def _crossing_coords(crossing: dict[str, object] | None) -> tuple[float, float] | None:
    if not crossing:
        return None
    lat = crossing.get("lat")
    lng = crossing.get("lng")
    if lat is None or lng is None:
        return None
    return float(lat), float(lng)


def plan_ai_flight_route(
    *,
    takeoff_lat: float,
    takeoff_lng: float,
    landing_lat: float,
    landing_lng: float,
    target_lat: float,
    target_lng: float,
    target_label: str,
    target_card_id: str,
    coordinate_id: str | None,
    rank: int,
    border_route: dict[str, object],
    wing_id: str,
    wing_name: str,
    params: AiRoutePlannerParams | None = None,
    ingress_bearing_deg: float | None = None,
    fly_through_waypoints_override: list[dict[str, object]] | None = None,
    return_fly_through_waypoints_override: list[dict[str, object]] | None = None,
    allow_terrain_network: bool = True,
) -> dict[str, Any] | None:
    """Takeoff → (terrain seg.1) → corridor/TGT → (terrain seg.3) → RTB Takeoff."""
    settings = params or AiRoutePlannerParams()
    profile = profile_for_ai_params(settings)

    entry = _crossing_coords(
        border_route.get("entry") if isinstance(border_route.get("entry"), dict) else None
    )
    exit_point = _crossing_coords(
        border_route.get("exit") if isinstance(border_route.get("exit"), dict) else None
    )

    terrain_label = ""
    outbound_override = list(fly_through_waypoints_override or [])
    return_override = list(return_fly_through_waypoints_override or [])

    if not outbound_override and not return_override:
        segment_plan = plan_three_segment_waypoints(
            takeoff=(takeoff_lat, takeoff_lng),
            target=(target_lat, target_lng),
            entry=entry,
            exit_point=exit_point,
            params=settings,
            route_style=settings.route_style,
            allow_network=allow_terrain_network,
        )
        if segment_plan is not None:
            outbound_override = segment_plan.outbound_fly_through
            return_override = segment_plan.return_fly_through
            terrain_label = segment_plan.planner_label

    route = build_ingress_corridor_flight_route(
        wing_lat=takeoff_lat,
        wing_lng=takeoff_lng,
        wing_name=wing_name,
        wing_id=wing_id,
        target_lat=target_lat,
        target_lng=target_lng,
        target_label=target_label,
        target_card_id=target_card_id,
        coordinate_id=coordinate_id,
        rank=rank,
        border_route=border_route,
        flight_profile=profile,
        ingress_bearing_deg=ingress_bearing_deg,
        fly_through_waypoints_override=outbound_override or None,
        return_fly_through_waypoints_override=return_override or None,
        recovery_point=(takeoff_lat, takeoff_lng),
        unified_route=True,
    )
    if route is None:
        return None

    style_labels = {
        RouteStyle.LOW_LEVEL: "Low-Level (AGL)",
        RouteStyle.CRUISE: "Cruise MSL",
        RouteStyle.VALLEY: "Valley",
        RouteStyle.HYBRID: "Hybrid LL",
    }
    editable_waypoints = list(outbound_override) + list(return_override)
    if not editable_waypoints:
        editable_waypoints = extract_editable_fly_through_waypoints(route)

    route["routeSource"] = "ai_planner"
    route["routeColor"] = "#38bdf8"
    route["unifiedRoute"] = True
    route["showReturnRoute"] = False
    style_name = style_labels.get(settings.route_style, "AI")
    if terrain_label:
        style_name = f"{style_name} · {terrain_label}"
    route["routeStyleLabel"] = style_name
    route["useTerrainAgl"] = settings.route_style in {
        RouteStyle.LOW_LEVEL,
        RouteStyle.VALLEY,
        RouteStyle.HYBRID,
    }
    route["prefAglM"] = settings.pref_agl_m
    route["minAglM"] = settings.min_agl_m
    route["maxAglM"] = settings.max_agl_m
    route["cruiseAltitudeFt"] = int(settings.cruise_altitude_ft)
    route["takeoff"] = [takeoff_lat, takeoff_lng]
    route["landing"] = [takeoff_lat, takeoff_lng]
    route["fitToRoute"] = True
    default_alt_m = float(settings.cruise_altitude_ft) * 0.3048
    connector_route, connector_path3d = build_waypoint_connector_paths(
        takeoff=(takeoff_lat, takeoff_lng),
        target=(target_lat, target_lng),
        landing=(takeoff_lat, takeoff_lng),
        editable_waypoints=editable_waypoints,
        entry=entry,
        exit_point=exit_point,
        default_alt_m=default_alt_m,
    )
    route["waypointConnectorRoute"] = connector_route
    route["waypointConnectorPath3d"] = connector_path3d
    route["drawWaypointConnectors"] = True
    if entry is not None:
        route["borderEntry"] = [entry[0], entry[1]]
    if exit_point is not None:
        route["borderExit"] = [exit_point[0], exit_point[1]]
    route["summary"] = (
        f"AI · {style_name} · {wing_name} → เข้า → {target_label} → ออก → RTB {wing_name} · "
        f"{format_distance_km(float(route.get('totalDistanceM') or 0))} · "
        f"~{format_duration_min(float(route.get('totalDurationMin') or 0))}"
    )
    attach_route_edit_metadata(
        route,
        editable_waypoints=editable_waypoints,
        show_waypoints=True,
        route_edit_enabled=True,
    )
    return route


# Re-export for callers that import params from ai_planner.
from maap_app.modules.flight_route.params import AiRoutePlannerParams, RouteStyle
