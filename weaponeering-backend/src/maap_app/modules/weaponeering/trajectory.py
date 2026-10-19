from __future__ import annotations

import math
from dataclasses import dataclass

from maap_app.modules.weaponeering.flight_path import (
    FT_TO_M,
    FlightProfileSettings,
    bearing_deg,
    destination_point,
    distance_m,
    normalize_bearing_deg,
)


GRAVITY_MPS2 = 9.81
KT_TO_MPS = 0.514444
DEFAULT_SAMPLE_STEP_M = 250.0


@dataclass(frozen=True)
class TrajectorySample:
    lat: float
    lng: float
    altitude_ft: float
    phase: str
    distance_m: float = 0.0


def knots_to_mps(knots: float) -> float:
    return knots * KT_TO_MPS


def turn_radius_m(speed_kt: float, bank_deg: float) -> float:
    if bank_deg <= 0.5:
        return 1_000_000.0
    velocity = knots_to_mps(speed_kt)
    phi = math.radians(bank_deg)
    return (velocity * velocity) / (GRAVITY_MPS2 * math.tan(phi))


def angle_delta_deg(bearing_in: float, bearing_out: float) -> float:
    delta = bearing_out - bearing_in
    while delta > 180.0:
        delta -= 360.0
    while delta < -180.0:
        delta += 360.0
    return delta


def lead_distance_m(radius_m: float, delta_deg: float) -> float:
    half_angle = math.radians(abs(delta_deg) / 2.0)
    if half_angle < 1e-6:
        return 0.0
    return radius_m * math.tan(half_angle)


def climb_horizontal_distance_m(profile: FlightProfileSettings) -> float:
    if profile.climb_rate_ft_min <= 0:
        return 0.0
    climb_minutes = profile.cruise_altitude_ft / profile.climb_rate_ft_min
    return knots_to_mps(profile.climb_speed_kt) * climb_minutes * 60.0


def descent_horizontal_distance_m(profile: FlightProfileSettings) -> float:
    if profile.descent_rate_ft_min <= 0:
        return 0.0
    delta_alt = max(profile.cruise_altitude_ft - profile.ingress_altitude_ft, 0)
    descent_minutes = delta_alt / profile.descent_rate_ft_min
    return knots_to_mps(profile.descent_speed_kt) * descent_minutes * 60.0


def _append_geodesic_samples(
    path: list[tuple[float, float]],
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    step_m: float,
) -> None:
    if start == end:
        return
    leg_distance = distance_m(start[0], start[1], end[0], end[1])
    if leg_distance <= step_m:
        if not path or path[-1] != end:
            path.append(end)
        return
    bearing = bearing_deg(start[0], start[1], end[0], end[1])
    samples = max(int(leg_distance / step_m), 1)
    for index in range(1, samples + 1):
        offset = leg_distance * (index / samples)
        point = destination_point(start[0], start[1], bearing, offset)
        if not path or (
            abs(path[-1][0] - point[0]) > 1e-8 or abs(path[-1][1] - point[1]) > 1e-8
        ):
            path.append(point)


def _append_turn_arc(
    path: list[tuple[float, float]],
    entry: tuple[float, float],
    exit_point: tuple[float, float],
    *,
    bearing_in: float,
    bearing_out: float,
    radius_m: float,
    delta_deg: float,
    step_m: float,
) -> None:
    if abs(delta_deg) < 3.0:
        _append_geodesic_samples(path, entry, exit_point, step_m=step_m)
        return
    turn_dir = 1.0 if delta_deg > 0 else -1.0
    center_bearing = normalize_bearing_deg(bearing_in + 90.0 * turn_dir)
    center = destination_point(entry[0], entry[1], center_bearing, radius_m)
    arc_length = radius_m * math.radians(abs(delta_deg))
    samples = max(int(arc_length / step_m), 6)
    start_bearing = bearing_deg(center[0], center[1], entry[0], entry[1])
    for index in range(1, samples + 1):
        fraction = index / samples
        angle = normalize_bearing_deg(start_bearing + turn_dir * abs(delta_deg) * fraction)
        point = destination_point(center[0], center[1], angle, radius_m)
        if not path or (
            abs(path[-1][0] - point[0]) > 1e-8 or abs(path[-1][1] - point[1]) > 1e-8
        ):
            path.append(point)


def build_fly_by_horizontal_path(
    waypoints: list[tuple[float, float]],
    *,
    speed_kt: float,
    bank_deg: float,
    turn_mode: str = "fly_by",
    sample_step_m: float = DEFAULT_SAMPLE_STEP_M,
) -> list[tuple[float, float]]:
    if len(waypoints) < 2:
        return list(waypoints)
    if turn_mode != "fly_by" or len(waypoints) == 2:
        path: list[tuple[float, float]] = [waypoints[0]]
        for index in range(1, len(waypoints)):
            _append_geodesic_samples(
                path,
                path[-1],
                waypoints[index],
                step_m=sample_step_m,
            )
        return path

    radius = turn_radius_m(speed_kt, bank_deg)
    path: list[tuple[float, float]] = [waypoints[0]]
    current = waypoints[0]

    for index in range(1, len(waypoints) - 1):
        previous = waypoints[index - 1]
        waypoint = waypoints[index]
        nxt = waypoints[index + 1]
        bearing_in = bearing_deg(previous[0], previous[1], waypoint[0], waypoint[1])
        bearing_out = bearing_deg(waypoint[0], waypoint[1], nxt[0], nxt[1])
        delta = angle_delta_deg(bearing_in, bearing_out)
        inbound_leg = distance_m(previous[0], previous[1], waypoint[0], waypoint[1])
        outbound_leg = distance_m(waypoint[0], waypoint[1], nxt[0], nxt[1])
        lead = lead_distance_m(radius, delta)
        lead = min(lead, inbound_leg * 0.45, outbound_leg * 0.45)

        if lead < 80.0 or abs(delta) < 5.0:
            _append_geodesic_samples(path, current, waypoint, step_m=sample_step_m)
            current = waypoint
            continue

        entry = destination_point(waypoint[0], waypoint[1], bearing_in + 180.0, lead)
        exit_point = destination_point(waypoint[0], waypoint[1], bearing_out, lead)
        _append_geodesic_samples(path, current, entry, step_m=sample_step_m)
        _append_turn_arc(
            path,
            entry,
            exit_point,
            bearing_in=bearing_in,
            bearing_out=bearing_out,
            radius_m=radius,
            delta_deg=delta,
            step_m=sample_step_m,
        )
        current = exit_point

    _append_geodesic_samples(path, current, waypoints[-1], step_m=sample_step_m)
    return path


def _cumulative_distances(path: list[tuple[float, float]]) -> list[float]:
    if not path:
        return []
    cumulative = [0.0]
    for index in range(1, len(path)):
        cumulative.append(
            cumulative[-1]
            + distance_m(
                path[index - 1][0],
                path[index - 1][1],
                path[index][0],
                path[index][1],
            )
        )
    return cumulative


def assign_vertical_profile(
    path: list[tuple[float, float]],
    *,
    profile: FlightProfileSettings,
) -> list[TrajectorySample]:
    if not path:
        return []
    cumulative = _cumulative_distances(path)
    total_distance = cumulative[-1]
    climb_dist = (
        climb_horizontal_distance_m(profile) if profile.auto_toc_tod else 0.0
    )
    descent_dist = (
        descent_horizontal_distance_m(profile) if profile.auto_toc_tod else 0.0
    )
    tod_start = max(total_distance - descent_dist, climb_dist)
    descent_delta = max(profile.cruise_altitude_ft - profile.ingress_altitude_ft, 0)

    samples: list[TrajectorySample] = []
    for index, (lat, lng) in enumerate(path):
        distance_along = cumulative[index]
        if distance_along <= climb_dist and climb_dist > 0:
            altitude = profile.cruise_altitude_ft * (distance_along / climb_dist)
            phase = "climb"
        elif distance_along >= tod_start and descent_dist > 0:
            fraction = (distance_along - tod_start) / descent_dist
            altitude = profile.cruise_altitude_ft - descent_delta * min(fraction, 1.0)
            phase = "descent"
        else:
            altitude = float(profile.cruise_altitude_ft)
            phase = "cruise"

        if index == len(path) - 1:
            altitude = float(profile.target_altitude_ft)
            phase = "attack"
        if index == 0:
            altitude = 0.0
            phase = "takeoff"

        samples.append(
            TrajectorySample(
                lat=lat,
                lng=lng,
                altitude_ft=altitude,
                phase=phase,
                distance_m=distance_along,
            )
        )
    return samples


def build_realistic_trajectory(
    waypoints: list[tuple[float, float]],
    *,
    profile: FlightProfileSettings,
) -> list[TrajectorySample]:
    horizontal = build_fly_by_horizontal_path(
        waypoints,
        speed_kt=profile.cruise_speed_kt,
        bank_deg=profile.bank_angle_deg,
        turn_mode=profile.turn_mode,
    )
    return assign_vertical_profile(horizontal, profile=profile)


def assign_return_vertical_profile(
    path: list[tuple[float, float]],
    *,
    profile: FlightProfileSettings,
) -> list[TrajectorySample]:
    if not path:
        return []
    cumulative = _cumulative_distances(path)
    total_distance = cumulative[-1]
    climb_delta = max(profile.cruise_altitude_ft - profile.target_altitude_ft, 0)
    climb_minutes = (
        climb_delta / profile.climb_rate_ft_min if profile.climb_rate_ft_min > 0 else 0
    )
    climb_dist = knots_to_mps(profile.climb_speed_kt) * climb_minutes * 60.0
    descent_minutes = (
        profile.cruise_altitude_ft / profile.descent_rate_ft_min
        if profile.descent_rate_ft_min > 0
        else 0
    )
    descent_dist = knots_to_mps(profile.descent_speed_kt) * descent_minutes * 60.0
    tod_start = max(total_distance - descent_dist, climb_dist)

    samples: list[TrajectorySample] = []
    for index, (lat, lng) in enumerate(path):
        distance_along = cumulative[index]
        if distance_along <= climb_dist and climb_dist > 0:
            altitude = profile.target_altitude_ft + climb_delta * (
                distance_along / climb_dist
            )
            phase = "rtb_climb"
        elif distance_along >= tod_start and descent_dist > 0:
            fraction = (distance_along - tod_start) / descent_dist
            altitude = profile.cruise_altitude_ft * (1.0 - min(fraction, 1.0))
            phase = "rtb_descent"
        else:
            altitude = float(profile.cruise_altitude_ft)
            phase = "rtb_cruise"

        if index == 0:
            altitude = float(profile.target_altitude_ft)
            phase = "attack"
        if index == len(path) - 1:
            altitude = 0.0
            phase = "landing"

        samples.append(
            TrajectorySample(
                lat=lat,
                lng=lng,
                altitude_ft=altitude,
                phase=phase,
                distance_m=distance_along,
            )
        )
    return samples


def build_return_trajectory(
    waypoints: list[tuple[float, float]],
    *,
    profile: FlightProfileSettings,
) -> list[TrajectorySample]:
    horizontal = build_fly_by_horizontal_path(
        waypoints,
        speed_kt=profile.cruise_speed_kt,
        bank_deg=profile.bank_angle_deg,
        turn_mode=profile.turn_mode,
    )
    return assign_return_vertical_profile(horizontal, profile=profile)


def trajectory_to_path3d(
    samples: list[TrajectorySample],
) -> list[tuple[float, float, float]]:
    return [(sample.lat, sample.lng, sample.altitude_ft * FT_TO_M) for sample in samples]


def trajectory_phase_markers(
    samples: list[TrajectorySample],
    *,
    profile: FlightProfileSettings,
) -> list[dict[str, object]]:
    if not samples:
        return []
    markers: list[dict[str, object]] = []
    climb_dist = climb_horizontal_distance_m(profile)
    descent_dist = descent_horizontal_distance_m(profile)
    total = samples[-1].distance_m

    def _nearest(distance_target: float, label: str, code: str, phase: str) -> None:
        if distance_target < 0:
            return
        distance_target = min(distance_target, total)
        nearest = min(samples, key=lambda s: abs(s.distance_m - distance_target))
        markers.append(
            {
                "lat": nearest.lat,
                "lng": nearest.lng,
                "label": label,
                "pointType": phase,
                "routeCode": code,
                "altitudeFt": round(nearest.altitude_ft),
                "phase": phase,
                "leg": "outbound",
            }
        )

    if profile.auto_toc_tod:
        _nearest(climb_dist, "TOC", "TOC", "toc")
        _nearest(max(total - descent_dist, 0), "TOD", "TOD", "tod")
    return markers
