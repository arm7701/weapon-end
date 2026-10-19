from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from maap_app.modules.weaponeering.flight_path import (
    bearing_deg,
    destination_point,
    distance_m,
    normalize_bearing_deg,
)

METERS_PER_NM = 1852.0
DEFAULT_MAX_SEARCH_M = 800_000.0
DEFAULT_STEP_M = 4_000.0
REFINE_ITERATIONS = 12
THAILAND_BOUNDS = (5.5, 20.5, 97.3, 105.65)
MAX_INTERIOR_SNAP_M = 40_000.0
SNAP_BEARING_STEP_DEG = 10
SNAP_DISTANCE_STEP_M = 2_000.0
NEAREST_BORDER_BEARING_TOLERANCE_DEG = 45.0
AXIS_BORDER_ANGULAR_TOLERANCE_DEG = 22.5
NEAR_BORDER_STEP_M = 500.0
NEAR_BORDER_MAX_SEARCH_M = 50_000.0

PolygonRings = list[list[tuple[float, float]]]
MultiPolygon = list[PolygonRings]


@dataclass(frozen=True)
class BorderCrossing:
    lat: float
    lng: float
    bearing_deg: float
    distance_m: float


@dataclass(frozen=True)
class ResolvedThailandTarget:
    lat: float
    lng: float
    snapped: bool
    snap_distance_m: float = 0.0


@dataclass(frozen=True)
class IngressBorderRoute:
    available: bool
    approach_bearing_deg: float = 0.0
    ingress_bearing_deg: float = 0.0
    entry: BorderCrossing | None = None
    exit: BorderCrossing | None = None
    nearest_border: BorderCrossing | None = None
    total_corridor_m: float | None = None
    message: str = ""

    def to_map_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "available": self.available,
            "approachBearingDeg": self.approach_bearing_deg,
            "ingressBearingDeg": self.ingress_bearing_deg,
            "message": self.message,
        }
        if self.entry is not None:
            payload["entry"] = {
                "lat": self.entry.lat,
                "lng": self.entry.lng,
                "bearingDeg": self.entry.bearing_deg,
                "distanceM": round(self.entry.distance_m, 1),
                "distanceNm": round(self.entry.distance_m / METERS_PER_NM, 1),
            }
        if self.exit is not None:
            payload["exit"] = {
                "lat": self.exit.lat,
                "lng": self.exit.lng,
                "bearingDeg": self.exit.bearing_deg,
                "distanceM": round(self.exit.distance_m, 1),
                "distanceNm": round(self.exit.distance_m / METERS_PER_NM, 1),
            }
        if self.nearest_border is not None:
            payload["nearestBorder"] = {
                "lat": self.nearest_border.lat,
                "lng": self.nearest_border.lng,
                "bearingDeg": self.nearest_border.bearing_deg,
                "distanceM": round(self.nearest_border.distance_m, 1),
                "distanceNm": round(self.nearest_border.distance_m / METERS_PER_NM, 1),
            }
        if self.total_corridor_m is not None:
            payload["totalCorridorM"] = round(self.total_corridor_m, 1)
            payload["totalCorridorNm"] = round(
                self.total_corridor_m / METERS_PER_NM,
                1,
            )
        return payload


def default_border_geojson_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "ui"
        / "map"
        / "assets"
        / "borders"
        / "thailand_adm0_simplified.geojson"
    )


@lru_cache(maxsize=1)
def load_thailand_multipolygon(
    geojson_path: str | None = None,
) -> MultiPolygon:
    path = Path(geojson_path) if geojson_path else default_border_geojson_path()
    data = json.loads(path.read_text(encoding="utf-8"))
    polygons: MultiPolygon = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry") or {}
        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates") or []
        if geom_type == "Polygon":
            polygons.append(_normalize_polygon_rings(coordinates))
        elif geom_type == "MultiPolygon":
            for polygon_coords in coordinates:
                polygons.append(_normalize_polygon_rings(polygon_coords))
    return polygons


def _normalize_polygon_rings(polygon_coords: list) -> PolygonRings:
    rings: PolygonRings = []
    for ring_coords in polygon_coords:
        ring: list[tuple[float, float]] = []
        for point in ring_coords:
            lng = float(point[0])
            lat = float(point[1])
            ring.append((lng, lat))
        if ring:
            rings.append(ring)
    return rings


def point_in_thailand(
    lat: float,
    lng: float,
    *,
    multipolygon: MultiPolygon | None = None,
) -> bool:
    polygons = multipolygon or load_thailand_multipolygon()
    for polygon in polygons:
        if not polygon:
            continue
        if _point_in_ring(lng, lat, polygon[0]):
            if any(_point_in_ring(lng, lat, hole) for hole in polygon[1:]):
                continue
            return True
    return False


def _point_in_ring(lng: float, lat: float, ring: list[tuple[float, float]]) -> bool:
    inside = False
    count = len(ring)
    if count < 3:
        return False
    previous = ring[-1]
    for current in ring:
        prev_lng, prev_lat = previous
        curr_lng, curr_lat = current
        intersects = (curr_lat > lat) != (prev_lat > lat) and lng < (
            (prev_lng - curr_lng) * (lat - curr_lat) / (prev_lat - curr_lat + 1e-15)
            + curr_lng
        )
        if intersects:
            inside = not inside
        previous = current
    return inside


def _within_thailand_bounds(lat: float, lng: float) -> bool:
    min_lat, max_lat, min_lng, max_lng = THAILAND_BOUNDS
    return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng


def _find_nearest_interior_point(
    lat: float,
    lng: float,
    *,
    max_radius_m: float = MAX_INTERIOR_SNAP_M,
    multipolygon: MultiPolygon,
) -> tuple[float, float, float] | None:
    best: tuple[float, float, float] | None = None
    for bearing in range(0, 360, SNAP_BEARING_STEP_DEG):
        distance = SNAP_DISTANCE_STEP_M
        while distance <= max_radius_m:
            sample_lat, sample_lng = destination_point(
                lat,
                lng,
                float(bearing),
                distance,
            )
            if point_in_thailand(
                sample_lat,
                sample_lng,
                multipolygon=multipolygon,
            ):
                if best is None or distance < best[2]:
                    best = (sample_lat, sample_lng, distance)
                break
            distance += SNAP_DISTANCE_STEP_M
    return best


def resolve_target_for_border_route(
    lat: float,
    lng: float,
    *,
    multipolygon: MultiPolygon | None = None,
) -> ResolvedThailandTarget | None:
    polygons = multipolygon or load_thailand_multipolygon()
    if point_in_thailand(lat, lng, multipolygon=polygons):
        return ResolvedThailandTarget(lat=lat, lng=lng, snapped=False)

    if not _within_thailand_bounds(lat, lng):
        return None

    nearest = _find_nearest_interior_point(
        lat,
        lng,
        multipolygon=polygons,
    )
    if nearest is None:
        return None
    snap_lat, snap_lng, snap_distance_m = nearest
    return ResolvedThailandTarget(
        lat=snap_lat,
        lng=snap_lng,
        snapped=True,
        snap_distance_m=snap_distance_m,
    )


def _angular_diff_deg(a: float, b: float) -> float:
    diff = abs(normalize_bearing_deg(a) - normalize_bearing_deg(b)) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff


def _closest_point_on_segment_lla(
    point_lat: float,
    point_lng: float,
    a_lng: float,
    a_lat: float,
    b_lng: float,
    b_lat: float,
) -> tuple[float, float]:
    mean_lat = math.radians((point_lat + a_lat + b_lat) / 3.0)
    cos_lat = max(math.cos(mean_lat), 0.1)
    px = point_lng * cos_lat * 111_320.0
    py = point_lat * 111_320.0
    ax = a_lng * cos_lat * 111_320.0
    ay = a_lat * 111_320.0
    bx = b_lng * cos_lat * 111_320.0
    by = b_lat * 111_320.0
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return a_lat, a_lng
    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    closest_x = ax + t * dx
    closest_y = ay + t * dy
    return closest_y / 111_320.0, closest_x / (cos_lat * 111_320.0)


def find_nearest_border(
    lat: float,
    lng: float,
    *,
    multipolygon: MultiPolygon | None = None,
) -> BorderCrossing | None:
    polygons = multipolygon or load_thailand_multipolygon()
    best_distance_m = float("inf")
    best_lat = 0.0
    best_lng = 0.0
    for polygon in polygons:
        if not polygon:
            continue
        outer_ring = polygon[0]
        if len(outer_ring) < 2:
            continue
        for index in range(len(outer_ring)):
            a_lng, a_lat = outer_ring[index]
            b_lng, b_lat = outer_ring[(index + 1) % len(outer_ring)]
            closest_lat, closest_lng = _closest_point_on_segment_lla(
                lat,
                lng,
                a_lng,
                a_lat,
                b_lng,
                b_lat,
            )
            segment_distance_m = distance_m(lat, lng, closest_lat, closest_lng)
            if segment_distance_m < best_distance_m:
                best_distance_m = segment_distance_m
                best_lat = closest_lat
                best_lng = closest_lng
    if best_distance_m == float("inf"):
        return None
    return BorderCrossing(
        lat=round(best_lat, 6),
        lng=round(best_lng, 6),
        bearing_deg=round(bearing_deg(lat, lng, best_lat, best_lng), 1),
        distance_m=round(best_distance_m, 1),
    )


def _crossing_from_target(
    crossing: BorderCrossing,
    target_lat: float,
    target_lng: float,
) -> BorderCrossing:
    return BorderCrossing(
        lat=crossing.lat,
        lng=crossing.lng,
        bearing_deg=round(bearing_deg(target_lat, target_lng, crossing.lat, crossing.lng), 1),
        distance_m=round(distance_m(target_lat, target_lng, crossing.lat, crossing.lng), 1),
    )


def find_border_crossing_along_bearing(
    *,
    origin_lat: float,
    origin_lng: float,
    bearing_deg: float,
    start_inside: bool,
    max_search_m: float = DEFAULT_MAX_SEARCH_M,
    step_m: float = DEFAULT_STEP_M,
    multipolygon: MultiPolygon | None = None,
) -> BorderCrossing | None:
    polygons = multipolygon or load_thailand_multipolygon()
    normalized_bearing = normalize_bearing_deg(bearing_deg)
    origin_inside = point_in_thailand(
        origin_lat,
        origin_lng,
        multipolygon=polygons,
    )
    if start_inside and not origin_inside:
        return None
    if not start_inside and origin_inside:
        return None

    previous_distance = 0.0
    previous_inside = origin_inside
    distance = step_m
    while distance <= max_search_m:
        sample_lat, sample_lng = destination_point(
            origin_lat,
            origin_lng,
            normalized_bearing,
            distance,
        )
        sample_inside = point_in_thailand(
            sample_lat,
            sample_lng,
            multipolygon=polygons,
        )
        if previous_inside != sample_inside:
            crossing_distance = _refine_crossing_distance(
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                bearing_deg=normalized_bearing,
                near_m=previous_distance,
                far_m=distance,
                expect_inside_at_near=start_inside,
                multipolygon=polygons,
            )
            crossing_lat, crossing_lng = destination_point(
                origin_lat,
                origin_lng,
                normalized_bearing,
                crossing_distance,
            )
            return BorderCrossing(
                lat=round(crossing_lat, 6),
                lng=round(crossing_lng, 6),
                bearing_deg=normalized_bearing,
                distance_m=round(crossing_distance, 1),
            )
        previous_distance = distance
        previous_inside = sample_inside
        distance += step_m
    return None


def _refine_crossing_distance(
    *,
    origin_lat: float,
    origin_lng: float,
    bearing_deg: float,
    near_m: float,
    far_m: float,
    expect_inside_at_near: bool,
    multipolygon: MultiPolygon,
) -> float:
    low = near_m
    high = far_m
    for _ in range(REFINE_ITERATIONS):
        mid = (low + high) / 2.0
        mid_lat, mid_lng = destination_point(
            origin_lat,
            origin_lng,
            bearing_deg,
            mid,
        )
        mid_inside = point_in_thailand(
            mid_lat,
            mid_lng,
            multipolygon=multipolygon,
        )
        if mid_inside == expect_inside_at_near:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def find_nearest_border_point_on_axis(
    target_lat: float,
    target_lng: float,
    axis_bearing_deg: float,
    *,
    multipolygon: MultiPolygon | None = None,
    angular_tolerance_deg: float = AXIS_BORDER_ANGULAR_TOLERANCE_DEG,
    max_distance_m: float = DEFAULT_MAX_SEARCH_M,
) -> BorderCrossing | None:
    polygons = multipolygon or load_thailand_multipolygon()
    axis = normalize_bearing_deg(axis_bearing_deg)
    best: BorderCrossing | None = None
    for polygon in polygons:
        if not polygon:
            continue
        for ring in polygon:
            if len(ring) < 2:
                continue
            for index in range(len(ring)):
                a_lng, a_lat = ring[index]
                b_lng, b_lat = ring[(index + 1) % len(ring)]
                closest_lat, closest_lng = _closest_point_on_segment_lla(
                    target_lat,
                    target_lng,
                    a_lng,
                    a_lat,
                    b_lng,
                    b_lat,
                )
                segment_distance_m = distance_m(
                    target_lat,
                    target_lng,
                    closest_lat,
                    closest_lng,
                )
                if segment_distance_m <= 0.0 or segment_distance_m > max_distance_m:
                    continue
                point_bearing = bearing_deg(
                    target_lat,
                    target_lng,
                    closest_lat,
                    closest_lng,
                )
                if _angular_diff_deg(point_bearing, axis) > angular_tolerance_deg:
                    continue
                if best is None or segment_distance_m < best.distance_m:
                    best = BorderCrossing(
                        lat=round(closest_lat, 6),
                        lng=round(closest_lng, 6),
                        bearing_deg=axis,
                        distance_m=round(segment_distance_m, 1),
                    )
    return best


def _find_axis_border_crossing(
    *,
    target_lat: float,
    target_lng: float,
    calc_lat: float,
    calc_lng: float,
    axis_bearing_deg: float,
    max_search_m: float,
    multipolygon: MultiPolygon,
) -> BorderCrossing | None:
    axis = normalize_bearing_deg(axis_bearing_deg)
    candidates: list[BorderCrossing] = []

    geom = find_nearest_border_point_on_axis(
        target_lat,
        target_lng,
        axis,
        multipolygon=multipolygon,
        max_distance_m=max_search_m,
    )
    if geom is not None:
        candidates.append(geom)

    target_inside = point_in_thailand(
        target_lat,
        target_lng,
        multipolygon=multipolygon,
    )
    if target_inside:
        target_ray = find_border_crossing_along_bearing(
            origin_lat=target_lat,
            origin_lng=target_lng,
            bearing_deg=axis,
            start_inside=True,
            max_search_m=max_search_m,
            step_m=NEAR_BORDER_STEP_M,
            multipolygon=multipolygon,
        )
    else:
        target_ray = find_border_crossing_along_bearing(
            origin_lat=target_lat,
            origin_lng=target_lng,
            bearing_deg=axis,
            start_inside=False,
            max_search_m=min(max_search_m, NEAR_BORDER_MAX_SEARCH_M),
            step_m=NEAR_BORDER_STEP_M,
            multipolygon=multipolygon,
        )
    if target_ray is not None:
        candidates.append(
            BorderCrossing(
                lat=target_ray.lat,
                lng=target_ray.lng,
                bearing_deg=axis,
                distance_m=round(
                    distance_m(target_lat, target_lng, target_ray.lat, target_ray.lng),
                    1,
                ),
            )
        )

    if (calc_lat, calc_lng) != (target_lat, target_lng) and point_in_thailand(
        calc_lat,
        calc_lng,
        multipolygon=multipolygon,
    ):
        calc_ray = find_border_crossing_along_bearing(
            origin_lat=calc_lat,
            origin_lng=calc_lng,
            bearing_deg=axis,
            start_inside=True,
            max_search_m=max_search_m,
            step_m=NEAR_BORDER_STEP_M,
            multipolygon=multipolygon,
        )
        if calc_ray is not None:
            projected = _crossing_on_corridor_axis(
                BorderCrossing(
                    lat=calc_ray.lat,
                    lng=calc_ray.lng,
                    bearing_deg=axis,
                    distance_m=calc_ray.distance_m,
                ),
                target_lat,
                target_lng,
                axis,
            )
            if projected is not None:
                candidates.append(projected)

    if not candidates:
        return None
    return min(candidates, key=lambda item: item.distance_m)


def _crossing_on_corridor_axis(
    crossing: BorderCrossing | None,
    target_lat: float,
    target_lng: float,
    axis_bearing_deg: float,
) -> BorderCrossing | None:
    if crossing is None:
        return None
    corridor_distance_m = distance_m(
        target_lat,
        target_lng,
        crossing.lat,
        crossing.lng,
    )
    axis_lat, axis_lng = destination_point(
        target_lat,
        target_lng,
        axis_bearing_deg,
        corridor_distance_m,
    )
    return BorderCrossing(
        lat=round(axis_lat, 6),
        lng=round(axis_lng, 6),
        bearing_deg=round(normalize_bearing_deg(axis_bearing_deg), 1),
        distance_m=round(corridor_distance_m, 1),
    )


def calculate_ingress_border_route(
    *,
    target_lat: float,
    target_lng: float,
    approach_bearing_deg: float,
    max_search_m: float = DEFAULT_MAX_SEARCH_M,
    multipolygon: MultiPolygon | None = None,
) -> IngressBorderRoute:
    polygons = multipolygon or load_thailand_multipolygon()
    approach = normalize_bearing_deg(approach_bearing_deg)
    ingress = normalize_bearing_deg(approach + 180.0)

    resolved = resolve_target_for_border_route(
        target_lat,
        target_lng,
        multipolygon=polygons,
    )
    if resolved is None:
        return IngressBorderRoute(
            available=False,
            approach_bearing_deg=approach,
            ingress_bearing_deg=ingress,
            message="เป้าหมายอยู่นอกขอบเขตประเทศไทย — ไม่สามารถคำนวณจุดเข้า-ออกชายแดนได้",
        )

    calc_lat = resolved.lat
    calc_lng = resolved.lng
    nearest_border = find_nearest_border(
        target_lat,
        target_lng,
        multipolygon=polygons,
    )
    if nearest_border is None and resolved.snapped:
        nearest_border = find_nearest_border(
            calc_lat,
            calc_lng,
            multipolygon=polygons,
        )

    snap_note = ""
    if resolved.snapped:
        snap_note = (
            " (อ้างอิงจากจุดในประเทศไทยที่ใกล้เป้าหมาย "
            f"{format_border_distance(resolved.snap_distance_m)} — "
            "ข้อมูลชายแดน simplified อาจมีช่องว่างบริเวณพรีเซ็ต)"
        )

    raw_exit = _find_axis_border_crossing(
        target_lat=target_lat,
        target_lng=target_lng,
        calc_lat=calc_lat,
        calc_lng=calc_lng,
        axis_bearing_deg=approach,
        max_search_m=max_search_m,
        multipolygon=polygons,
    )
    raw_entry = _find_axis_border_crossing(
        target_lat=target_lat,
        target_lng=target_lng,
        calc_lat=calc_lat,
        calc_lng=calc_lng,
        axis_bearing_deg=ingress,
        max_search_m=max_search_m,
        multipolygon=polygons,
    )

    exit_candidate = raw_exit
    entry_candidate = raw_entry

    entry = _crossing_on_corridor_axis(
        entry_candidate,
        target_lat,
        target_lng,
        ingress,
    )
    exit_crossing = _crossing_on_corridor_axis(
        exit_candidate,
        target_lat,
        target_lng,
        approach,
    )
    if nearest_border is not None:
        nearest_border = _crossing_from_target(nearest_border, target_lat, target_lng)
        if _angular_diff_deg(nearest_border.bearing_deg, approach) > (
            NEAREST_BORDER_BEARING_TOLERANCE_DEG
        ) and _angular_diff_deg(nearest_border.bearing_deg, ingress) > (
            NEAREST_BORDER_BEARING_TOLERANCE_DEG
        ):
            nearest_border = None

    if entry is None and exit_crossing is None:
        return IngressBorderRoute(
            available=False,
            approach_bearing_deg=approach,
            ingress_bearing_deg=ingress,
            message="ไม่พบจุดตัดชายแดนในทิศทางเข้า (ตรงข้ามทิศความเสี่ยง) หรือทิศออก"
            + snap_note,
        )

    total_corridor_m: float | None = None
    if entry is not None and exit_crossing is not None:
        total_corridor_m = entry.distance_m + exit_crossing.distance_m
    elif entry is not None:
        total_corridor_m = entry.distance_m
    elif exit_crossing is not None:
        total_corridor_m = exit_crossing.distance_m
    elif nearest_border is not None:
        total_corridor_m = nearest_border.distance_m

    notes: list[str] = []
    if snap_note.strip():
        notes.append(snap_note.strip())
    if nearest_border is not None:
        notes.append(
            "ขอบประเทศใกล้สุด "
            f"{format_border_distance(nearest_border.distance_m)} "
            f"ทิศ {nearest_border.bearing_deg:.0f}°"
        )

    return IngressBorderRoute(
        available=True,
        approach_bearing_deg=approach,
        ingress_bearing_deg=ingress,
        entry=entry,
        exit=exit_crossing,
        nearest_border=nearest_border,
        total_corridor_m=total_corridor_m,
        message=" · ".join(notes),
    )


def format_border_distance(distance_m: float | None) -> str:
    if distance_m is None:
        return "—"
    if distance_m >= 1000.0:
        return f"{distance_m / 1000.0:.1f} km ({distance_m / METERS_PER_NM:.1f} NM)"
    return f"{distance_m:.0f} m"


def border_route_summary_th(route: IngressBorderRoute) -> str:
    if not route.available:
        return route.message or "ยังไม่สามารถคำนวณเส้นทางเข้า-ออกชายแดนได้"

    parts: list[str] = [
        f"ทิศทางเข้า (Ingress) {route.ingress_bearing_deg:.0f}°",
    ]
    if route.nearest_border is not None:
        parts.append(
            "ขอบประเทศใกล้สุด "
            f"{format_border_distance(route.nearest_border.distance_m)} "
            f"({route.nearest_border.bearing_deg:.0f}°)"
        )
    if route.entry is not None:
        parts.append(
            "จุดเข้าประเทศ "
            f"{route.entry.lat:.4f}, {route.entry.lng:.4f} "
            f"({format_border_distance(route.entry.distance_m)} จากเป้าหมาย)"
        )
    if route.exit is not None:
        parts.append(
            "จุดออกประเทศ "
            f"{route.exit.lat:.4f}, {route.exit.lng:.4f} "
            f"({format_border_distance(route.exit.distance_m)} จากเป้าหมาย)"
        )
    if route.total_corridor_m is not None:
        parts.append(
            f"ระยะทางภายในประเทศโดยประมาณ {format_border_distance(route.total_corridor_m)}"
        )
    return " · ".join(parts)
