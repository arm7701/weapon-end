from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

from maap_app.modules.weaponeering.flight_path import distance_m


@dataclass(frozen=True)
class GridNode:
    row: int
    col: int

    def key(self) -> tuple[int, int]:
        return (self.row, self.col)


@dataclass
class AStarResult:
    path: list[tuple[float, float]]
    total_cost: float
    explored: int


def _neighbors(node: GridNode, rows: int, cols: int) -> list[GridNode]:
    result: list[GridNode] = []
    for dr, dc in (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    ):
        row = node.row + dr
        col = node.col + dc
        if 0 <= row < rows and 0 <= col < cols:
            result.append(GridNode(row, col))
    return result


def astar_on_grid(
    *,
    rows: int,
    cols: int,
    cell_cost: list[float],
    passable: list[bool],
    lat_lng_for: callable,
    start: GridNode,
    goal: GridNode,
    valley_bias: bool = False,
    terrain_for: callable | None = None,
) -> AStarResult | None:
    if not passable[start.row * cols + start.col]:
        return None
    if not passable[goal.row * cols + goal.col]:
        return None

    def heuristic(node: GridNode) -> float:
        lat1, lng1 = lat_lng_for(node.row, node.col)
        lat2, lng2 = lat_lng_for(goal.row, goal.col)
        return distance_m(lat1, lng1, lat2, lng2)

    open_heap: list[tuple[float, int, GridNode]] = []
    counter = 0
    g_score: dict[tuple[int, int], float] = {start.key(): 0.0}
    came_from: dict[tuple[int, int], GridNode] = {}
    heapq.heappush(open_heap, (heuristic(start), counter, start))
    explored = 0

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        explored += 1
        if current.key() == goal.key():
            path_nodes = [current]
            while current.key() in came_from:
                current = came_from[current.key()]
                path_nodes.append(current)
            path_nodes.reverse()
            path = [lat_lng_for(node.row, node.col) for node in path_nodes]
            return AStarResult(
                path=path,
                total_cost=g_score[goal.key()],
                explored=explored,
            )

        current_g = g_score[current.key()]
        for neighbor in _neighbors(current, rows, cols):
            index = neighbor.row * cols + neighbor.col
            if not passable[index]:
                continue
            lat1, lng1 = lat_lng_for(current.row, current.col)
            lat2, lng2 = lat_lng_for(neighbor.row, neighbor.col)
            step = distance_m(lat1, lng1, lat2, lng2)
            terrain_penalty = 0.0
            if valley_bias and terrain_for is not None:
                terrain_penalty = terrain_for(neighbor.row, neighbor.col) * 0.35
            move_cost = step * cell_cost[index] + terrain_penalty
            tentative = current_g + move_cost
            key = neighbor.key()
            if tentative < g_score.get(key, math.inf):
                g_score[key] = tentative
                came_from[key] = current
                counter += 1
                f_score = tentative + heuristic(neighbor)
                heapq.heappush(open_heap, (f_score, counter, neighbor))
    return None


def simplify_path(
    path: list[tuple[float, float]],
    *,
    min_step_m: float,
    max_points: int = 24,
) -> list[tuple[float, float]]:
    if len(path) <= 2:
        return list(path)
    simplified: list[tuple[float, float]] = [path[0]]
    for point in path[1:]:
        if distance_m(simplified[-1][0], simplified[-1][1], point[0], point[1]) >= min_step_m:
            simplified.append(point)
    if simplified[-1] != path[-1]:
        simplified.append(path[-1])
    if len(simplified) <= max_points:
        return simplified
    stride = max(1, (len(simplified) - 1) // (max_points - 1))
    reduced = [simplified[index] for index in range(0, len(simplified), stride)]
    if reduced[-1] != simplified[-1]:
        reduced.append(simplified[-1])
    if len(reduced) > max_points:
        reduced = reduced[: max_points - 1] + [simplified[-1]]
    return reduced
