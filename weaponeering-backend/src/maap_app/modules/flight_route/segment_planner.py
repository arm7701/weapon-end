from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from maap_app.modules.flight_route.params import AiRoutePlannerParams, RouteStyle
from maap_app.modules.flight_route.astar import GridNode, astar_on_grid, simplify_path
from maap_app.modules.flight_route.rrt_star import RrtStarConfig, rrt_star_refine
from maap_app.modules.flight_route.border_corridor_planner import plan_efficient_route_waypoints
from maap_app.modules.flight_route.terrain_sampler import (
    BilinearTerrainGrid,
    TerrainSampler,
    bbox_around_points,
    build_bbox_grid_sampler,
    default_terrain_sampler,
)
from maap_app.modules.weaponeering.flight_path import distance_m


@dataclass(frozen=True)
class TerrainSegmentPlan:
    outbound_fly_through: list[dict[str, Any]]
    return_fly_through: list[dict[str, Any]]
    planner_label: str


def _agl_to_ft(agl_m: float) -> int:
    return max(int(round(agl_m * 3.28084)), 200)


def _flight_altitude_m(
    terrain_m: float,
    *,
    params: AiRoutePlannerParams,
) -> float:
    agl = float(params.pref_agl_m) + float(params.cruise_pad_m) * 0.25
    agl = min(max(agl, float(params.min_agl_m)), float(params.max_agl_m))
    return terrain_m + agl


def _terrain_styles(style: RouteStyle) -> bool:
    return style in {RouteStyle.LOW_LEVEL, RouteStyle.VALLEY, RouteStyle.HYBRID}


def _path_to_waypoints(
    path: list[tuple[float, float]],
    *,
    terrain: BilinearTerrainGrid,
    params: AiRoutePlannerParams,
    label_prefix: str,
) -> list[dict[str, Any]]:
    waypoints: list[dict[str, Any]] = []
    for index, (lat, lng) in enumerate(path[1:-1], start=1):
        terrain_m = terrain.elevation_m(lat, lng)
        alt_m = _flight_altitude_m(terrain_m, params=params)
        waypoints.append(
            {
                "id": f"{label_prefix}-{index}",
                "lat": lat,
                "lng": lng,
                "label": f"{label_prefix}{index}",
                "altitudeFt": _agl_to_ft(alt_m - terrain_m),
            }
        )
    return waypoints


def _build_segment_grid(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    params: AiRoutePlannerParams,
    sampler: TerrainSampler,
) -> BilinearTerrainGrid:
    leg_m = distance_m(start[0], start[1], end[0], end[1])
    padding_m = min(max(leg_m * 0.12, float(params.grid_m) * 4.0), 25_000.0)
    min_lat, max_lat, min_lng, max_lng = bbox_around_points(
        [start, end],
        padding_m=padding_m,
    )
    return build_bbox_grid_sampler(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
        grid_m=int(params.grid_m),
        fetcher=sampler,
    )


def _plan_segment_path(
    *,
    start: tuple[float, float],
    end: tuple[float, float],
    params: AiRoutePlannerParams,
    route_style: RouteStyle,
    terrain_grid: BilinearTerrainGrid,
) -> list[tuple[float, float]]:
    rows, cols = terrain_grid.rows, terrain_grid.cols
    cell_cost: list[float] = []
    passable: list[bool] = []
    terrain_values: list[float] = []

    max_clearance_m = float(params.max_agl_m) + float(params.cruise_pad_m)

    def lat_lng_for(row: int, col: int) -> tuple[float, float]:
        lat = terrain_grid.min_lat + row * terrain_grid.step_lat
        lng = terrain_grid.min_lng + col * terrain_grid.step_lng
        return lat, lng

    for row in range(rows):
        for col in range(cols):
            lat, lng = lat_lng_for(row, col)
            terrain_m = terrain_grid.elevation_m(lat, lng)
            terrain_values.append(terrain_m)
            clearance = _flight_altitude_m(terrain_m, params=params) - terrain_m
            ok = clearance <= max_clearance_m and clearance >= float(params.min_agl_m) * 0.5
            passable.append(ok)
            cell_cost.append(1.0)

    def nearest_node(point: tuple[float, float]) -> tuple[int, int]:
        best = (0, 0)
        best_dist = float("inf")
        for row in range(rows):
            for col in range(cols):
                lat, lng = lat_lng_for(row, col)
                dist = distance_m(point[0], point[1], lat, lng)
                if dist < best_dist:
                    best_dist = dist
                    best = (row, col)
        return best

    start_node = GridNode(*nearest_node(start))
    goal_node = GridNode(*nearest_node(end))
    result = astar_on_grid(
        rows=rows,
        cols=cols,
        cell_cost=cell_cost,
        passable=passable,
        lat_lng_for=lat_lng_for,
        start=start_node,
        goal=goal_node,
        valley_bias=route_style == RouteStyle.VALLEY,
        terrain_for=lambda row, col: terrain_values[row * cols + col],
    )
    if result is None:
        return [start, end]

    path = simplify_path(
        result.path,
        min_step_m=max(float(params.grid_m) * 1.5, 120.0),
        max_points=16,
    )
    if route_style != RouteStyle.HYBRID:
        return path

    min_lat = terrain_grid.min_lat
    min_lng = terrain_grid.min_lng
    max_lat = min_lat + terrain_grid.step_lat * (rows - 1)
    max_lng = min_lng + terrain_grid.step_lng * (cols - 1)

    def is_free(point: tuple[float, float]) -> bool:
        terrain_m = terrain_grid.elevation_m(point[0], point[1])
        clearance = _flight_altitude_m(terrain_m, params=params) - terrain_m
        return float(params.min_agl_m) * 0.5 <= clearance <= max_clearance_m

    refined = rrt_star_refine(
        start=start,
        goal=end,
        initial_path=path,
        bounds=(min_lat, max_lat, min_lng, max_lng),
        is_free=is_free,
        config=RrtStarConfig(
            step_m=max(float(params.grid_m) * 2.0, 200.0),
            max_iterations=72,
            turn_radius_m=float(params.turn_radius_m),
            cruise_kts=float(params.cruise_kts),
        ),
    )
    return simplify_path(
        refined,
        min_step_m=max(float(params.turn_radius_m) * 0.35, float(params.grid_m)),
        max_points=18,
    )


def plan_three_segment_waypoints(
    *,
    takeoff: tuple[float, float],
    target: tuple[float, float],
    entry: tuple[float, float] | None,
    exit_point: tuple[float, float] | None,
    params: AiRoutePlannerParams,
    route_style: RouteStyle,
    terrain_sampler: TerrainSampler | None = None,
    allow_network: bool = True,
) -> TerrainSegmentPlan | None:
    """Segments 1 & 3: shortest inland-safe path — segment 2 stays corridor (entry→TGT→exit)."""
    outbound_end = entry if entry is not None else target
    return_start = exit_point if exit_point is not None else target
    outbound_fly_through: list[dict[str, Any]] = []
    return_fly_through: list[dict[str, Any]] = []
    planner_label = "corridor-only"

    alt_ft = max(
        int(params.cruise_altitude_ft),
        int(round(params.pref_agl_m * 3.28084)),
        200,
    )
    step_m = max(float(params.border_step_m), float(params.grid_m) * 6.0, 8_000.0)
    standoff_m = max(float(params.border_standoff_m), 12_000.0)
    lateral_m = max(standoff_m * 0.15, 2_500.0)

    outbound_fly_through, outbound_mode = plan_efficient_route_waypoints(
        takeoff,
        outbound_end,
        label_prefix="AI-OUT",
        step_m=step_m,
        max_points=12,
        interior_offset_m=standoff_m,
        lateral_dispersion_m=lateral_m,
        altitude_ft=alt_ft,
    )
    return_fly_through, return_mode = plan_efficient_route_waypoints(
        return_start,
        takeoff,
        label_prefix="AI-RTB",
        step_m=step_m,
        max_points=12,
        interior_offset_m=standoff_m,
        lateral_dispersion_m=lateral_m,
        altitude_ft=alt_ft,
    )
    planner_label = f"{outbound_mode} · {return_mode}"
    if _terrain_styles(route_style) and (
        not outbound_fly_through or not return_fly_through
    ):
        sampler = terrain_sampler or default_terrain_sampler(allow_network=allow_network)
        if not outbound_fly_through:
            outbound_grid = _build_segment_grid(
                takeoff, outbound_end, params=params, sampler=sampler
            )
            outbound_path = _plan_segment_path(
                start=takeoff,
                end=outbound_end,
                params=params,
                route_style=route_style,
                terrain_grid=outbound_grid,
            )
            outbound_fly_through = _path_to_waypoints(
                outbound_path,
                terrain=outbound_grid,
                params=params,
                label_prefix="AI-OUT",
            )
        if not return_fly_through:
            return_grid = _build_segment_grid(
                return_start, takeoff, params=params, sampler=sampler
            )
            return_path = _plan_segment_path(
                start=return_start,
                end=takeoff,
                params=params,
                route_style=route_style,
                terrain_grid=return_grid,
            )
            return_fly_through = _path_to_waypoints(
                return_path,
                terrain=return_grid,
                params=params,
                label_prefix="AI-RTB",
            )
        labels = {
            RouteStyle.LOW_LEVEL: "A* terrain LL",
            RouteStyle.VALLEY: "A* valley",
            RouteStyle.HYBRID: "Hybrid A*+RRT*",
        }
        planner_label = labels.get(route_style, planner_label)

    if not outbound_fly_through and not return_fly_through:
        return TerrainSegmentPlan([], [], planner_label)

    return TerrainSegmentPlan(
        outbound_fly_through=outbound_fly_through,
        return_fly_through=return_fly_through,
        planner_label=planner_label,
    )
