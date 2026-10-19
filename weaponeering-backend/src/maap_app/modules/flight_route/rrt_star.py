from __future__ import annotations

import math
import random
from dataclasses import dataclass

from maap_app.modules.weaponeering.flight_path import bearing_deg, distance_m, destination_point
from maap_app.modules.weaponeering.trajectory import turn_radius_m


@dataclass(frozen=True)
class RrtStarConfig:
    step_m: float = 400.0
    max_iterations: int = 280
    goal_bias: float = 0.18
    rewire_radius_m: float = 900.0
    turn_radius_m: float = 800.0
    cruise_kts: float = 250.0
    bank_deg: float = 25.0


def _min_turn_radius(config: RrtStarConfig) -> float:
    if config.turn_radius_m > 0:
        return float(config.turn_radius_m)
    return turn_radius_m(config.cruise_kts, config.bank_deg)


def _feasible_turn(
    prev: tuple[float, float] | None,
    current: tuple[float, float],
    nxt: tuple[float, float],
    *,
    min_radius_m: float,
) -> bool:
    if prev is None:
        return True
    in_bearing = bearing_deg(prev[0], prev[1], current[0], current[1])
    out_bearing = bearing_deg(current[0], current[1], nxt[0], nxt[1])
    delta = abs(out_bearing - in_bearing)
    if delta > 180:
        delta = 360 - delta
    leg_in = max(distance_m(prev[0], prev[1], current[0], current[1]), 1.0)
    leg_out = max(distance_m(current[0], current[1], nxt[0], nxt[1]), 1.0)
    required = min_radius_m * math.radians(max(delta, 1.0))
    return leg_in >= required * 0.35 and leg_out >= required * 0.35


def rrt_star_refine(
    *,
    start: tuple[float, float],
    goal: tuple[float, float],
    initial_path: list[tuple[float, float]],
    bounds: tuple[float, float, float, float],
    is_free: callable,
    config: RrtStarConfig | None = None,
) -> list[tuple[float, float]]:
    """Lightweight RRT* refinement anchored to an initial A* polyline."""
    settings = config or RrtStarConfig()
    min_radius = _min_turn_radius(settings)
    if len(initial_path) < 2:
        return list(initial_path)

    min_lat, max_lat, min_lng, max_lng = bounds
    nodes: list[tuple[float, float]] = [start]
    parents: list[int] = [-1]
    costs: list[float] = [0.0]
    goal_index: int | None = None
    rng = random.Random(42)

    def nearest_index(point: tuple[float, float]) -> int:
        return min(
            range(len(nodes)),
            key=lambda index: distance_m(
                nodes[index][0], nodes[index][1], point[0], point[1]
            ),
        )

    def steer(from_point: tuple[float, float], to_point: tuple[float, float]) -> tuple[float, float]:
        dist = distance_m(from_point[0], from_point[1], to_point[0], to_point[1])
        if dist <= settings.step_m:
            return to_point
        bearing = bearing_deg(from_point[0], from_point[1], to_point[0], to_point[1])
        lat, lng = destination_point(from_point[0], from_point[1], bearing, settings.step_m)
        return lat, lng

    def near_indices(point: tuple[float, float]) -> list[int]:
        return [
            index
            for index, node in enumerate(nodes)
            if distance_m(node[0], node[1], point[0], point[1]) <= settings.rewire_radius_m
        ]

    for _ in range(settings.max_iterations):
        if rng.random() < settings.goal_bias:
            sample = goal
        elif rng.random() < 0.35 and initial_path:
            sample = initial_path[rng.randrange(len(initial_path))]
        else:
            sample = (
                rng.uniform(min_lat, max_lat),
                rng.uniform(min_lng, max_lng),
            )
        nearest = nearest_index(sample)
        new_point = steer(nodes[nearest], sample)
        if not (min_lat <= new_point[0] <= max_lat and min_lng <= new_point[1] <= max_lng):
            continue
        if not is_free(new_point):
            continue
        parent = nearest
        best_cost = costs[nearest] + distance_m(
            nodes[nearest][0], nodes[nearest][1], new_point[0], new_point[1]
        )
        for index in near_indices(new_point):
            parent_point = nodes[index]
            prev = nodes[parents[index]] if parents[index] >= 0 else None
            if not _feasible_turn(prev, parent_point, new_point, min_radius_m=min_radius):
                continue
            candidate = costs[index] + distance_m(
                parent_point[0], parent_point[1], new_point[0], new_point[1]
            )
            if candidate < best_cost:
                best_cost = candidate
                parent = index
        prev_parent = nodes[parent] if parent >= 0 else None
        if not _feasible_turn(prev_parent, nodes[parent], new_point, min_radius_m=min_radius):
            continue
        nodes.append(new_point)
        parents.append(parent)
        costs.append(best_cost)
        new_index = len(nodes) - 1
        if distance_m(new_point[0], new_point[1], goal[0], goal[1]) <= settings.step_m * 1.5:
            goal_index = new_index

    if goal_index is None:
        return list(initial_path)

    chain: list[tuple[float, float]] = []
    index = goal_index
    while index >= 0:
        chain.append(nodes[index])
        index = parents[index]
    chain.reverse()
    if chain[0] != start:
        chain.insert(0, start)
    if chain[-1] != goal:
        chain.append(goal)
    return chain
