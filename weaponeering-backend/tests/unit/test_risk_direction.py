from __future__ import annotations

import math

from maap_app.modules.detection.risk_direction import (
    RiskDirectionObject,
    bearing_to_compass_label_th,
    calculate_lowest_risk_direction,
    risk_direction_tip_coordinates,
)


def _object_at_bearing(
    target_lat: float,
    target_lng: float,
    bearing: float,
    distance_m: float,
    *,
    risk_level: str,
) -> RiskDirectionObject:
    tip_lat, tip_lng = risk_direction_tip_coordinates(
        target_lat,
        target_lng,
        bearing,
        distance_m,
    )
    return RiskDirectionObject(
        lat=tip_lat,
        lng=tip_lng,
        risk_level=risk_level,
        label="synthetic",
    )


def test_calculate_lowest_risk_direction_without_objects() -> None:
    result = calculate_lowest_risk_direction(
        target_lat=14.0,
        target_lng=100.0,
        objects=[],
        scan_radius_m=120.0,
    )

    assert result.available is False
    assert result.bearing_deg is None
    assert len(result.recommendations) >= 1


def test_calculate_lowest_risk_direction_prefers_clear_sector() -> None:
    target_lat = 14.0
    target_lng = 100.0
    objects = [
        _object_at_bearing(target_lat, target_lng, 90.0, 80.0, risk_level="high"),
        _object_at_bearing(target_lat, target_lng, 100.0, 70.0, risk_level="medium"),
        _object_at_bearing(target_lat, target_lng, 270.0, 60.0, risk_level="low"),
    ]

    result = calculate_lowest_risk_direction(
        target_lat=target_lat,
        target_lng=target_lng,
        objects=objects,
        scan_radius_m=120.0,
    )

    assert result.available is True
    assert result.bearing_deg is not None
    assert result.avoid_bearing_deg is not None
    assert abs(result.bearing_deg - result.avoid_bearing_deg) > 45.0
    assert result.compass_label
    assert len(result.recommended_options) == 3
    assert result.recommended_options[0].rank == 1
    assert result.recommended_options[0].risk_score <= result.recommended_options[1].risk_score
    assert result.recommended_options[0].risk_score > 0
    assert result.avoid_risk_score == 100.0
    assert len(result.recommendations) >= 3


def test_calculate_lowest_risk_direction_returns_three_distinct_options() -> None:
    target_lat = 14.0
    target_lng = 100.0
    objects = [
        _object_at_bearing(target_lat, target_lng, 90.0, 80.0, risk_level="high"),
        _object_at_bearing(target_lat, target_lng, 100.0, 70.0, risk_level="medium"),
        _object_at_bearing(target_lat, target_lng, 270.0, 60.0, risk_level="low"),
    ]

    result = calculate_lowest_risk_direction(
        target_lat=target_lat,
        target_lng=target_lng,
        objects=objects,
        scan_radius_m=120.0,
    )

    bearings = [option.bearing_deg for option in result.recommended_options]
    assert len(bearings) == 3
    scores = [option.risk_score for option in result.recommended_options]
    assert max(scores) - min(scores) >= 0.1
    for option in result.recommended_options:
        assert option.compass_label
        assert 0 < option.risk_score < 100


def test_calculate_lowest_risk_direction_favors_opposite_of_high_risk_cluster() -> None:
    target_lat = 15.0
    target_lng = 101.0
    objects = [
        _object_at_bearing(target_lat, target_lng, 0.0, 50.0, risk_level="high"),
        _object_at_bearing(target_lat, target_lng, 10.0, 55.0, risk_level="high"),
        _object_at_bearing(target_lat, target_lng, 350.0, 45.0, risk_level="high"),
    ]

    result = calculate_lowest_risk_direction(
        target_lat=target_lat,
        target_lng=target_lng,
        objects=objects,
        scan_radius_m=120.0,
    )

    assert result.available is True
    assert result.bearing_deg is not None
    delta = abs(result.bearing_deg - 180.0)
    delta = min(delta, 360.0 - delta)
    assert delta < 60.0


def test_bearing_to_compass_label_th() -> None:
    assert bearing_to_compass_label_th(0.0) == "เหนือ"
    assert bearing_to_compass_label_th(90.0) == "ตะวันออก"
    assert bearing_to_compass_label_th(225.0) == "ตะวันตกเฉียงใต้"


def test_risk_direction_tip_coordinates_moves_expected_distance() -> None:
    tip_lat, tip_lng = risk_direction_tip_coordinates(14.0, 100.0, 0.0, 100.0)
    assert tip_lat > 14.0
    assert math.isclose(tip_lng, 100.0, abs_tol=0.01)
