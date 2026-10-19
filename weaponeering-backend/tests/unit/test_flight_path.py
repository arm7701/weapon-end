from __future__ import annotations

import pytest

from maap_app.modules.weaponeering.flight_path import (
    FlightProfileSettings,
    FlightWaypointSpec,
    bearing_deg,
    compute_flight_path,
    compute_flight_profile,
    destination_point,
    distance_m,
    normalize_bearing_deg,
)


def test_bearing_deg_points_north_and_east() -> None:
    assert normalize_bearing_deg(370) == 10
    assert bearing_deg(0.0, 0.0, 1.0, 0.0) == pytest.approx(0.0, abs=1.0)
    assert bearing_deg(0.0, 0.0, 0.0, 1.0) == pytest.approx(90.0, abs=1.0)


def test_destination_point_moves_expected_distance() -> None:
    lat, lng = destination_point(16.0, 100.0, 0.0, 1000.0)
    moved = distance_m(16.0, 100.0, lat, lng)
    assert moved == pytest.approx(1000.0, rel=0.01)


def test_compute_flight_profile_with_waypoints_and_ingress() -> None:
    result = compute_flight_profile(
        takeoff=(16.0, 100.0),
        destination=(16.1, 100.1),
        outbound_waypoints=[
            FlightWaypointSpec(lat=16.05, lng=100.02, label="Corridor"),
        ],
        ingress_bearing_deg=45.0,
        ingress_offset_m=5000,
    )

    assert result.points[0].point_type == "takeoff"
    assert result.points[0].altitude_ft == 0.0
    assert any(point.point_type == "fly_through" for point in result.points)
    assert any(point.point_type == "ingress" for point in result.points)
    assert any(point.point_type == "target" for point in result.points)
    assert result.points[-1].point_type == "takeoff"
    assert len(result.legs) >= 3
    assert result.total_distance_m > 0
    assert result.total_duration_min > 0
    assert result.final_approach_bearing_deg == 45.0
    assert len(result.path3d) > 10
    assert len(result.outbound_route) >= 2
    assert result.route_markers
    assert result.route_markers[0]["routeCode"] == "DEP"


def test_compute_flight_profile_includes_return_path() -> None:
    result = compute_flight_profile(
        takeoff=(16.0, 100.0),
        destination=(16.08, 100.08),
        outbound_waypoints=[
            FlightWaypointSpec(lat=16.04, lng=100.04, label="WP1"),
        ],
        profile=FlightProfileSettings(return_enabled=True),
    )

    assert len(result.return_path3d) > 10
    assert result.total_distance_m > distance_m(16.0, 100.0, 16.08, 100.08)
    assert any(segment["legType"] == "return" for segment in result.profile_segments)


def test_compute_flight_path_wrapper_still_works() -> None:
    result = compute_flight_path(
        takeoff=(16.0, 100.0),
        destination=(16.05, 100.05),
    )

    assert len(result.points) >= 2
    assert result.total_duration_min > 0


def test_compute_flight_profile_assigns_cruise_and_descent_altitudes() -> None:
    result = compute_flight_profile(
        takeoff=(16.0, 100.0),
        destination=(16.1, 100.1),
        outbound_waypoints=[FlightWaypointSpec(lat=16.05, lng=100.05, label="WP")],
        ingress_bearing_deg=90.0,
        ingress_offset_m=8000,
        profile=FlightProfileSettings(
            cruise_altitude_ft=25000,
            ingress_altitude_ft=5000,
            target_altitude_ft=1500,
            return_enabled=False,
        ),
    )

    cruise_points = [
        point for point in result.points if point.point_type == "fly_through"
    ]
    assert cruise_points
    assert cruise_points[0].altitude_ft == pytest.approx(25000.0)
    ingress = next(point for point in result.points if point.point_type == "ingress")
    assert ingress.altitude_ft == pytest.approx(5000.0)
    assert result.points[-1].altitude_ft == pytest.approx(1500.0)
