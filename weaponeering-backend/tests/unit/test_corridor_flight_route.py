from __future__ import annotations

import pytest

from maap_app.modules.detection.corridor_flight_route import (
    build_deployment_plan_corridor_route,
    build_ingress_corridor_flight_route,
    build_waypoint_sketch_route,
)
from maap_app.modules.weaponeering.models import (
    TargetDeploymentPlan,
    TargetDeploymentWaypoint,
)


def _sample_border_route() -> dict:
    return {
        "available": True,
        "ingressBearingDeg": 255.0,
        "approachBearingDeg": 75.0,
        "entry": {
            "lat": 13.380228,
            "lng": 102.356854,
            "bearingDeg": 255.0,
            "distanceM": 374.7,
        },
        "exit": {
            "lat": 13.385388,
            "lng": 102.376651,
            "bearingDeg": 75.0,
            "distanceM": 1842.4,
        },
    }


def test_build_ingress_corridor_flight_route_recovers_at_takeoff_by_default() -> None:
    payload = build_ingress_corridor_flight_route(
        wing_lat=14.93444,
        wing_lng=102.07861,
        wing_name="Wing-1",
        wing_id="wing-1",
        target_lat=13.38110,
        target_lng=102.36020,
        target_label="TGT-003",
        target_card_id="tgt-3",
        coordinate_id="coord-1",
        rank=1,
        border_route=_sample_border_route(),
    )

    assert payload is not None
    assert payload["returnRoute"][-1][0] == pytest.approx(14.93444, abs=0.02)
    assert payload["returnRoute"][-1][1] == pytest.approx(102.07861, abs=0.02)


def test_build_ingress_corridor_flight_route_can_override_recovery_point() -> None:
    payload = build_ingress_corridor_flight_route(
        wing_lat=14.93444,
        wing_lng=102.07861,
        wing_name="Wing-1",
        wing_id="wing-1",
        target_lat=13.38110,
        target_lng=102.36020,
        target_label="TGT-003",
        target_card_id="tgt-3",
        coordinate_id="coord-1",
        rank=1,
        border_route=_sample_border_route(),
        recovery_point=(15.10, 102.20),
    )

    assert payload is not None
    assert payload["returnRoute"][-1][0] == pytest.approx(15.10, abs=0.02)
    assert payload["returnRoute"][-1][1] == pytest.approx(102.20, abs=0.02)


def test_build_ingress_corridor_flight_route_includes_entry_target_exit_and_rtb() -> None:
    payload = build_ingress_corridor_flight_route(
        wing_lat=14.93444,
        wing_lng=102.07861,
        wing_name="Wing-1",
        wing_id="wing-1",
        target_lat=13.38110,
        target_lng=102.36020,
        target_label="TGT-003",
        target_card_id="tgt-3",
        coordinate_id="coord-1",
        rank=1,
        border_route=_sample_border_route(),
    )

    assert payload is not None
    assert payload["routeStyle"] == "curved_fly_by"
    assert payload["routeSource"] == "corridor_auto"
    assert len(payload["outboundRoute"]) >= 20
    assert len(payload["returnRoute"]) >= 10
    assert payload["outboundRoute"][0][0] == pytest.approx(14.93444)
    assert payload["returnRoute"][-1][0] == pytest.approx(14.93444)
    assert payload["routeMarkers"][0]["pointType"] == "takeoff"
    assert "Wing-1" in str(payload["summary"])
    assert "fly-by" in str(payload["summary"])
    assert payload.get("showReturnRoute") is True


def test_curved_corridor_route_has_more_points_than_straight_legs() -> None:
    payload = build_ingress_corridor_flight_route(
        wing_lat=14.0,
        wing_lng=100.0,
        wing_name="Wing-A",
        wing_id="wing-a",
        target_lat=16.0,
        target_lng=101.0,
        target_label="TGT-A",
        target_card_id="tgt-a",
        coordinate_id=None,
        rank=1,
        border_route={
            "available": True,
            "ingressBearingDeg": 90.0,
            "entry": {"lat": 15.0, "lng": 100.5, "bearingDeg": 90.0, "distanceM": 1000},
            "exit": {"lat": 15.2, "lng": 101.2, "bearingDeg": 270.0, "distanceM": 1000},
        },
    )
    assert payload is not None
    assert len(payload["outboundRoute"]) > 8
    assert payload.get("path3d")


def test_auto_corridor_visits_border_entry_before_target() -> None:
    wing = (14.93444, 102.07861)
    target = (13.38110, 102.36020)
    entry = (13.380228, 102.356854)
    payload = build_ingress_corridor_flight_route(
        wing_lat=wing[0],
        wing_lng=wing[1],
        wing_name="Wing-1",
        wing_id="wing-1",
        target_lat=target[0],
        target_lng=target[1],
        target_label="TGT-003",
        target_card_id="tgt-3",
        coordinate_id="coord-1",
        rank=1,
        border_route=_sample_border_route(),
    )
    assert payload is not None
    route = payload["outboundRoute"]

    def closest_idx(point: tuple[float, float]) -> int:
        return min(
            range(len(route)),
            key=lambda index: (route[index][0] - point[0]) ** 2
            + (route[index][1] - point[1]) ** 2,
        )

    entry_idx = closest_idx(entry)
    target_idx = closest_idx(target)
    assert entry_idx < target_idx
    assert not any(
        marker.get("routeCode") in {"TOC", "TOD"} for marker in payload["routeMarkers"]
    )


def test_deployment_plan_corridor_route_uses_saved_waypoints() -> None:
    plan = TargetDeploymentPlan(
        id="plan-1",
        scenario_id="scenario-1",
        target_card_id="tgt-3",
        wing_id="wing-1",
        flying_unit_id="unit-1",
        aircraft_lines=(),
        takeoff_lat=14.93444,
        takeoff_lng=102.07861,
        ingress_bearing_deg=255.0,
        ingress_offset_m=8000,
        waypoints=(
            TargetDeploymentWaypoint(
                id="wp-1",
                plan_id="plan-1",
                waypoint_type="fly_through",
                label="Hold-A",
                lat=14.20,
                lng=102.10,
                sort_order=0,
            ),
            TargetDeploymentWaypoint(
                id="wp-2",
                plan_id="plan-1",
                waypoint_type="return",
                label="RTB-1",
                lat=14.50,
                lng=102.20,
                sort_order=1,
            ),
        ),
    )
    payload = build_deployment_plan_corridor_route(
        plan=plan,
        wing_lat=14.93444,
        wing_lng=102.07861,
        wing_name="Wing-1",
        wing_id="wing-1",
        target_lat=13.38110,
        target_lng=102.36020,
        target_label="TGT-003",
        target_card_id="tgt-3",
        coordinate_id="coord-1",
        rank=1,
        border_route=_sample_border_route(),
    )

    assert payload is not None
    assert payload["routeSource"] == "weaponeering_plan"
    assert payload["routeColor"] == "#38bdf8"
    assert "แผน Weaponeering" in payload["summary"]
    assert len(payload["outboundRoute"]) >= 20
    marker_labels = {
        str(marker.get("label") or "") for marker in payload["routeMarkers"]
    }
    assert "Hold-A" in marker_labels or any(
        marker.get("routeCode") == "WP1" for marker in payload["routeMarkers"]
    )


def test_build_waypoint_sketch_route_follows_waypoints_exactly() -> None:
    payload = build_waypoint_sketch_route(
        wing_lat=14.0,
        wing_lng=100.0,
        wing_name="Wing-A",
        wing_id="wing-a",
        target_lat=16.0,
        target_lng=101.0,
        target_label="TGT-A",
        target_card_id="tgt-a",
        coordinate_id=None,
        rank=1,
        fly_through_waypoints=[
            {"id": "wp-1", "lat": 14.5, "lng": 100.2, "label": "A"},
            {"id": "wp-2", "lat": 15.0, "lng": 100.5, "label": "B"},
        ],
    )

    assert payload["routeStyle"] == "waypoint_polyline"
    assert payload["outboundRoute"] == [
        [14.0, 100.0],
        [14.5, 100.2],
        [15.0, 100.5],
    ]
    assert payload["fitToRoute"] is False
    assert len(payload["outboundRoute"]) == 3
