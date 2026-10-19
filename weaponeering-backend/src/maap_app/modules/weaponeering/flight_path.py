from __future__ import annotations

import math
from dataclasses import dataclass


EARTH_RADIUS_M = 6_371_000.0
FT_TO_M = 0.3048
CRUISE_SPEED_MPS = 231.5  # ~450 kt
PROFILE_SAMPLES_PER_LEG = 20


@dataclass(frozen=True)
class FlightProfileSettings:
    cruise_altitude_ft: int = 25000
    ingress_altitude_ft: int = 2000
    target_altitude_ft: int = 2000
    climb_rate_ft_min: int = 3000
    descent_rate_ft_min: int = 2000
    return_enabled: bool = True
    cruise_speed_kt: float = 420.0
    climb_speed_kt: float = 250.0
    descent_speed_kt: float = 300.0
    ingress_speed_kt: float = 250.0
    bank_angle_deg: float = 20.0
    turn_mode: str = "fly_by"
    auto_toc_tod: bool = True


@dataclass(frozen=True)
class FlightWaypointSpec:
    lat: float
    lng: float
    label: str = ""
    waypoint_type: str = "fly_through"
    altitude_ft: int | None = None


@dataclass(frozen=True)
class FlightPathPoint:
    lat: float
    lng: float
    label: str = ""
    point_type: str = "waypoint"
    altitude_ft: float = 0.0
    phase: str = "cruise"


@dataclass(frozen=True)
class FlightPathLeg:
    from_index: int
    to_index: int
    distance_m: float
    bearing_deg: float
    start_altitude_ft: float = 0.0
    end_altitude_ft: float = 0.0
    phase: str = "cruise"
    duration_min: float = 0.0


@dataclass(frozen=True)
class FlightPathResult:
    points: tuple[FlightPathPoint, ...]
    legs: tuple[FlightPathLeg, ...]
    total_distance_m: float
    total_duration_min: float
    outbound_route: tuple[tuple[float, float], ...] = ()
    return_route: tuple[tuple[float, float], ...] = ()
    route_markers: tuple[dict[str, object], ...] = ()
    final_approach_bearing_deg: float | None = None
    path3d: tuple[tuple[float, float, float], ...] = ()
    return_path3d: tuple[tuple[float, float, float], ...] = ()
    profile_segments: tuple[dict[str, object], ...] = ()
    trajectory_samples: tuple[dict[str, object], ...] = ()


def normalize_bearing_deg(value: float) -> float:
    normalized = value % 360.0
    if normalized < 0:
        normalized += 360.0
    return normalized


def bearing_deg(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    delta_lng = math.radians(lng2 - lng1)
    y = math.sin(delta_lng) * math.cos(lat2_r)
    x = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(
        lat2_r
    ) * math.cos(delta_lng)
    return normalize_bearing_deg(math.degrees(math.atan2(y, x)))


def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(delta_lng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def destination_point(
    lat: float,
    lng: float,
    bearing: float,
    offset_m: float,
) -> tuple[float, float]:
    if offset_m <= 0:
        return lat, lng
    bearing_r = math.radians(normalize_bearing_deg(bearing))
    lat_r = math.radians(lat)
    lng_r = math.radians(lng)
    angular = offset_m / EARTH_RADIUS_M
    dest_lat = math.asin(
        math.sin(lat_r) * math.cos(angular)
        + math.cos(lat_r) * math.sin(angular) * math.cos(bearing_r)
    )
    dest_lng = lng_r + math.atan2(
        math.sin(bearing_r) * math.sin(angular) * math.cos(lat_r),
        math.cos(angular) - math.sin(lat_r) * math.sin(dest_lat),
    )
    return math.degrees(dest_lat), math.degrees(dest_lng)


def format_distance_km(distance_m: float) -> str:
    if distance_m >= 1000:
        return f"{distance_m / 1000:.1f} km"
    return f"{distance_m:.0f} m"


def format_duration_min(duration_min: float) -> str:
    if duration_min >= 60:
        hours = int(duration_min // 60)
        minutes = int(round(duration_min % 60))
        return f"{hours}h {minutes}m"
    return f"{duration_min:.0f} min"


def _leg_duration_minutes(
    distance_m: float,
    alt_change_ft: float,
    *,
    climb_rate_ft_min: int,
    descent_rate_ft_min: int,
) -> float:
    horizontal_min = (distance_m / CRUISE_SPEED_MPS) / 60.0
    if alt_change_ft > 0:
        vertical_min = alt_change_ft / max(climb_rate_ft_min, 1)
    elif alt_change_ft < 0:
        vertical_min = abs(alt_change_ft) / max(descent_rate_ft_min, 1)
    else:
        vertical_min = 0.0
    return horizontal_min + vertical_min


def _interpolate_geodesic(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
    fraction: float,
) -> tuple[float, float]:
    if fraction <= 0:
        return lat1, lng1
    if fraction >= 1:
        return lat2, lng2
    lat1_r = math.radians(lat1)
    lng1_r = math.radians(lng1)
    lat2_r = math.radians(lat2)
    lng2_r = math.radians(lng2)
    delta_lat = lat2_r - lat1_r
    delta_lng = lng2_r - lng1_r
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(delta_lng / 2) ** 2
    )
    angular = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))
    if angular == 0:
        return lat1, lng1
    a_factor = math.sin((1 - fraction) * angular) / math.sin(angular)
    b_factor = math.sin(fraction * angular) / math.sin(angular)
    x = a_factor * math.cos(lat1_r) * math.cos(lng1_r) + b_factor * math.cos(
        lat2_r
    ) * math.cos(lng2_r)
    y = a_factor * math.cos(lat1_r) * math.sin(lng1_r) + b_factor * math.cos(
        lat2_r
    ) * math.sin(lng2_r)
    z = a_factor * math.sin(lat1_r) + b_factor * math.sin(lat2_r)
    lat = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
    lng = math.degrees(math.atan2(y, x))
    return lat, lng


def _build_leg_path3d(
    start: FlightPathPoint,
    end: FlightPathPoint,
    *,
    samples: int = PROFILE_SAMPLES_PER_LEG,
) -> list[tuple[float, float, float]]:
    positions: list[tuple[float, float, float]] = []
    for index in range(samples + 1):
        fraction = index / samples
        lat, lng = _interpolate_geodesic(
            start.lat,
            start.lng,
            end.lat,
            end.lng,
            fraction,
        )
        alt_ft = start.altitude_ft + (end.altitude_ft - start.altitude_ft) * fraction
        positions.append((lat, lng, alt_ft * FT_TO_M))
    return positions


def _assign_altitudes(
    points: list[FlightPathPoint],
    *,
    profile: FlightProfileSettings,
    outbound: bool,
) -> list[FlightPathPoint]:
    if not points:
        return points

    updated: list[FlightPathPoint] = list(points)
    if outbound:
        updated[0] = FlightPathPoint(
            updated[0].lat,
            updated[0].lng,
            updated[0].label,
            updated[0].point_type,
            0.0,
            "takeoff",
        )
        for index in range(1, len(updated)):
            point = updated[index]
            if point.point_type == "fly_through":
                alt = (
                    float(point.altitude_ft)
                    if point.altitude_ft
                    else float(profile.cruise_altitude_ft)
                )
                updated[index] = FlightPathPoint(
                    point.lat,
                    point.lng,
                    point.label,
                    point.point_type,
                    alt,
                    "cruise",
                )
            elif point.point_type == "ingress":
                updated[index] = FlightPathPoint(
                    point.lat,
                    point.lng,
                    point.label,
                    point.point_type,
                    float(profile.ingress_altitude_ft),
                    "ingress",
                )
            elif point.point_type == "target":
                updated[index] = FlightPathPoint(
                    point.lat,
                    point.lng,
                    point.label,
                    point.point_type,
                    float(profile.target_altitude_ft),
                    "attack",
                )
        if len(updated) >= 2 and updated[1].point_type == "fly_through":
            updated[1] = FlightPathPoint(
                updated[1].lat,
                updated[1].lng,
                updated[1].label,
                updated[1].point_type,
                float(profile.cruise_altitude_ft),
                "climb",
            )
        return updated

    updated[0] = FlightPathPoint(
        updated[0].lat,
        updated[0].lng,
        updated[0].label,
        updated[0].point_type,
        float(profile.target_altitude_ft),
        "rtb_climb",
    )
    for index in range(1, len(updated)):
        point = updated[index]
        if point.point_type in {"fly_through", "return"}:
            alt = (
                float(point.altitude_ft)
                if point.altitude_ft
                else float(profile.cruise_altitude_ft)
            )
            phase = "rtb_cruise" if index < len(updated) - 1 else "rtb_descent"
            updated[index] = FlightPathPoint(
                point.lat,
                point.lng,
                point.label,
                point.point_type,
                alt,
                phase,
            )
        elif point.point_type == "takeoff":
            updated[index] = FlightPathPoint(
                point.lat,
                point.lng,
                point.label,
                point.point_type,
                0.0,
                "landing",
            )
    if len(updated) >= 2:
        updated[1] = FlightPathPoint(
            updated[1].lat,
            updated[1].lng,
            updated[1].label,
            updated[1].point_type,
            float(profile.cruise_altitude_ft),
            "rtb_climb",
        )
        updated[-1] = FlightPathPoint(
            updated[-1].lat,
            updated[-1].lng,
            updated[-1].label,
            updated[-1].point_type,
            0.0,
            "landing",
        )
    return updated


def _leg_phase(start: FlightPathPoint, end: FlightPathPoint) -> str:
    if end.phase in {"climb", "rtb_climb"}:
        return "climb"
    if end.phase in {"ingress", "attack", "landing", "rtb_descent"}:
        return "descent"
    if start.phase == "attack" and end.phase == "rtb_cruise":
        return "climb"
    return "cruise"


def _build_legs(
    points: list[FlightPathPoint],
    *,
    profile: FlightProfileSettings,
) -> list[FlightPathLeg]:
    legs: list[FlightPathLeg] = []
    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]
        leg_distance = distance_m(start.lat, start.lng, end.lat, end.lng)
        leg_bearing = bearing_deg(start.lat, start.lng, end.lat, end.lng)
        alt_change = end.altitude_ft - start.altitude_ft
        phase = _leg_phase(start, end)
        legs.append(
            FlightPathLeg(
                from_index=index,
                to_index=index + 1,
                distance_m=leg_distance,
                bearing_deg=leg_bearing,
                start_altitude_ft=start.altitude_ft,
                end_altitude_ft=end.altitude_ft,
                phase=phase,
                duration_min=_leg_duration_minutes(
                    leg_distance,
                    alt_change,
                    climb_rate_ft_min=profile.climb_rate_ft_min,
                    descent_rate_ft_min=profile.descent_rate_ft_min,
                ),
            )
        )
    return legs


def _build_path3d(
    points: list[FlightPathPoint],
    legs: list[FlightPathLeg],
) -> list[tuple[float, float, float]]:
    if len(points) < 2:
        return []
    positions: list[tuple[float, float, float]] = []
    for leg in legs:
        leg_positions = _build_leg_path3d(points[leg.from_index], points[leg.to_index])
        start_index = 0 if not positions else 1
        positions.extend(leg_positions[start_index:])
    return positions


def _profile_segment_label(leg: FlightPathLeg, end: FlightPathPoint) -> str:
    if leg.phase == "climb":
        return f"ขึ้นสู่ FL{int(round(leg.end_altitude_ft / 100))}"
    if leg.phase == "descent":
        return f"ลดความสูง → {int(round(leg.end_altitude_ft))} ft ({end.label})"
    return f"บินรอบ → {end.label} @ {int(round(leg.end_altitude_ft))} ft"


def _route_marker_code(point: FlightPathPoint, index: int, *, leg: str) -> str:
    if point.point_type == "takeoff":
        return "DEP" if leg == "outbound" else "REC"
    if point.point_type == "target":
        return "TGT"
    if point.point_type == "ingress":
        return "IP"
    if point.point_type == "return":
        return f"R{index}"
    return f"WP{index}"


def _route_markers_for_points(
    points: list[FlightPathPoint],
    *,
    leg: str,
) -> list[dict[str, object]]:
    markers: list[dict[str, object]] = []
    waypoint_index = 0
    for sequence, point in enumerate(points, start=1):
        if point.point_type == "fly_through":
            waypoint_index += 1
        markers.append(
            {
                "lat": point.lat,
                "lng": point.lng,
                "label": point.label,
                "pointType": point.point_type,
                "routeCode": _route_marker_code(
                    point,
                    waypoint_index,
                    leg=leg,
                ),
                "sequence": sequence,
                "altitudeFt": round(point.altitude_ft),
                "phase": point.phase,
                "leg": leg,
            }
        )
    return markers


def compute_flight_path(
    *,
    takeoff: tuple[float, float],
    destination: tuple[float, float],
    waypoints: list[tuple[float, float, str]] | None = None,
    ingress_bearing_deg: float | None = None,
    ingress_offset_m: int = 5000,
) -> FlightPathResult:
    profile = compute_flight_profile(
        takeoff=takeoff,
        destination=destination,
        outbound_waypoints=[
            FlightWaypointSpec(lat=lat, lng=lng, label=label)
            for lat, lng, label in (waypoints or [])
        ],
        ingress_bearing_deg=ingress_bearing_deg,
        ingress_offset_m=ingress_offset_m,
    )
    return profile


def compute_flight_profile(
    *,
    takeoff: tuple[float, float],
    destination: tuple[float, float],
    outbound_waypoints: list[FlightWaypointSpec] | None = None,
    return_waypoints: list[FlightWaypointSpec] | None = None,
    ingress_bearing_deg: float | None = None,
    ingress_offset_m: int = 5000,
    profile: FlightProfileSettings | None = None,
    recovery: tuple[float, float] | None = None,
) -> FlightPathResult:
    settings = profile or FlightProfileSettings()
    recovery_point = recovery or takeoff

    outbound_points: list[FlightPathPoint] = [
        FlightPathPoint(takeoff[0], takeoff[1], "Takeoff", "takeoff"),
    ]
    for index, waypoint in enumerate(outbound_waypoints or []):
        label = waypoint.label or f"WP{index + 1}"
        outbound_points.append(
            FlightPathPoint(
                waypoint.lat,
                waypoint.lng,
                label,
                waypoint.waypoint_type,
                float(waypoint.altitude_ft or 0),
            )
        )

    if ingress_bearing_deg is not None and ingress_offset_m > 0:
        ingress_lat, ingress_lng = destination_point(
            destination[0],
            destination[1],
            ingress_bearing_deg + 180.0,
            float(ingress_offset_m),
        )
        outbound_points.append(
            FlightPathPoint(ingress_lat, ingress_lng, "Ingress", "ingress")
        )

    outbound_points.append(
        FlightPathPoint(destination[0], destination[1], "Target", "target")
    )
    outbound_points = _assign_altitudes(outbound_points, profile=settings, outbound=True)
    outbound_legs = _build_legs(outbound_points, profile=settings)

    from maap_app.modules.weaponeering.trajectory import (
        build_realistic_trajectory,
        build_return_trajectory,
        trajectory_phase_markers,
        trajectory_to_path3d,
    )

    outbound_coords = [(point.lat, point.lng) for point in outbound_points]
    outbound_trajectory = build_realistic_trajectory(
        outbound_coords,
        profile=settings,
    )
    outbound_path3d = trajectory_to_path3d(outbound_trajectory)

    return_points: list[FlightPathPoint] = []
    return_legs: list[FlightPathLeg] = []
    return_path3d: list[tuple[float, float, float]] = []
    return_trajectory = ()

    if settings.return_enabled:
        return_specs = list(return_waypoints or [])
        if not return_specs:
            for waypoint in reversed(outbound_waypoints or []):
                return_specs.append(
                    FlightWaypointSpec(
                        lat=waypoint.lat,
                        lng=waypoint.lng,
                        label=f"RTB {waypoint.label or 'WP'}",
                        waypoint_type="return",
                        altitude_ft=waypoint.altitude_ft,
                    )
                )
        return_points = [
            FlightPathPoint(
                destination[0],
                destination[1],
                "Target",
                "target",
            )
        ]
        for index, waypoint in enumerate(return_specs):
            label = waypoint.label or f"RTB{index + 1}"
            return_points.append(
                FlightPathPoint(
                    waypoint.lat,
                    waypoint.lng,
                    label,
                    "return",
                    float(waypoint.altitude_ft or 0),
                )
            )
        recovery_label = (
            "Landing"
            if distance_m(takeoff[0], takeoff[1], recovery_point[0], recovery_point[1]) > 500.0
            else "Recovery"
        )
        return_points.append(
            FlightPathPoint(
                recovery_point[0],
                recovery_point[1],
                recovery_label,
                "takeoff",
            )
        )
        return_points = _assign_altitudes(return_points, profile=settings, outbound=False)
        return_legs = _build_legs(return_points, profile=settings)
        return_coords = [(point.lat, point.lng) for point in return_points]
        return_trajectory = build_return_trajectory(return_coords, profile=settings)
        if return_trajectory:
            last_distance = return_trajectory[-1].distance_m
            from maap_app.modules.weaponeering.trajectory import TrajectorySample

            return_trajectory[-1] = TrajectorySample(
                recovery_point[0],
                recovery_point[1],
                0.0,
                "landing",
                last_distance,
            )
        return_path3d = trajectory_to_path3d(return_trajectory)
        if return_path3d:
            return_path3d[-1] = (
                recovery_point[0],
                recovery_point[1],
                return_path3d[-1][2],
            )

    all_points = outbound_points + (
        return_points[1:] if return_points else []
    )
    all_legs = outbound_legs + return_legs
    total_distance_m = sum(leg.distance_m for leg in all_legs)
    total_duration_min = sum(leg.duration_min for leg in all_legs)
    final_bearing = (
        normalize_bearing_deg(ingress_bearing_deg)
        if ingress_bearing_deg is not None
        else (outbound_legs[-1].bearing_deg if outbound_legs else None)
    )
    profile_segments = tuple(
        {
            "phase": leg.phase,
            "label": _profile_segment_label(leg, all_points[leg.to_index]),
            "distanceM": round(leg.distance_m, 1),
            "distanceLabel": format_distance_km(leg.distance_m),
            "durationMin": round(leg.duration_min, 1),
            "durationLabel": format_duration_min(leg.duration_min),
            "startAltFt": round(leg.start_altitude_ft),
            "endAltFt": round(leg.end_altitude_ft),
            "bearingDeg": round(leg.bearing_deg, 1),
            "legType": "outbound" if index < len(outbound_legs) else "return",
        }
        for index, leg in enumerate(all_legs)
    )

    outbound_route = tuple(
        (sample.lat, sample.lng) for sample in outbound_trajectory
    )
    return_route = tuple(
        (sample.lat, sample.lng) for sample in return_trajectory
    ) if return_points else ()
    route_markers = _route_markers_for_points(outbound_points, leg="outbound")
    route_markers.extend(trajectory_phase_markers(outbound_trajectory, profile=settings))
    if return_points:
        route_markers.extend(_route_markers_for_points(return_points[1:], leg="return"))
    trajectory_samples = tuple(
        {
            "lat": sample.lat,
            "lng": sample.lng,
            "altitudeFt": round(sample.altitude_ft),
            "phase": sample.phase,
            "distanceM": round(sample.distance_m, 1),
        }
        for sample in outbound_trajectory
    )
    if outbound_trajectory:
        trajectory_distance = outbound_trajectory[-1].distance_m
        return_distance = (
            return_trajectory[-1].distance_m if return_trajectory else 0.0
        )
        if trajectory_distance > 0:
            total_distance_m = trajectory_distance + return_distance

    return FlightPathResult(
        points=tuple(all_points),
        legs=tuple(all_legs),
        total_distance_m=total_distance_m,
        total_duration_min=total_duration_min,
        outbound_route=outbound_route,
        return_route=return_route,
        route_markers=tuple(route_markers),
        final_approach_bearing_deg=final_bearing,
        path3d=tuple(outbound_path3d),
        return_path3d=tuple(return_path3d),
        profile_segments=profile_segments,
        trajectory_samples=trajectory_samples,
    )
