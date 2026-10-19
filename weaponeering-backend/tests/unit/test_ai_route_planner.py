from __future__ import annotations

import pytest

from maap_app.modules.flight_route.ai_planner import plan_ai_flight_route, profile_for_ai_params
from maap_app.modules.flight_route.params import AiRoutePlannerParams, RouteStyle


def test_plan_ai_flight_route_returns_path3d() -> None:
    border_route = {
        "available": True,
        "entry": {"lat": 16.5, "lng": 99.0},
        "exit": {"lat": 16.6, "lng": 99.1},
        "ingressBearingDeg": 45.0,
    }
    route = plan_ai_flight_route(
        takeoff_lat=14.93,
        takeoff_lng=102.08,
        landing_lat=14.93,
        landing_lng=102.08,
        target_lat=16.81,
        target_lng=100.0,
        target_label="Test Target",
        target_card_id="tgt-1",
        coordinate_id="coord-1",
        rank=1,
        border_route=border_route,
        wing_id="wing-1",
        wing_name="Wing A",
        params=AiRoutePlannerParams(route_style=RouteStyle.LOW_LEVEL),
        allow_terrain_network=False,
    )
    assert route is not None
    assert route.get("routeSource") == "ai_planner"
    assert route.get("routeColor") == "#38bdf8"
    assert route.get("drawWaypointConnectors") is True
    assert len(route.get("waypointConnectorPath3d") or []) >= 4
    assert len(route.get("path3d") or []) >= 2
    assert route.get("takeoff") == [14.93, 102.08]
    assert route.get("landing") == [14.93, 102.08]
    assert route["returnRoute"][-1] == pytest.approx([14.93, 102.08], abs=0.01)


def test_plan_ai_flight_route_returns_to_takeoff_when_landing_differs() -> None:
    border_route = {
        "available": True,
        "entry": {"lat": 16.5, "lng": 99.0},
        "exit": {"lat": 16.6, "lng": 99.1},
        "ingressBearingDeg": 45.0,
    }
    route = plan_ai_flight_route(
        takeoff_lat=14.93,
        takeoff_lng=102.08,
        landing_lat=15.10,
        landing_lng=102.20,
        target_lat=16.81,
        target_lng=100.0,
        target_label="Test Target",
        target_card_id="tgt-1",
        coordinate_id="coord-1",
        rank=1,
        border_route=border_route,
        wing_id="wing-1",
        wing_name="Wing A",
        params=AiRoutePlannerParams(route_style=RouteStyle.LOW_LEVEL),
        allow_terrain_network=False,
    )
    assert route is not None
    assert route["returnRoute"][-1][0] == pytest.approx(14.93, abs=0.02)
    assert route["returnRoute"][-1][1] == pytest.approx(102.08, abs=0.02)
    assert route["landing"] == [14.93, 102.08]
