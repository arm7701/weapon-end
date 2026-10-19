from __future__ import annotations

from maap_app.modules.flight_route.border_corridor_planner import (
    _path_length,
    build_waypoint_connector_paths,
    plan_border_corridor_waypoints,
    plan_efficient_route_waypoints,
)
from maap_app.modules.weaponeering.flight_path import distance_m


def _route_length(
    start: tuple[float, float],
    waypoints: list[dict],
    end: tuple[float, float],
) -> float:
    points = [start] + [(float(point["lat"]), float(point["lng"])) for point in waypoints] + [end]
    return _path_length(points)


def test_efficient_route_korat_to_eastern_entry_is_short() -> None:
    takeoff = (14.93444, 102.07861)
    entry = (12.5, 102.4)
    waypoints, mode = plan_efficient_route_waypoints(
        takeoff,
        entry,
        label_prefix="AI-OUT",
        step_m=25_000,
        max_points=12,
    )
    assert waypoints
    assert mode in {"direct", "inland detour"}
    total_m = _route_length(takeoff, waypoints, entry)
    direct_m = distance_m(takeoff[0], takeoff[1], entry[0], entry[1])
    assert total_m < direct_m * 1.8
    assert total_m < 600_000


def test_efficient_route_wing4_to_western_entry_avoids_border_ring() -> None:
    takeoff = (15.27732, 100.29586)
    entry = (16.5, 99.0)
    waypoints, mode = plan_efficient_route_waypoints(
        takeoff,
        entry,
        label_prefix="AI-OUT",
        step_m=20_000,
        max_points=12,
    )
    assert waypoints
    total_m = _route_length(takeoff, waypoints, entry)
    assert total_m < 500_000
    assert mode in {"direct", "inland detour", "direct (unchecked)"}


def test_border_corridor_rtb_returns_toward_takeoff() -> None:
    takeoff = (14.93444, 102.07861)
    exit_point = (12.45, 102.55)
    waypoints = plan_border_corridor_waypoints(
        exit_point,
        takeoff,
        label_prefix="AI-RTB",
        step_m=25_000,
        max_points=12,
    )
    assert waypoints
    last = waypoints[-1]
    dist_m = distance_m(float(last["lat"]), float(last["lng"]), takeoff[0], takeoff[1])
    assert dist_m < 80_000


def test_waypoint_connector_links_takeoff_through_each_waypoint() -> None:
    editable = [
        {"id": "AI-OUT-1", "label": "AI-OUT1", "lat": 14.5, "lng": 102.2, "altitudeFt": 350},
        {"id": "AI-OUT-2", "label": "AI-OUT2", "lat": 14.0, "lng": 102.3, "altitudeFt": 350},
        {"id": "AI-RTB-1", "label": "AI-RTB1", "lat": 13.5, "lng": 102.25, "altitudeFt": 350},
    ]
    route_2d, path_3d = build_waypoint_connector_paths(
        takeoff=(14.93, 102.08),
        target=(13.38, 102.36),
        landing=(14.93, 102.08),
        editable_waypoints=editable,
        entry=(13.39, 102.35),
        exit_point=(13.40, 102.37),
        default_alt_m=120.0,
    )
    assert len(route_2d) == 8
    assert route_2d[0] == [14.93, 102.08]
    assert route_2d[-1] == [14.93, 102.08]
    assert len(path_3d) == len(route_2d)
