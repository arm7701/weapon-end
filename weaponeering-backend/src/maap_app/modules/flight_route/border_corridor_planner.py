from __future__ import annotations

import re
from typing import Any

from maap_app.modules.detection.border_route import (
    find_nearest_border,
    load_thailand_multipolygon,
    point_in_thailand,
)
from maap_app.modules.weaponeering.flight_path import bearing_deg, destination_point, distance_m

THAILAND_CENTROID = (13.0, 101.0)
DEFAULT_BORDER_STEP_M = 12_000.0
DEFAULT_INTERIOR_OFFSET_M = 22_000.0
DEFAULT_LATERAL_DISPERSION_M = 5_500.0
INSIDE_CHECK_STEP_M = 5_000.0
MAX_DETOUR_ANCHORS = 4


def _offset_interior(
    point: tuple[float, float],
    *,
    offset_m: float,
) -> tuple[float, float]:
    if offset_m <= 0:
        return point
    bearing = bearing_deg(
        point[0],
        point[1],
        THAILAND_CENTROID[0],
        THAILAND_CENTROID[1],
    )
    lat, lng = destination_point(point[0], point[1], bearing, offset_m)
    return lat, lng


def _apply_route_dispersion(
    path: list[tuple[float, float]],
    *,
    lateral_m: float,
) -> list[tuple[float, float]]:
    """Add gentle S-turns so the track is longer and less radar-visible."""
    if len(path) < 3 or lateral_m <= 0:
        return path
    dispersed = [path[0]]
    for index in range(1, len(path) - 1):
        previous = path[index - 1]
        current = path[index]
        nxt = path[index + 1]
        leg_bearing = bearing_deg(previous[0], previous[1], nxt[0], nxt[1])
        side = 1.0 if index % 2 == 0 else -1.0
        weave = lateral_m * (0.45 + (index % 4) * 0.12)
        offset_bearing = leg_bearing + (90.0 * side)
        dispersed.append(
            destination_point(current[0], current[1], offset_bearing, weave)
        )
    dispersed.append(path[-1])
    return dispersed


def _sample_polyline(
    points: list[tuple[float, float]],
    *,
    step_m: float,
    max_points: int,
) -> list[tuple[float, float]]:
    if len(points) < 2:
        return list(points)
    sampled = [points[0]]
    for index in range(1, len(points)):
        start = sampled[-1]
        end = points[index]
        leg_m = distance_m(start[0], start[1], end[0], end[1])
        if leg_m <= step_m:
            sampled.append(end)
            continue
        steps = max(int(leg_m // step_m), 1)
        bearing = bearing_deg(start[0], start[1], end[0], end[1])
        for step_index in range(1, steps + 1):
            fraction = min(step_index / steps, 1.0)
            distance_along = leg_m * fraction
            lat, lng = destination_point(start[0], start[1], bearing, distance_along)
            sampled.append((lat, lng))
    if len(sampled) > max_points:
        stride = max((len(sampled) - 2) // max(max_points - 2, 1), 1)
        middle = sampled[1:-1:stride]
        sampled = [sampled[0], *middle, sampled[-1]]
    return sampled


def _path_length(path: list[tuple[float, float]]) -> float:
    return sum(
        distance_m(path[index][0], path[index][1], path[index + 1][0], path[index + 1][1])
        for index in range(len(path) - 1)
    )


def _sample_geodesic_line(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    step_m: float,
) -> list[tuple[float, float]]:
    total_m = distance_m(start[0], start[1], end[0], end[1])
    if total_m <= step_m:
        return [start, end]
    bearing = bearing_deg(start[0], start[1], end[0], end[1])
    samples = [start]
    distance_along = step_m
    while distance_along < total_m:
        samples.append(destination_point(start[0], start[1], bearing, distance_along))
        distance_along += step_m
    samples.append(end)
    return samples


def _path_stays_inside_thailand(
    path: list[tuple[float, float]],
    *,
    multipolygon: list,
    check_step_m: float = INSIDE_CHECK_STEP_M,
) -> bool:
    if len(path) < 2:
        return True
    for index in range(len(path) - 1):
        for lat, lng in _sample_geodesic_line(
            path[index],
            path[index + 1],
            step_m=check_step_m,
        ):
            if not point_in_thailand(lat, lng, multipolygon=multipolygon):
                return False
    return True


def _interpolate_along_geodesic(
    start: tuple[float, float],
    end: tuple[float, float],
    fraction: float,
) -> tuple[float, float]:
    total_m = distance_m(start[0], start[1], end[0], end[1])
    if total_m <= 1.0:
        return end
    bearing = bearing_deg(start[0], start[1], end[0], end[1])
    return destination_point(start[0], start[1], bearing, total_m * fraction)


def _inland_anchor_for_point(
    lat: float,
    lng: float,
    *,
    interior_offset_m: float,
    multipolygon: list,
) -> tuple[float, float]:
    nearest = find_nearest_border(lat, lng, multipolygon=multipolygon)
    base = (nearest.lat, nearest.lng) if nearest is not None else (lat, lng)
    return _offset_interior(base, offset_m=interior_offset_m)


def _minimal_inland_detour_path(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    interior_offset_m: float,
    multipolygon: list,
) -> list[tuple[float, float]]:
    """Bend the route inward only where the direct line would leave Thailand."""
    samples = _sample_geodesic_line(start, end, step_m=INSIDE_CHECK_STEP_M)
    outside = [
        (lat, lng)
        for lat, lng in samples
        if not point_in_thailand(lat, lng, multipolygon=multipolygon)
    ]
    if not outside:
        return [start, end]

    anchors: list[tuple[float, float]] = []
    for fraction in (0.25, 0.5, 0.75):
        lat, lng = _interpolate_along_geodesic(start, end, fraction)
        if not point_in_thailand(lat, lng, multipolygon=multipolygon):
            anchors.append(
                _inland_anchor_for_point(
                    lat,
                    lng,
                    interior_offset_m=interior_offset_m,
                    multipolygon=multipolygon,
                )
            )
        if len(anchors) >= MAX_DETOUR_ANCHORS:
            break

    if not anchors:
        avg_lat = sum(point[0] for point in outside) / len(outside)
        avg_lng = sum(point[1] for point in outside) / len(outside)
        anchors.append(
            _inland_anchor_for_point(
                avg_lat,
                avg_lng,
                interior_offset_m=interior_offset_m,
                multipolygon=multipolygon,
            )
        )

    deduped: list[tuple[float, float]] = []
    for anchor in anchors:
        if not deduped or distance_m(anchor[0], anchor[1], deduped[-1][0], deduped[-1][1]) > 5_000:
            deduped.append(anchor)

    return [start, *deduped, end]


def _resolve_efficient_route_path(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    interior_offset_m: float,
    multipolygon: list,
) -> tuple[list[tuple[float, float]], str]:
    direct = [start, end]
    if _path_stays_inside_thailand(direct, multipolygon=multipolygon):
        return direct, "direct"

    detour = _minimal_inland_detour_path(
        start,
        end,
        interior_offset_m=interior_offset_m,
        multipolygon=multipolygon,
    )
    if _path_stays_inside_thailand(detour, multipolygon=multipolygon):
        return detour, "inland detour"

    return direct, "direct (unchecked)"


def _waypoints_from_path(
    path_points: list[tuple[float, float]],
    *,
    label_prefix: str,
    step_m: float,
    max_points: int,
    lateral_dispersion_m: float,
    altitude_ft: int,
) -> list[dict[str, Any]]:
    if len(path_points) < 2:
        return []

    working = list(path_points)
    if len(working) > 2 and lateral_dispersion_m > 0:
        working = _apply_route_dispersion(working, lateral_m=lateral_dispersion_m * 0.35)

    sampled = _sample_polyline(working, step_m=step_m, max_points=max_points + 2)
    waypoints: list[dict[str, Any]] = []
    for index, (lat, lng) in enumerate(sampled[1:-1], start=1):
        waypoints.append(
            {
                "id": f"{label_prefix}-{index}",
                "lat": lat,
                "lng": lng,
                "label": f"{label_prefix}{index}",
                "altitudeFt": altitude_ft,
            }
        )
    return waypoints


def plan_efficient_route_waypoints(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    label_prefix: str,
    step_m: float = DEFAULT_BORDER_STEP_M,
    max_points: int = 24,
    interior_offset_m: float = DEFAULT_INTERIOR_OFFSET_M,
    lateral_dispersion_m: float = DEFAULT_LATERAL_DISPERSION_M,
    altitude_ft: int = 350,
) -> tuple[list[dict[str, Any]], str]:
    """Prefer the shortest path; offset inland only where a direct leg would cross the border."""
    multipolygon = load_thailand_multipolygon()
    path_points, mode = _resolve_efficient_route_path(
        start,
        end,
        interior_offset_m=interior_offset_m,
        multipolygon=multipolygon,
    )
    waypoints = _waypoints_from_path(
        path_points,
        label_prefix=label_prefix,
        step_m=step_m,
        max_points=max_points,
        lateral_dispersion_m=lateral_dispersion_m,
        altitude_ft=altitude_ft,
    )
    return waypoints, mode


def plan_border_corridor_waypoints(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    label_prefix: str,
    step_m: float = DEFAULT_BORDER_STEP_M,
    max_points: int = 24,
    interior_offset_m: float = DEFAULT_INTERIOR_OFFSET_M,
    lateral_dispersion_m: float = DEFAULT_LATERAL_DISPERSION_M,
    altitude_ft: int = 350,
) -> list[dict[str, Any]]:
    waypoints, _mode = plan_efficient_route_waypoints(
        start,
        end,
        label_prefix=label_prefix,
        step_m=step_m,
        max_points=max_points,
        interior_offset_m=interior_offset_m,
        lateral_dispersion_m=lateral_dispersion_m,
        altitude_ft=altitude_ft,
    )
    return waypoints


def _waypoint_sort_key(waypoint: dict[str, Any]) -> int:
    label = str(waypoint.get("label") or waypoint.get("id") or "")
    match = re.search(r"(\d+)\s*$", label)
    return int(match.group(1)) if match else 0


def _filter_waypoints(waypoints: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for waypoint in waypoints:
        waypoint_id = str(waypoint.get("id") or "")
        label = str(waypoint.get("label") or "")
        if waypoint_id.startswith(prefix) or label.startswith(prefix):
            filtered.append(waypoint)
    return sorted(filtered, key=_waypoint_sort_key)


def build_waypoint_connector_paths(
    *,
    takeoff: tuple[float, float],
    target: tuple[float, float],
    landing: tuple[float, float],
    editable_waypoints: list[dict[str, Any]],
    entry: tuple[float, float] | None = None,
    exit_point: tuple[float, float] | None = None,
    default_alt_m: float = 120.0,
) -> tuple[list[list[float]], list[list[float]]]:
    """Geodesic chain through every waypoint for map segment lines."""
    outbound = _filter_waypoints(editable_waypoints, "AI-OUT")
    return_wps = _filter_waypoints(editable_waypoints, "AI-RTB")

    chain: list[tuple[float, float, float]] = [
        (takeoff[0], takeoff[1], default_alt_m),
    ]
    for waypoint in outbound:
        alt_m = float(waypoint.get("altitudeFt") or 0) * 0.3048 or default_alt_m
        chain.append((float(waypoint["lat"]), float(waypoint["lng"]), alt_m))
    if entry is not None:
        chain.append((entry[0], entry[1], default_alt_m))
    chain.append((target[0], target[1], default_alt_m))
    if exit_point is not None:
        chain.append((exit_point[0], exit_point[1], default_alt_m))
    for waypoint in return_wps:
        alt_m = float(waypoint.get("altitudeFt") or 0) * 0.3048 or default_alt_m
        chain.append((float(waypoint["lat"]), float(waypoint["lng"]), alt_m))
    chain.append((landing[0], landing[1], default_alt_m))

    route_2d = [[lat, lng] for lat, lng, _alt in chain]
    path_3d = [[lat, lng, alt_m] for lat, lng, alt_m in chain]
    return route_2d, path_3d
