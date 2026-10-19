from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

MAX_GRID_ROWS = 40
MAX_GRID_COLS = 40
_ELEVATION_BATCH_SIZE = 100


class TerrainSampler(Protocol):
    def elevation_m(self, lat: float, lng: float) -> float: ...


class FlatTerrainSampler:
    """Zero elevation — used in tests and offline fallback."""

    def elevation_m(self, lat: float, lng: float) -> float:
        return 0.0

    def elevations_batch(self, points: list[tuple[float, float]]) -> list[float]:
        return [0.0] * len(points)


@dataclass
class BilinearTerrainGrid:
    """Elevation field on a regular lat/lng grid with bilinear lookup."""

    min_lat: float
    min_lng: float
    step_lat: float
    step_lng: float
    rows: int
    cols: int
    elevations: tuple[float, ...]

    def elevation_m(self, lat: float, lng: float) -> float:
        if self.rows < 2 or self.cols < 2:
            return self.elevations[0] if self.elevations else 0.0
        col_f = (lng - self.min_lng) / self.step_lng if self.step_lng else 0.0
        row_f = (lat - self.min_lat) / self.step_lat if self.step_lat else 0.0
        col_f = min(max(col_f, 0.0), self.cols - 1)
        row_f = min(max(row_f, 0.0), self.rows - 1)
        col0 = int(math.floor(col_f))
        row0 = int(math.floor(row_f))
        col1 = min(col0 + 1, self.cols - 1)
        row1 = min(row0 + 1, self.rows - 1)
        tx = col_f - col0
        ty = row_f - row0

        def at(row: int, col: int) -> float:
            return self.elevations[row * self.cols + col]

        v00 = at(row0, col0)
        v10 = at(row0, col1)
        v01 = at(row1, col0)
        v11 = at(row1, col1)
        return (
            v00 * (1 - tx) * (1 - ty)
            + v10 * tx * (1 - ty)
            + v01 * (1 - tx) * ty
            + v11 * tx * ty
        )


def _meters_to_lat_delta(meters: float) -> float:
    return meters / 111_320.0


def _meters_to_lng_delta(meters: float, lat: float) -> float:
    cos_lat = max(math.cos(math.radians(lat)), 0.15)
    return meters / (111_320.0 * cos_lat)


def _grid_dimensions(
    *,
    min_lat: float,
    max_lat: float,
    min_lng: float,
    max_lng: float,
    grid_m: int,
) -> tuple[int, int, float, float]:
    center_lat = (min_lat + max_lat) / 2.0
    span_lat_m = abs(max_lat - min_lat) * 111_320.0
    span_lng_m = abs(max_lng - min_lng) * 111_320.0 * max(
        math.cos(math.radians(center_lat)), 0.15
    )
    span_m = max(span_lat_m, span_lng_m, float(grid_m))
    effective_grid_m = max(float(grid_m), span_m / max(MAX_GRID_ROWS - 1, 1))
    step_lat = _meters_to_lat_delta(effective_grid_m)
    step_lng = _meters_to_lng_delta(effective_grid_m, center_lat)
    rows = max(2, min(MAX_GRID_ROWS, int(math.ceil(span_lat_m / effective_grid_m)) + 1))
    cols = max(2, min(MAX_GRID_COLS, int(math.ceil(span_lng_m / effective_grid_m)) + 1))
    step_lat = (max_lat - min_lat) / (rows - 1) if rows > 1 else step_lat
    step_lng = (max_lng - min_lng) / (cols - 1) if cols > 1 else step_lng
    return rows, cols, step_lat, step_lng


def build_bbox_grid_sampler(
    *,
    min_lat: float,
    max_lat: float,
    min_lng: float,
    max_lng: float,
    grid_m: int,
    fetcher: TerrainSampler | None = None,
) -> BilinearTerrainGrid:
    """Sample elevation on a regular grid covering the bounding box."""
    fetch = fetcher or FlatTerrainSampler()
    rows, cols, step_lat, step_lng = _grid_dimensions(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
        grid_m=grid_m,
    )

    points: list[tuple[float, float]] = []
    for row in range(rows):
        lat = min_lat + row * step_lat
        for col in range(cols):
            lng = min_lng + col * step_lng
            points.append((lat, lng))

    if hasattr(fetch, "elevations_batch"):
        elevations = list(fetch.elevations_batch(points))  # type: ignore[attr-defined]
    else:
        elevations = [fetch.elevation_m(lat, lng) for lat, lng in points]

    return BilinearTerrainGrid(
        min_lat=min_lat,
        min_lng=min_lng,
        step_lat=step_lat,
        step_lng=step_lng,
        rows=rows,
        cols=cols,
        elevations=tuple(elevations),
    )


def bbox_around_points(
    points: list[tuple[float, float]],
    *,
    padding_m: float,
) -> tuple[float, float, float, float]:
    lats = [point[0] for point in points]
    lngs = [point[1] for point in points]
    center_lat = sum(lats) / len(lats)
    padding_lat = _meters_to_lat_delta(padding_m)
    padding_lng = _meters_to_lng_delta(padding_m, center_lat)
    return (
        min(lats) - padding_lat,
        max(lats) + padding_lat,
        min(lngs) - padding_lng,
        max(lngs) + padding_lng,
    )


class OpenElevationSampler:
    """Fetch terrain via batched open-elevation.com requests."""

    def __init__(self, *, timeout_s: float = 4.0) -> None:
        self._timeout_s = timeout_s
        self._cache: dict[tuple[float, float], float] = {}

    def _cache_key(self, lat: float, lng: float) -> tuple[float, float]:
        return (round(lat, 4), round(lng, 4))

    def elevation_m(self, lat: float, lng: float) -> float:
        values = self.elevations_batch([(lat, lng)])
        return values[0] if values else 0.0

    def elevations_batch(self, points: list[tuple[float, float]]) -> list[float]:
        if not points:
            return []
        results: list[float | None] = [None] * len(points)
        pending: list[tuple[int, float, float]] = []
        for index, (lat, lng) in enumerate(points):
            key = self._cache_key(lat, lng)
            if key in self._cache:
                results[index] = self._cache[key]
            else:
                pending.append((index, lat, lng))

        for chunk_start in range(0, len(pending), _ELEVATION_BATCH_SIZE):
            chunk = pending[chunk_start : chunk_start + _ELEVATION_BATCH_SIZE]
            fetched = self._fetch_batch([(lat, lng) for _, lat, lng in chunk])
            for (index, lat, lng), elevation in zip(chunk, fetched, strict=False):
                key = self._cache_key(lat, lng)
                self._cache[key] = elevation
                results[index] = elevation

        return [float(value or 0.0) for value in results]

    def _fetch_batch(self, points: list[tuple[float, float]]) -> list[float]:
        if not points:
            return []
        payload = json.dumps(
            {
                "locations": [
                    {"latitude": lat, "longitude": lng} for lat, lng in points
                ]
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.open-elevation.com/api/v1/lookup",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                body = json.loads(response.read().decode("utf-8"))
            rows = body.get("results") or []
            return [float(row.get("elevation") or 0.0) for row in rows]
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return [0.0] * len(points)


def default_terrain_sampler(*, allow_network: bool = True) -> TerrainSampler:
    if not allow_network:
        return FlatTerrainSampler()
    return OpenElevationSampler()
