from __future__ import annotations

import math

import pytest

from maap_app.modules.weaponeering.flight_path import (
    FlightProfileSettings,
    FlightWaypointSpec,
    compute_flight_profile,
)
from maap_app.modules.weaponeering.trajectory import (
    angle_delta_deg,
    build_fly_by_horizontal_path,
    climb_horizontal_distance_m,
    descent_horizontal_distance_m,
    lead_distance_m,
    turn_radius_m,
)


def test_turn_radius_at_250kt_bank_25() -> None:
    radius = turn_radius_m(250, 25)
    assert radius == pytest.approx(3600, rel=0.15)


def test_lead_distance_for_60_degree_turn() -> None:
    radius = turn_radius_m(250, 25)
    lead = lead_distance_m(radius, 60)
    assert lead == pytest.approx(radius * math.tan(math.radians(30)), rel=0.01)


def test_angle_delta_normalizes_to_shortest_turn() -> None:
    assert angle_delta_deg(350, 10) == pytest.approx(20.0)
    assert angle_delta_deg(10, 350) == pytest.approx(-20.0)


def test_climb_and_descent_horizontal_distances() -> None:
    profile = FlightProfileSettings(
        cruise_altitude_ft=25000,
        ingress_altitude_ft=1997,
        climb_rate_ft_min=3000,
        descent_rate_ft_min=2000,
        climb_speed_kt=250,
        descent_speed_kt=300,
    )
    climb_dist = climb_horizontal_distance_m(profile)
    descent_dist = descent_horizontal_distance_m(profile)
    assert climb_dist == pytest.approx(64_000, rel=0.15)
    assert descent_dist == pytest.approx(107_000, rel=0.15)


def test_fly_by_path_has_more_points_than_waypoints() -> None:
    waypoints = [
        (16.0, 100.0),
        (16.05, 100.05),
        (16.1, 100.0),
        (16.12, 100.12),
    ]
    path = build_fly_by_horizontal_path(
        waypoints,
        speed_kt=300,
        bank_deg=25,
        turn_mode="fly_by",
        sample_step_m=500,
    )
    assert len(path) > len(waypoints) * 3


def test_compute_flight_profile_uses_dense_trajectory() -> None:
    result = compute_flight_profile(
        takeoff=(14.0, 100.0),
        destination=(17.0, 103.0),
        outbound_waypoints=[
            FlightWaypointSpec(lat=15.5, lng=101.5, label="Corridor"),
        ],
        ingress_bearing_deg=45.0,
        ingress_offset_m=8000,
        profile=FlightProfileSettings(
            bank_angle_deg=25,
            auto_toc_tod=True,
        ),
    )
    assert len(result.outbound_route) > len(result.points)
    assert len(result.path3d) > 20
    assert result.trajectory_samples
    assert any(marker.get("routeCode") == "TOC" for marker in result.route_markers)
    assert any(marker.get("routeCode") == "TOD" for marker in result.route_markers)
    phases = {sample["phase"] for sample in result.trajectory_samples}
    assert "climb" in phases
    assert "cruise" in phases
    assert "descent" in phases
