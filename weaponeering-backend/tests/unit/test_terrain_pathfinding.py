from __future__ import annotations

import pytest

from maap_app.modules.flight_route.astar import GridNode, astar_on_grid, simplify_path
from maap_app.modules.flight_route.params import AiRoutePlannerParams, RouteStyle
from maap_app.modules.flight_route.segment_planner import plan_three_segment_waypoints
from maap_app.modules.flight_route.terrain_sampler import FlatTerrainSampler


def test_astar_finds_path_on_open_grid() -> None:
    rows, cols = 12, 12

    def lat_lng_for(row: int, col: int) -> tuple[float, float]:
        return 14.0 + row * 0.01, 100.0 + col * 0.01

    result = astar_on_grid(
        rows=rows,
        cols=cols,
        cell_cost=[1.0] * (rows * cols),
        passable=[True] * (rows * cols),
        lat_lng_for=lat_lng_for,
        start=GridNode(0, 0),
        goal=GridNode(11, 11),
    )
    assert result is not None
    assert len(result.path) >= 2
    assert result.path[0] == pytest.approx(lat_lng_for(0, 0))
    assert result.path[-1] == pytest.approx(lat_lng_for(11, 11))


def test_simplify_path_reduces_points() -> None:
    path = [(14.0 + index * 0.001, 100.0) for index in range(40)]
    simplified = simplify_path(path, min_step_m=50.0, max_points=10)
    assert len(simplified) <= 10
    assert simplified[0] == path[0]
    assert simplified[-1] == path[-1]


def test_three_segment_planner_produces_outbound_and_return_waypoints() -> None:
    params = AiRoutePlannerParams(
        route_style=RouteStyle.LOW_LEVEL,
        grid_m=120,
        turn_radius_m=600,
    )
    plan = plan_three_segment_waypoints(
        takeoff=(14.93, 102.08),
        target=(16.81, 100.0),
        entry=(16.5, 99.0),
        exit_point=(16.6, 99.1),
        params=params,
        route_style=RouteStyle.LOW_LEVEL,
        terrain_sampler=FlatTerrainSampler(),
        allow_network=False,
    )
    assert plan is not None
    assert plan.outbound_fly_through
    assert plan.return_fly_through
    assert "direct" in plan.planner_label or "inland detour" in plan.planner_label


def test_hybrid_planner_label() -> None:
    params = AiRoutePlannerParams(route_style=RouteStyle.HYBRID, grid_m=150)
    plan = plan_three_segment_waypoints(
        takeoff=(14.0, 100.0),
        target=(14.05, 100.05),
        entry=(14.02, 100.02),
        exit_point=(14.03, 100.03),
        params=params,
        route_style=RouteStyle.HYBRID,
        terrain_sampler=FlatTerrainSampler(),
        allow_network=False,
    )
    assert plan is not None
    assert "Hybrid" in plan.planner_label or "RRT" in plan.planner_label
