from __future__ import annotations

import pytest

from maap_app.modules.detection.border_route import (
    calculate_ingress_border_route,
    find_border_crossing_along_bearing,
    find_nearest_border,
    find_nearest_border_point_on_axis,
    point_in_thailand,
    resolve_target_for_border_route,
)
from maap_app.modules.detection.risk_direction import (
    RiskDirectionObject,
    calculate_lowest_risk_direction,
    risk_direction_tip_coordinates,
)


def test_point_in_thailand_for_bangkok() -> None:
    assert point_in_thailand(13.7563, 100.5018) is True


def test_point_in_thailand_for_outside_point() -> None:
    assert point_in_thailand(3.0, 100.0) is False


def test_find_border_crossing_from_bangkok_north() -> None:
    crossing = find_border_crossing_along_bearing(
        origin_lat=13.7563,
        origin_lng=100.5018,
        bearing_deg=0.0,
        start_inside=True,
    )

    assert crossing is not None
    assert crossing.distance_m > 50_000.0
    assert crossing.lat > 13.7563
    assert point_in_thailand(crossing.lat, crossing.lng) is False


def test_calculate_ingress_border_route_returns_entry_and_exit() -> None:
    route = calculate_ingress_border_route(
        target_lat=14.0,
        target_lng=101.0,
        approach_bearing_deg=0.0,
    )

    assert route.available is True
    assert route.ingress_bearing_deg == 180.0
    assert route.entry is not None
    assert route.exit is not None
    assert route.entry.bearing_deg == pytest.approx(180.0, abs=1.0)
    assert route.exit.bearing_deg == pytest.approx(0.0, abs=1.0)
    assert route.total_corridor_m is not None
    assert route.total_corridor_m > 0.0


def test_border_route_snaps_near_border_targets_inside_simplified_gaps() -> None:
    target_lat = 13.38110
    target_lng = 102.36020
    assert point_in_thailand(target_lat, target_lng) is False

    resolved = resolve_target_for_border_route(target_lat, target_lng)
    assert resolved is not None
    assert resolved.snapped is True
    assert point_in_thailand(resolved.lat, resolved.lng) is True

    route = calculate_ingress_border_route(
        target_lat=target_lat,
        target_lng=target_lng,
        approach_bearing_deg=75.0,
    )
    assert route.available is True
    assert route.entry is not None
    assert route.exit is not None
    assert route.entry.bearing_deg == pytest.approx(255.0, abs=1.0)
    assert route.exit.bearing_deg == pytest.approx(75.0, abs=1.0)
    assert route.entry.distance_m < 5_000.0
    assert route.exit.distance_m < 5_000.0


def test_find_nearest_border_point_on_axis_prefers_closest_aligned_point() -> None:
    target_lat = 13.38110
    target_lng = 102.36020
    nearest = find_nearest_border_point_on_axis(
        target_lat,
        target_lng,
        255.0,
        max_distance_m=5_000.0,
    )
    assert nearest is not None
    assert nearest.distance_m < 1_000.0
    assert nearest.bearing_deg == pytest.approx(255.0, abs=1.0)


def test_find_nearest_border_uses_target_coordinates() -> None:
    nearest = find_nearest_border(13.38110, 102.36020)
    assert nearest is not None
    assert nearest.distance_m > 0.0
    assert nearest.distance_m < 30_000.0


def test_risk_direction_includes_border_route_payload() -> None:
    target_lat = 14.0
    target_lng = 101.0
    tip_lat, tip_lng = risk_direction_tip_coordinates(
        target_lat,
        target_lng,
        90.0,
        80.0,
    )
    objects = [
        RiskDirectionObject(
            lat=tip_lat,
            lng=tip_lng,
            risk_level="high",
            label="synthetic",
        )
    ]

    result = calculate_lowest_risk_direction(
        target_lat=target_lat,
        target_lng=target_lng,
        objects=objects,
        scan_radius_m=120.0,
    )
    payload = result.to_map_payload()

    assert result.available is True
    assert payload.get("borderRoute") is not None
    options = payload.get("recommendedOptions") or []
    assert options
    assert options[0].get("ingressBearingDeg") is not None
    assert options[0].get("borderRoute") is not None
